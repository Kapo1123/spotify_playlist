# backend/spotify_playlist/urls.py
from django.contrib import admin
from django.urls import path, include
from playlists import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
]
