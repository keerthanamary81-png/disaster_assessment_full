from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('user', 'Field User'),
        ('admin', 'Admin'),
        ('ngo', 'NGO Worker'),
        ('govt', 'Government Official'),
    ], default='user')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class DisasterImage(models.Model):
    DISASTER_TYPES = [
        ('flood', 'Flood'),
        ('cyclone', 'Cyclone'),
        ('storm', 'Storm'),
        ('earthquake', 'Earthquake'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    disaster_type = models.CharField(max_length=20, choices=DISASTER_TYPES)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_of_incident = models.DateField(default=timezone.now)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.disaster_type} - {self.location} ({self.uploaded_at.date()})"

    def filename(self):
        return os.path.basename(self.image.name)


class DamageAssessment(models.Model):
    SEVERITY_CHOICES = [
        ('none', 'No Visible Damage'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    image = models.OneToOneField(DisasterImage, on_delete=models.CASCADE, related_name='assessment')
    analysed_image = models.ImageField(upload_to='results/%Y/%m/%d/', blank=True, null=True)
    total_detections = models.PositiveIntegerField(default=0)
    overall_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='none')
    summary = models.TextField(blank=True)
    processing_time = models.FloatField(default=0.0)  # seconds
    model_version = models.CharField(max_length=50, default='YOLOv8')
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Assessment #{self.id} - {self.image.location}"


class DetectionResult(models.Model):
    CATEGORY_CHOICES = [
        ('fallen_tree', 'Fallen Tree / Debris'),
        ('damaged_building', 'Damaged Building'),
        ('flooded_road', 'Flooded Road'),
        ('debris', 'General Debris'),
        ('other', 'Other Visible Damage'),
        ('unsupported', 'Unsupported / Not Detected'),
    ]

    assessment = models.ForeignKey(DamageAssessment, on_delete=models.CASCADE, related_name='detections')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    confidence = models.FloatField()  # 0.0 to 1.0
    bbox_x = models.FloatField(null=True, blank=True)
    bbox_y = models.FloatField(null=True, blank=True)
    bbox_w = models.FloatField(null=True, blank=True)
    bbox_h = models.FloatField(null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)
    count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.get_category_display()} ({self.confidence:.2%})"

    @property
    def confidence_percent(self):
        return round(self.confidence * 100, 1)


class AssessmentReport(models.Model):
    assessment = models.OneToOneField(DamageAssessment, on_delete=models.CASCADE, related_name='report')
    report_file = models.FileField(upload_to='reports/%Y/%m/%d/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Assessment #{self.assessment.id}"
