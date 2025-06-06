"""
URL configuration for E_Platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('home/', include('home.urls', namespace='home')),
    path('chat/', include('chatting.urls', namespace='chatting')),  # Chat app URLs
    path('ai/', include('Ai_prototype.urls', namespace='ai_prototype')),  # AI prototype app URLs

    # API URLs
    path('api/auth/', include('authentication.api.urls')),
    path('api/', include('home.api.urls')),
    path('api/chat/', include('chatting.api.urls', namespace='chat_api')),  # Chat API URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
