from django.contrib import admin
from .models import Profile, DisasterImage, DamageAssessment, DetectionResult, AssessmentReport

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'organization', 'phone', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'organization']

@admin.register(DisasterImage)
class DisasterImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'disaster_type', 'location', 'user', 'uploaded_at']
    list_filter = ['disaster_type', 'uploaded_at']
    search_fields = ['location', 'user__username']

class DetectionInline(admin.TabularInline):
    model = DetectionResult
    extra = 0

@admin.register(DamageAssessment)
class DamageAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'overall_severity', 'total_detections', 'created_at', 'is_verified']
    list_filter = ['overall_severity', 'is_verified', 'created_at']
    inlines = [DetectionInline]

@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'category', 'confidence', 'label']
    list_filter = ['category']

@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'generated_at']
