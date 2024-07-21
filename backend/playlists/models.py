# backend/playlists/models.py
from django.db import models

class Playlist(models.Model):
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    spotify_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class Song(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='songs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    spotify_url = models.URLField()
    id = models.CharField(max_length=40, primary_key=True, editable=False)

class Vote(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()  # True for upvote, False for downvote
    created_at = models.DateTimeField(auto_now_add=True)

