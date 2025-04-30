from django.urls import path
from . import views

app_name = 'ai_prototype'

urlpatterns = [
    # Main AI Assistant page
    path('assistant/', views.ai_assistant_page, name='ai_assistant'),
    
    # API endpoints for mock AI feedback
    path('api/feedback/<str:submission_id>/', views.generate_mock_feedback_view, name='generate_feedback'),
    path('api/feedback/', views.generate_mock_feedback_view, name='generate_feedback_random'),
    path('api/feedback-request/', views.feedback_request_view, name='feedback_request'),
]