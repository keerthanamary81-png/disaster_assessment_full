from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib.auth.models import User
from assessments.models import DisasterImage, DamageAssessment, DetectionResult
from django.utils import timezone
from datetime import timedelta


@login_required
def home(request):
    user = request.user
    is_admin = user.is_staff or user.is_superuser

    if is_admin:
        total_images = DisasterImage.objects.count()
        total_assessments = DamageAssessment.objects.count()
        total_users = User.objects.count()
        recent = DamageAssessment.objects.select_related('image', 'image__user').order_by('-created_at')[:8]
        category_stats = DetectionResult.objects.values('category').annotate(count=Count('id')).order_by('-count')
        severity_stats = DamageAssessment.objects.values('overall_severity').annotate(count=Count('id'))
    else:
        total_images = DisasterImage.objects.filter(user=user).count()
        total_assessments = DamageAssessment.objects.filter(image__user=user).count()
        total_users = 1
        recent = DamageAssessment.objects.filter(image__user=user).select_related('image').order_by('-created_at')[:8]
        category_stats = DetectionResult.objects.filter(assessment__image__user=user).values('category').annotate(count=Count('id')).order_by('-count')
        severity_stats = DamageAssessment.objects.filter(image__user=user).values('overall_severity').annotate(count=Count('id'))

    # Chart data
    cat_labels = [c['category'].replace('_', ' ').title() for c in category_stats]
    cat_counts = [c['count'] for c in category_stats]
    sev_labels = [s['overall_severity'].title() for s in severity_stats]
    sev_counts = [s['count'] for s in severity_stats]

    # Last 7 days activity
    days = []
    day_counts = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        days.append(day.strftime('%d %b'))
        if is_admin:
            cnt = DamageAssessment.objects.filter(created_at__date=day).count()
        else:
            cnt = DamageAssessment.objects.filter(image__user=user, created_at__date=day).count()
        day_counts.append(cnt)

    context = {
        'total_images': total_images,
        'total_assessments': total_assessments,
        'total_users': total_users,
        'recent_assessments': recent,
        'cat_labels': cat_labels,
        'cat_counts': cat_counts,
        'sev_labels': sev_labels,
        'sev_counts': sev_counts,
        'days': days,
        'day_counts': day_counts,
        'is_admin': is_admin,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def admin_panel(request):
    if not (request.user.is_staff or request.user.is_superuser):
        from django.contrib import messages
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard:home')

    users = User.objects.all().select_related('profile').order_by('-date_joined')[:50]
    assessments = DamageAssessment.objects.select_related('image', 'image__user').order_by('-created_at')[:30]
    cat_stats = DetectionResult.objects.values('category').annotate(count=Count('id')).order_by('-count')

    return render(request, 'dashboard/admin_panel.html', {
        'users': users,
        'assessments': assessments,
        'cat_stats': cat_stats,
        'total_users': User.objects.count(),
        'total_assessments': DamageAssessment.objects.count(),
    })
