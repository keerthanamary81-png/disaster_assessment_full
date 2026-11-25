from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:pk>/', views.assessment_result, name='result'),
    path('history/', views.history, name='history'),
    path('report/<int:pk>/', views.download_report, name='download_report'),
    path('delete/<int:pk>/', views.delete_assessment, name='delete'),
]
