from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from authentication.models import CustomUser
from .models_profile import ProfileUserProfile, ProfileEducation, ProfileExperience, ProfileSkill, ProfileProject, ProfileCertification
from .forms_profile import (
    ProfileForm, SocialLinksForm, EducationForm, ExperienceForm,
    SkillForm, ProjectForm, CertificationForm, PrivacySettingsForm,
    ProfilePictureForm
)


@login_required
def profile_view(request):
    """View for displaying the user's profile."""
    # Ensure the user has a profile
    profile, created = ProfileUserProfile.objects.get_or_create(user=request.user)

    # Get related data
    education = ProfileEducation.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')
    experience = ProfileExperience.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')
    skills = ProfileSkill.objects.filter(user=request.user).order_by('-proficiency', 'order', 'name')
    projects = ProfileProject.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')
    certifications = ProfileCertification.objects.filter(user=request.user).order_by('-issue_date', 'order')

    # Get recent posts
    from home.models import Post
    from home.views import format_content_with_mentions

    recent_posts = Post.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Format post content with mentions
    for post in recent_posts:
        post.formatted_content = format_content_with_mentions(post.content)

    context = {
        'profile': profile,
        'profile_user': request.user,  # Add profile_user to match the template's expectations
        'education': education,
        'experience': experience,
        'skills': skills,
        'projects': projects,
        'certifications': certifications,
        'recent_posts': recent_posts,
        'completion_percentage': profile.get_completion_percentage(),
        'active_page': 'profile',
        'is_own_profile': True,  # This is the user's own profile
    }

    return render(request, 'home/profile/profile.html', context)


@login_required
def edit_profile_view(request):
    """View for editing basic profile information."""
    # Ensure the user has a profile
    profile, created = ProfileUserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully.'))
            return redirect('home:profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    context = {
        'form': form,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/edit_profile.html', context)


@login_required
def social_links_view(request):
    """View for editing social media links."""
    # Ensure the user has a profile
    profile, created = ProfileUserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SocialLinksForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Social links updated successfully.'))
            return redirect('home:profile')
    else:
        form = SocialLinksForm(user=request.user)

    context = {
        'form': form,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/social_links.html', context)


@login_required
def privacy_settings_view(request):
    """View for managing privacy settings."""
    # Ensure the user has a profile
    profile, created = ProfileUserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PrivacySettingsForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Privacy settings updated successfully.'))
            return redirect('home:profile')
    else:
        form = PrivacySettingsForm(user=request.user)

    context = {
        'form': form,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/privacy_settings.html', context)


@login_required
def upload_profile_picture(request):
    """View for uploading profile picture."""
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile picture updated successfully.'))
            return redirect('home:profile')
        else:
            messages.error(request, _('Error uploading profile picture. Please try again.'))

    return redirect('home:profile')


# Education views
@login_required
def education_list(request):
    """View for listing education entries."""
    education = ProfileEducation.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')

    context = {
        'education': education,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/education_list.html', context)


@login_required
def add_education(request):
    """View for adding a new education entry."""
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.user = request.user
            education.save()
            messages.success(request, _('Education added successfully.'))
            return redirect('home:profile')
    else:
        form = EducationForm()

    context = {
        'form': form,
        'active_page': 'profile',
        'is_add': True,
    }

    return render(request, 'home/profile/education_form.html', context)


@login_required
def edit_education(request, education_id):
    """View for editing an education entry."""
    education = get_object_or_404(ProfileEducation, id=education_id, user=request.user)

    if request.method == 'POST':
        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            form.save()
            messages.success(request, _('Education updated successfully.'))
            return redirect('home:profile')
    else:
        form = EducationForm(instance=education)

    context = {
        'form': form,
        'education': education,
        'active_page': 'profile',
        'is_add': False,
    }

    return render(request, 'home/profile/education_form.html', context)


@login_required
@require_POST
def delete_education(request, education_id):
    """View for deleting an education entry."""
    education = get_object_or_404(ProfileEducation, id=education_id, user=request.user)
    education.delete()
    messages.success(request, _('Education deleted successfully.'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('home:profile')


# Experience views
@login_required
def experience_list(request):
    """View for listing experience entries."""
    experience = ProfileExperience.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')

    context = {
        'experience': experience,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/experience_list.html', context)


@login_required
def add_experience(request):
    """View for adding a new experience entry."""
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.user = request.user
            experience.save()
            messages.success(request, _('Experience added successfully.'))
            return redirect('home:profile')
    else:
        form = ExperienceForm()

    context = {
        'form': form,
        'active_page': 'profile',
        'is_add': True,
    }

    return render(request, 'home/profile/experience_form.html', context)


@login_required
def edit_experience(request, experience_id):
    """View for editing an experience entry."""
    experience = get_object_or_404(ProfileExperience, id=experience_id, user=request.user)

    if request.method == 'POST':
        form = ExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, _('Experience updated successfully.'))
            return redirect('home:profile')
    else:
        form = ExperienceForm(instance=experience)

    context = {
        'form': form,
        'experience': experience,
        'active_page': 'profile',
        'is_add': False,
    }

    return render(request, 'home/profile/experience_form.html', context)


@login_required
@require_POST
def delete_experience(request, experience_id):
    """View for deleting an experience entry."""
    experience = get_object_or_404(ProfileExperience, id=experience_id, user=request.user)
    experience.delete()
    messages.success(request, _('Experience deleted successfully.'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('home:profile')


# Skill views
@login_required
def skill_list(request):
    """View for listing skills."""
    skills = ProfileSkill.objects.filter(user=request.user).order_by('-proficiency', 'order', 'name')

    context = {
        'skills': skills,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/skill_list.html', context)


@login_required
def add_skill(request):
    """View for adding a new skill."""
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            messages.success(request, _('Skill added successfully.'))
            return redirect('home:profile')
    else:
        form = SkillForm()

    context = {
        'form': form,
        'active_page': 'profile',
        'is_add': True,
    }

    return render(request, 'home/profile/skill_form.html', context)


@login_required
def edit_skill(request, skill_id):
    """View for editing a skill."""
    skill = get_object_or_404(ProfileSkill, id=skill_id, user=request.user)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, _('Skill updated successfully.'))
            return redirect('home:profile')
    else:
        form = SkillForm(instance=skill)

    context = {
        'form': form,
        'skill': skill,
        'active_page': 'profile',
        'is_add': False,
    }

    return render(request, 'home/profile/skill_form.html', context)


@login_required
@require_POST
def delete_skill(request, skill_id):
    """View for deleting a skill."""
    skill = get_object_or_404(ProfileSkill, id=skill_id, user=request.user)
    skill.delete()
    messages.success(request, _('Skill deleted successfully.'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('home:profile')


# Project views
@login_required
def project_list(request):
    """View for listing projects."""
    projects = ProfileProject.objects.filter(user=request.user).order_by('-end_date', '-start_date', 'order')

    context = {
        'projects': projects,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/project_list.html', context)


@login_required
def add_project(request):
    """View for adding a new project."""
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            messages.success(request, _('Project added successfully.'))
            return redirect('home:profile')
    else:
        form = ProjectForm()

    context = {
        'form': form,
        'active_page': 'profile',
        'is_add': True,
    }

    return render(request, 'home/profile/project_form.html', context)


@login_required
def edit_project(request, project_id):
    """View for editing a project."""
    project = get_object_or_404(ProfileProject, id=project_id, user=request.user)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, _('Project updated successfully.'))
            return redirect('home:profile')
    else:
        form = ProjectForm(instance=project)

    context = {
        'form': form,
        'project': project,
        'active_page': 'profile',
        'is_add': False,
    }

    return render(request, 'home/profile/project_form.html', context)


@login_required
@require_POST
def delete_project(request, project_id):
    """View for deleting a project."""
    project = get_object_or_404(ProfileProject, id=project_id, user=request.user)
    project.delete()
    messages.success(request, _('Project deleted successfully.'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('home:profile')


# Certification views
@login_required
def certification_list(request):
    """View for listing certifications."""
    certifications = ProfileCertification.objects.filter(user=request.user).order_by('-issue_date', 'order')

    context = {
        'certifications': certifications,
        'active_page': 'profile',
    }

    return render(request, 'home/profile/certification_list.html', context)


@login_required
def add_certification(request):
    """View for adding a new certification."""
    if request.method == 'POST':
        form = CertificationForm(request.POST)
        if form.is_valid():
            certification = form.save(commit=False)
            certification.user = request.user
            certification.save()
            messages.success(request, _('Certification added successfully.'))
            return redirect('home:profile')
    else:
        form = CertificationForm()

    context = {
        'form': form,
        'active_page': 'profile',
        'is_add': True,
    }

    return render(request, 'home/profile/certification_form.html', context)


@login_required
def edit_certification(request, certification_id):
    """View for editing a certification."""
    certification = get_object_or_404(ProfileCertification, id=certification_id, user=request.user)

    if request.method == 'POST':
        form = CertificationForm(request.POST, instance=certification)
        if form.is_valid():
            form.save()
            messages.success(request, _('Certification updated successfully.'))
            return redirect('home:profile')
    else:
        form = CertificationForm(instance=certification)

    context = {
        'form': form,
        'certification': certification,
        'active_page': 'profile',
        'is_add': False,
    }

    return render(request, 'home/profile/certification_form.html', context)


@login_required
@require_POST
def delete_certification(request, certification_id):
    """View for deleting a certification."""
    certification = get_object_or_404(ProfileCertification, id=certification_id, user=request.user)
    certification.delete()
    messages.success(request, _('Certification deleted successfully.'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('home:profile')


# Public profile view
def public_profile_view(request, username):
    """View for displaying a user's public profile."""
    user = get_object_or_404(CustomUser, username=username)

    # Check if the profile exists, if not, create it
    profile, created = ProfileUserProfile.objects.get_or_create(user=user)

    # Get privacy settings
    privacy_settings = profile.privacy_settings or {}

    # Determine what data to show based on privacy settings
    context = {
        'profile_user': user,
        'profile': profile,
        'active_page': 'profile',
        'is_own_profile': request.user == user,
    }

    # Helper function to check if a section should be visible
    def is_visible(section):
        setting = privacy_settings.get(section, 'public')
        if setting == 'public':
            return True
        elif setting == 'registered' and request.user.is_authenticated:
            return True
        elif setting == 'private' and request.user == user:
            return True
        return False

    # Add data to context based on privacy settings
    if is_visible('education'):
        context['education'] = ProfileEducation.objects.filter(user=user, is_visible=True).order_by('-end_date', '-start_date', 'order')

    if is_visible('experience'):
        context['experience'] = ProfileExperience.objects.filter(user=user, is_visible=True).order_by('-end_date', '-start_date', 'order')

    if is_visible('skills'):
        context['skills'] = ProfileSkill.objects.filter(user=user, is_visible=True).order_by('-proficiency', 'order', 'name')

    if is_visible('projects'):
        context['projects'] = ProfileProject.objects.filter(user=user, is_visible=True).order_by('-end_date', '-start_date', 'order')

    if is_visible('certifications'):
        context['certifications'] = ProfileCertification.objects.filter(user=user, is_visible=True).order_by('-issue_date', 'order')

    # Get recent posts
    from home.models import Post
    from home.views import format_content_with_mentions

    recent_posts = Post.objects.filter(user=user).order_by('-created_at')[:5]

    # Format post content with mentions
    for post in recent_posts:
        post.formatted_content = format_content_with_mentions(post.content)

    context['recent_posts'] = recent_posts

    # Add visibility flags to context
    context['show_bio'] = is_visible('bio')
    context['show_location'] = is_visible('location')
    context['show_website'] = is_visible('website')
    context['show_social_links'] = is_visible('social_links')

    return render(request, 'home/profile/public_profile.html', context)
