# backend/spotify_playlist/urls.py
from django.contrib import admin
from django.urls import path, include
from playlists import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('spotify_callback/', views.spotify_callback, name='spotify_callback'),
    path('about/', views.about, name='about'),
    path('delete_playlist/<str:playlist_id>/', views.delete_playlist, name='delete_playlist'),
]

