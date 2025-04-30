from django.urls import path
from . import views_profile

urlpatterns = [
    # Basic profile views
    path('profile/', views_profile.profile_view, name='profile'),
    path('profile/edit/', views_profile.edit_profile_view, name='edit_profile'),
    path('profile/social-links/', views_profile.social_links_view, name='social_links'),
    path('profile/privacy-settings/', views_profile.privacy_settings_view, name='privacy_settings'),
    path('profile/upload-picture/', views_profile.upload_profile_picture, name='upload_profile_picture'),
    
    # Education views
    path('profile/education/', views_profile.education_list, name='education_list'),
    path('profile/education/add/', views_profile.add_education, name='add_education'),
    path('profile/education/<int:education_id>/edit/', views_profile.edit_education, name='edit_education'),
    path('profile/education/<int:education_id>/delete/', views_profile.delete_education, name='delete_education'),
    
    # Experience views
    path('profile/experience/', views_profile.experience_list, name='experience_list'),
    path('profile/experience/add/', views_profile.add_experience, name='add_experience'),
    path('profile/experience/<int:experience_id>/edit/', views_profile.edit_experience, name='edit_experience'),
    path('profile/experience/<int:experience_id>/delete/', views_profile.delete_experience, name='delete_experience'),
    
    # Skill views
    path('profile/skills/', views_profile.skill_list, name='skill_list'),
    path('profile/skills/add/', views_profile.add_skill, name='add_skill'),
    path('profile/skills/<int:skill_id>/edit/', views_profile.edit_skill, name='edit_skill'),
    path('profile/skills/<int:skill_id>/delete/', views_profile.delete_skill, name='delete_skill'),
    
    # Project views
    path('profile/projects/', views_profile.project_list, name='project_list'),
    path('profile/projects/add/', views_profile.add_project, name='add_project'),
    path('profile/projects/<int:project_id>/edit/', views_profile.edit_project, name='edit_project'),
    path('profile/projects/<int:project_id>/delete/', views_profile.delete_project, name='delete_project'),
    
    # Certification views
    path('profile/certifications/', views_profile.certification_list, name='certification_list'),
    path('profile/certifications/add/', views_profile.add_certification, name='add_certification'),
    path('profile/certifications/<int:certification_id>/edit/', views_profile.edit_certification, name='edit_certification'),
    path('profile/certifications/<int:certification_id>/delete/', views_profile.delete_certification, name='delete_certification'),
    
    # Public profile view
    path('profile/<str:username>/', views_profile.public_profile_view, name='public_profile'),
]
