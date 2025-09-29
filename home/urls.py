from django.urls import path, include
from . import views
from .urls_subjects import urlpatterns as subject_urlpatterns
from .urls_profile import urlpatterns as profile_urlpatterns
from .urls_quiz import urlpatterns as quiz_urlpatterns

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('post/<int:post_id>/comments/', views.get_post_comments, name='get_post_comments'),
    path('post/<int:post_id>/likes/', views.get_post_likes, name='get_post_likes'),
    path('contact/', views.contact_view, name='contact'),

    # Notification and mention system URLs
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/count/', views.get_unread_notification_count, name='notification_count'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_all_notifications_read'),
    path('api/notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/users/search/', views.search_users_view, name='search_users_api'),
    path('api/users/suggestions/', views.search_suggestions, name='search_suggestions'),
    # Add a more specific URL pattern for search suggestions
    path('search/suggestions/', views.search_suggestions, name='search_suggestions_alt'),
    path('search/', views.search_users, name='search_users'),

]

# Add subject URL patterns
urlpatterns += subject_urlpatterns

# Add profile URL patterns
urlpatterns += profile_urlpatterns

# Add quiz URL patterns
urlpatterns += quiz_urlpatterns
