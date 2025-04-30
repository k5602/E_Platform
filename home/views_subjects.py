from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Subject, SubjectMaterial, SubjectEnrollment

@login_required
def subjects_list(request):
    """View for displaying all available subjects."""
    subjects = Subject.objects.filter(is_active=True)

    # Get user's enrolled subjects
    if request.user.is_authenticated:
        enrolled_subjects = [
            enrollment.subject.id
            for enrollment in SubjectEnrollment.objects.filter(
                student=request.user,
                is_active=True
            )
        ]
    else:
        enrolled_subjects = []

    context = {
        'subjects': subjects,
        'enrolled_subjects': enrolled_subjects,
        'active_page': 'subjects'
    }

    return render(request, 'home/subjects/subjects_list.html', context)

@login_required
def subject_detail(request, subject_code):
    """View for displaying details of a specific subject."""
    try:
        subject = get_object_or_404(Subject, code=subject_code, is_active=True)

        # Check if user is enrolled - force a fresh check from the database
        is_enrolled = SubjectEnrollment.objects.filter(
            student=request.user,
            subject=subject,
            is_active=True
        ).exists()

        # Get subject materials
        materials = SubjectMaterial.objects.filter(
            subject=subject,
            is_active=True
        )

        # Organize materials by type
        organized_materials = {
            'documents': materials.filter(material_type='document'),
            'videos': materials.filter(material_type='video'),
            'links': materials.filter(material_type='link'),
            'assignments': materials.filter(material_type='assignment'),
        }

        context = {
            'subject': subject,
            'is_enrolled': is_enrolled,
            'materials': organized_materials,
            'active_page': 'subjects'
        }

        return render(request, 'home/subjects/subject_detail.html', context)
    except Exception as e:
        # Log the error
        print(f"Error in subject_detail view: {str(e)}")
        messages.error(request, f"An error occurred while loading the subject: {str(e)}")
        return redirect('home:subjects_list')

@login_required
@require_POST
def enroll_subject(request, subject_id):
    """View for enrolling in a subject."""
    subject = get_object_or_404(Subject, id=subject_id, is_active=True)

    # Check if already enrolled with active enrollment
    if subject.is_user_enrolled(request.user):
        messages.info(request, f"You are already enrolled in {subject.name}.")
        return redirect('home:subject_detail', subject_code=subject.code)

    # Check if there's an inactive enrollment that can be reactivated
    try:
        enrollment = SubjectEnrollment.objects.get(
            student=request.user,
            subject=subject,
            is_active=False
        )
        # Reactivate the enrollment
        enrollment.is_active = True
        enrollment.save()
        messages.success(request, f"Successfully re-enrolled in {subject.name}!")
    except SubjectEnrollment.DoesNotExist:
        # Create a new enrollment
        SubjectEnrollment.objects.create(
            student=request.user,
            subject=subject
        )
        messages.success(request, f"Successfully enrolled in {subject.name}!")

    return redirect('home:subject_detail', subject_code=subject.code)

@login_required
@require_POST
def unenroll_subject(request, subject_id):
    """View for unenrolling from a subject."""
    subject = get_object_or_404(Subject, id=subject_id)

    # Try to find the enrollment
    try:
        enrollment = SubjectEnrollment.objects.get(
            student=request.user,
            subject=subject,
            is_active=True
        )

        # Deactivate enrollment if found
        enrollment.is_active = False
        enrollment.save()

        messages.success(request, f"Successfully unenrolled from {subject.name}.")
    except SubjectEnrollment.DoesNotExist:
        # Handle case when user is not enrolled
        messages.warning(request, f"You are not enrolled in {subject.name}.")

    # Redirect back to the subject detail page instead of the subjects list
    return redirect('home:subject_detail', subject_code=subject.code)

@login_required
def my_subjects(request):
    """View for displaying user's enrolled subjects."""
    enrollments = SubjectEnrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('subject')

    subjects = [enrollment.subject for enrollment in enrollments]

    context = {
        'subjects': subjects,
        'active_page': 'subjects',
        'my_subjects': True
    }

    return render(request, 'home/subjects/my_subjects.html', context)

# API Views for mobile app
@login_required
def api_subjects_list(request):
    """API endpoint for listing subjects."""
    subjects = Subject.objects.filter(is_active=True)

    # Get user's enrolled subjects
    enrolled_subject_ids = [
        enrollment.subject.id
        for enrollment in SubjectEnrollment.objects.filter(
            student=request.user,
            is_active=True
        )
    ]

    subjects_data = []
    for subject in subjects:
        subjects_data.append({
            'id': subject.id,
            'code': subject.code,
            'name': subject.name,
            'description': subject.description,
            'icon_name': subject.icon_name,
            'background_icon': subject.background_icon,
            'is_enrolled': subject.id in enrolled_subject_ids,
            'instructor': subject.instructor.get_full_name() if subject.instructor else None,
            'students_count': subject.get_enrolled_students_count()
        })

    return JsonResponse({
        'status': 'success',
        'subjects': subjects_data
    })

@login_required
def api_subject_detail(request, subject_id):
    """API endpoint for subject details."""
    subject = get_object_or_404(Subject, id=subject_id, is_active=True)

    # Check if user is enrolled
    is_enrolled = subject.is_user_enrolled(request.user)

    # Get subject materials
    materials = SubjectMaterial.objects.filter(
        subject=subject,
        is_active=True
    )

    materials_data = []
    for material in materials:
        material_data = {
            'id': material.id,
            'title': material.title,
            'description': material.description,
            'type': material.material_type,
            'created_at': material.created_at.isoformat()
        }

        if material.file:
            material_data['file_url'] = request.build_absolute_uri(material.file.url)

        if material.external_url:
            material_data['external_url'] = material.external_url

        materials_data.append(material_data)

    subject_data = {
        'id': subject.id,
        'code': subject.code,
        'name': subject.name,
        'description': subject.description,
        'icon_name': subject.icon_name,
        'background_icon': subject.background_icon,
        'is_enrolled': is_enrolled,
        'instructor': subject.instructor.get_full_name() if subject.instructor else None,
        'students_count': subject.get_enrolled_students_count(),
        'materials': materials_data
    }

    return JsonResponse({
        'status': 'success',
        'subject': subject_data
    })
