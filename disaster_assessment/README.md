# AI-Based Disaster Damage Assessment and Reporting System

Professional Django web application that uses YOLOv8 (Ultralytics) + OpenCV to analyse disaster images for visible damage (fallen trees, structural indicators, flooded areas) and generates PDF assessment reports.

## Features

- User registration, login, profile
- Image upload (JPG/PNG) with drag-and-drop
- Real YOLOv8 object detection + flood/debris heuristics
- Bounding boxes on annotated images
- Confidence scores & severity estimation
- Category-wise statistics & Chart.js charts
- Downloadable professional PDF reports
- Assessment history with search/filter
- Admin panel for users & overall stats
- MySQL database support
- Modern blue/white responsive UI

## Important AI Notes

- Uses **real** Ultralytics YOLOv8 model (auto-downloads `yolov8n.pt` on first run).
- Pre-trained COCO weights + colour heuristics for flood water and debris.
- For production accuracy on disaster imagery, fine-tune YOLO on a labelled disaster-damage dataset (e.g. from xBD, DisasterNet, or your own annotations with classes: `fallen_tree`, `damaged_building`, `flooded_road`).
- Place custom weights at `ai_models/disaster_yolo.pt` and update `YOLO_MODEL_PATH` in settings.
- **Disclaimer always shown**: Results are preliminary visual assessment only and require professional verification. The system does **not** confirm structural safety.

## Requirements

- Python 3.10+
- MySQL 8.x (or use SQLite for quick testing)
- 4GB+ RAM recommended for YOLO

## Installation (Step-by-step)

### 1. Create virtual environment
```bash
cd disaster_assessment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
(If `mysqlclient` fails, we already use `PyMySQL`. For ultralytics/torch it may take time and download large packages.)

### 3. Configure MySQL
Create database:
```sql
CREATE DATABASE disaster_assessment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Edit `disaster_project/settings.py`:
- Set `PASSWORD` under DATABASES
- Or comment MySQL block and uncomment the SQLite fallback for testing without MySQL.

Add to `disaster_project/__init__.py` (for PyMySQL):
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 4. Migrate
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/

### 6. First AI run
On first analysis YOLO will download `yolov8n.pt` (~6 MB) into the project or cache. Ensure internet is available once.

## Project Structure
```
disaster_assessment/
├── accounts/          # Auth views
├── assessments/       # Core models, AI, PDF, views
│   └── utils/
│       ├── ai_detector.py
│       └── pdf_report.py
├── dashboard/         # Home & admin
├── disaster_project/  # Settings, urls
├── templates/
├── static/
├── media/             # Uploaded & annotated images
├── ai_models/         # Place custom .pt here
├── requirements.txt
└── manage.py
```

## Training a Custom Disaster Model (Optional Advanced)

1. Collect / download labelled images (fallen trees, damaged buildings, flooded roads).
2. Use Roboflow or LabelImg to create YOLO format dataset.
3. Train:
```bash
yolo detect train data=your_data.yaml model=yolov8n.pt epochs=50 imgsz=640
```
4. Copy best.pt to `ai_models/disaster_yolo.pt` and update settings.

## Technologies
- Django 4.2 / 5.x
- Bootstrap 5 + custom CSS
- Chart.js
- Ultralytics YOLOv8
- OpenCV
- ReportLab (PDF)
- MySQL / PyMySQL

## Disclaimer
This system provides **preliminary visual damage indicators only**. It is not a substitute for professional structural assessment, engineering inspection, or official disaster management decisions.

---
Built as a complete professional project suitable for academic / company evaluation.
