from django.urls import path
from . import views_quiz

urlpatterns = [
    # Quiz Web Views
    path('quizzes/', views_quiz.quiz_list, name='quiz_list'),
    path('quizzes/my/', views_quiz.my_quizzes, name='my_quizzes'),
    path('quizzes/create/', views_quiz.create_quiz, name='create_quiz'),
    path('quizzes/<int:quiz_id>/', views_quiz.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/edit/', views_quiz.edit_quiz, name='quiz_edit'),
    path('quizzes/<int:quiz_id>/delete/', views_quiz.delete_quiz, name='delete_quiz'),
    path('quizzes/<int:quiz_id>/questions/', views_quiz.manage_questions, name='manage_questions'),
    path('quizzes/<int:quiz_id>/analytics/', views_quiz.quiz_analytics, name='quiz_analytics'),
    path('quizzes/<int:quiz_id>/start/', views_quiz.start_quiz, name='start_quiz'),
    
    # Question Management
    path('questions/<int:quiz_id>/add/', views_quiz.add_question, name='add_question'),
    path('questions/<int:question_id>/edit/', views_quiz.edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', views_quiz.delete_question, name='delete_question'),
    path('questions/<int:question_id>/answers/', views_quiz.manage_answers, name='manage_answers'),
    
    # Quiz Attempt Views
    path('attempt/<int:attempt_id>/take/', views_quiz.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/result/', views_quiz.quiz_result, name='quiz_result'),
    
    # AJAX Operations
    path('api/questions/reorder/', views_quiz.update_question_order, name='update_question_order'),
    path('api/answers/reorder/', views_quiz.update_answer_order, name='update_answer_order'),
    path('api/answers/<int:answer_id>/mark/', views_quiz.mark_short_answer, name='mark_short_answer'),
]
