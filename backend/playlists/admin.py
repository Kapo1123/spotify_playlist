# backend/playlists/admin.py

from django.contrib import admin
from .models import Playlist, Song, Vote,Episode

# Register your models here
admin.site.register(Playlist)
admin.site.register(Song)
admin.site.register(Episode)
admin.site.register(Vote)
