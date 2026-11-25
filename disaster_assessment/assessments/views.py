from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from pathlib import Path
import os

from .forms import DisasterImageForm
from .models import DisasterImage, DamageAssessment, DetectionResult, AssessmentReport
from .utils.ai_detector import get_detector
from .utils.pdf_report import generate_assessment_pdf


@login_required
def upload_image(request):
    if request.method == 'POST':
        form = DisasterImageForm(request.POST, request.FILES)
        if form.is_valid():
            disaster_img = form.save(commit=False)
            disaster_img.user = request.user
            disaster_img.save()

            # Run AI detection
            detector = get_detector()
            img_path = disaster_img.image.path
            result = detector.detect(img_path)

            # Create assessment
            assessment = DamageAssessment.objects.create(
                image=disaster_img,
                total_detections=result['total'],
                overall_severity=result['severity'],
                summary=result['summary'],
                processing_time=result['processing_time'],
                model_version=result['model_used'],
            )

            if result['annotated_path']:
                # Save relative path
                assessment.analysed_image.name = result['annotated_path']
                assessment.save()

            # Save individual detections
            for det in result['detections']:
                bbox = det.get('bbox')
                DetectionResult.objects.create(
                    assessment=assessment,
                    category=det['category'],
                    confidence=det['confidence'],
                    bbox_x=bbox[0] if bbox else None,
                    bbox_y=bbox[1] if bbox else None,
                    bbox_w=bbox[2] if bbox else None,
                    bbox_h=bbox[3] if bbox else None,
                    label=det.get('label', ''),
                )

            messages.success(request, 'Image analysed successfully. View the assessment result.')
            return redirect('assessments:result', pk=assessment.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DisasterImageForm()

    return render(request, 'assessments/upload.html', {'form': form})


@login_required
def assessment_result(request, pk):
    assessment = get_object_or_404(DamageAssessment, pk=pk, image__user=request.user)
    detections = assessment.detections.all()
    return render(request, 'assessments/result.html', {
        'assessment': assessment,
        'detections': detections,
        'image': assessment.image,
    })


@login_required
def history(request):
    qs = DamageAssessment.objects.filter(image__user=request.user).select_related('image').order_by('-created_at')

    disaster_type = request.GET.get('disaster_type')
    location = request.GET.get('location')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if disaster_type:
        qs = qs.filter(image__disaster_type=disaster_type)
    if location:
        qs = qs.filter(image__location__icontains=location)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    return render(request, 'assessments/history.html', {
        'assessments': qs,
        'filters': {
            'disaster_type': disaster_type or '',
            'location': location or '',
            'date_from': date_from or '',
            'date_to': date_to or '',
        }
    })


@login_required
def download_report(request, pk):
    assessment = get_object_or_404(DamageAssessment, pk=pk, image__user=request.user)
    # Generate PDF if not exists
    report, created = AssessmentReport.objects.get_or_create(assessment=assessment)
    if not report.report_file or created:
        pdf_path = generate_assessment_pdf(assessment)
        if pdf_path:
            report.report_file.name = pdf_path
            report.save()

    if report.report_file and os.path.exists(report.report_file.path):
        return FileResponse(
            open(report.report_file.path, 'rb'),
            as_attachment=True,
            filename=f"Damage_Assessment_Report_{assessment.id}.pdf"
        )
    messages.error(request, 'Could not generate PDF report.')
    return redirect('assessments:result', pk=pk)


@login_required
def delete_assessment(request, pk):
    assessment = get_object_or_404(DamageAssessment, pk=pk, image__user=request.user)
    if request.method == 'POST':
        # Delete files
        if assessment.image.image:
            assessment.image.image.delete(save=False)
        if assessment.analysed_image:
            assessment.analysed_image.delete(save=False)
        assessment.image.delete()
        messages.success(request, 'Assessment deleted.')
        return redirect('assessments:history')
    return render(request, 'assessments/confirm_delete.html', {'assessment': assessment})
