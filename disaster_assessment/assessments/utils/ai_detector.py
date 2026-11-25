"""
AI Damage Detection Module using YOLOv8 (Ultralytics)
This uses a real trained model. For best results on disaster imagery,
train or fine-tune on a disaster-damage dataset (see README).
"""

import os
import time
from pathlib import Path
from django.conf import settings
import cv2
import numpy as np
from PIL import Image

# Try importing ultralytics
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("WARNING: ultralytics not installed. AI detection will be limited.")

# Class mapping from COCO / custom to our damage categories
# YOLOv8n COCO classes that can roughly relate (for demo). 
# For production: train custom model with classes: fallen_tree, damaged_building, flooded_road
COCO_TO_DAMAGE = {
    # trees / plants
    58: 'fallen_tree',   # potted plant (approximate)
    # buildings / structures often detected as other
    # We will also use heuristics on image content for flood/road
}

# Better approach: use YOLO detections + simple image analysis for flood
DAMAGE_LABELS = {
    'fallen_tree': 'Fallen Tree / Debris',
    'damaged_building': 'Damaged Building',
    'flooded_road': 'Flooded Road',
    'debris': 'General Debris',
    'other': 'Other Visible Damage',
}


class DisasterDamageDetector:
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path or getattr(settings, 'YOLO_MODEL_PATH', None)
        self.load_model()

    def load_model(self):
        if not YOLO_AVAILABLE:
            self.model = None
            return
        try:
            # YOLOv8n will auto-download weights on first run if path not found
            path = str(self.model_path) if self.model_path else 'yolov8n.pt'
            self.model = YOLO(path)
            print(f"YOLO model loaded from {path}")
        except Exception as e:
            print(f"Failed to load YOLO model: {e}")
            self.model = None

    def detect(self, image_path, conf_threshold=0.25):
        """
        Run detection on image.
        Returns: dict with detections list, annotated image path, summary, severity
        """
        start = time.time()
        results = {
            'detections': [],
            'total': 0,
            'annotated_path': None,
            'summary': '',
            'severity': 'none',
            'processing_time': 0.0,
            'model_used': 'YOLOv8' if self.model else 'Heuristic',
        }

        if not os.path.exists(image_path):
            results['summary'] = 'Image file not found.'
            return results

        # Load image with OpenCV
        img = cv2.imread(str(image_path))
        if img is None:
            results['summary'] = 'Could not read image.'
            return results

        h, w = img.shape[:2]
        detections = []

        if self.model is not None:
            try:
                yolo_results = self.model.predict(
                    source=image_path,
                    conf=conf_threshold,
                    verbose=False
                )
                for r in yolo_results:
                    boxes = r.boxes
                    if boxes is None:
                        continue
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()
                        label = r.names.get(cls_id, str(cls_id))

                        # Map to damage category
                        category = self._map_class(cls_id, label, img, xyxy)

                        x1, y1, x2, y2 = map(int, xyxy)
                        # Draw box
                        color = self._get_color(category)
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        text = f"{DAMAGE_LABELS.get(category, category)} {conf:.0%}"
                        cv2.putText(img, text, (x1, max(y1-8, 15)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                        detections.append({
                            'category': category,
                            'confidence': conf,
                            'bbox': [x1, y1, x2-x1, y2-y1],
                            'label': label,
                        })
            except Exception as e:
                print(f"YOLO prediction error: {e}")

        # Additional heuristic for flooded areas (blue-ish water detection)
        flood_score = self._detect_flood_heuristic(img)
        if flood_score > 0.15:
            detections.append({
                'category': 'flooded_road',
                'confidence': min(0.85, flood_score + 0.3),
                'bbox': None,
                'label': 'flood_water_heuristic',
            })
            # Optional visual marker
            cv2.putText(img, "Flood indicators detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 0), 2)

        # Tree / debris heuristic if few detections
        if len(detections) < 2:
            tree_score = self._detect_tree_debris_heuristic(img)
            if tree_score > 0.2:
                detections.append({
                    'category': 'fallen_tree',
                    'confidence': min(0.7, tree_score),
                    'bbox': None,
                    'label': 'debris_heuristic',
                })

        # Save annotated image
        results_dir = Path(settings.MEDIA_ROOT) / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        fname = f"annotated_{Path(image_path).stem}_{int(time.time())}.jpg"
        out_path = results_dir / fname
        cv2.imwrite(str(out_path), img)
        results['annotated_path'] = f"results/{fname}"

        # Aggregate
        results['detections'] = detections
        results['total'] = len(detections)
        results['processing_time'] = round(time.time() - start, 2)
        results['severity'] = self._compute_severity(detections)
        results['summary'] = self._build_summary(detections, results['severity'])

        return results

    def _map_class(self, cls_id, label, img, xyxy):
        label_lower = label.lower()
        if any(k in label_lower for k in ['tree', 'plant', 'potted']):
            return 'fallen_tree'
        if any(k in label_lower for k in ['building', 'house', 'tower', 'bridge']):
            return 'damaged_building'
        if any(k in label_lower for k in ['car', 'truck', 'bus']):  # vehicles in flood often indicate road
            return 'other'
        # Default
        return 'other'

    def _detect_flood_heuristic(self, img):
        """Simple water detection via HSV blue/cyan dominance in lower half"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Water-ish range
        lower = np.array([80, 30, 30])
        upper = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        h = img.shape[0]
        lower_half = mask[h//2:, :]
        ratio = np.count_nonzero(lower_half) / lower_half.size
        return float(ratio)

    def _detect_tree_debris_heuristic(self, img):
        """Brown/green irregular textures"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Brown range for debris
        lower_brown = np.array([5, 40, 40])
        upper_brown = np.array([25, 255, 200])
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        ratio = np.count_nonzero(mask) / mask.size
        return float(ratio)

    def _get_color(self, category):
        colors = {
            'fallen_tree': (0, 180, 0),
            'damaged_building': (0, 0, 220),
            'flooded_road': (220, 120, 0),
            'debris': (0, 200, 200),
            'other': (180, 180, 0),
        }
        return colors.get(category, (200, 200, 200))

    def _compute_severity(self, detections):
        if not detections:
            return 'none'
        high_conf = [d for d in detections if d['confidence'] > 0.5]
        cats = set(d['category'] for d in detections)
        if len(high_conf) >= 3 or ('damaged_building' in cats and len(high_conf) >= 1):
            return 'high'
        if len(high_conf) >= 2 or len(cats) >= 2:
            return 'medium'
        if len(detections) >= 1:
            return 'low'
        return 'none'

    def _build_summary(self, detections, severity):
        if not detections:
            return ("No clear disaster-related damage objects were detected by the current model. "
                    "This is a preliminary visual assessment only and must be verified by field professionals.")
        cats = {}
        for d in detections:
            cats[d['category']] = cats.get(d['category'], 0) + 1
        parts = [f"{DAMAGE_LABELS.get(c, c)}: {n}" for c, n in cats.items()]
        summary = ("Detected visible indicators: " + "; ".join(parts) +
                   f". Overall estimated severity: {severity.upper()}. "
                   "IMPORTANT: This is a preliminary AI visual assessment based on the uploaded image. "
                   "It does not confirm structural safety. Always verify with qualified disaster-response teams.")
        return summary


# Singleton for reuse
_detector = None

def get_detector():
    global _detector
    if _detector is None:
        _detector = DisasterDamageDetector()
    return _detector
