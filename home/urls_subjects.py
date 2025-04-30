from django.urls import path
from . import views_subjects

urlpatterns = [
    # Web views
    path('subjects/', views_subjects.subjects_list, name='subjects_list'),
    path('subjects/my/', views_subjects.my_subjects, name='my_subjects'),
    path('subjects/<str:subject_code>/', views_subjects.subject_detail, name='subject_detail'),
    path('subjects/<int:subject_id>/enroll/', views_subjects.enroll_subject, name='enroll_subject'),
    path('subjects/<int:subject_id>/unenroll/', views_subjects.unenroll_subject, name='unenroll_subject'),
    
    # API endpoints for mobile app
    path('api/subjects/', views_subjects.api_subjects_list, name='api_subjects_list'),
    path('api/subjects/<int:subject_id>/', views_subjects.api_subject_detail, name='api_subject_detail'),
]
