# backend/playlists/models.py
from django.db import models

class Playlist(models.Model):
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    spotify_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class Song(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='songs', on_delete=models.CASCADE,null=True, blank=True)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    spotify_url = models.URLField()
    id = models.CharField(max_length=40, primary_key=True, editable=False)

class Episode(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='episode', on_delete=models.CASCADE,null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    release_date = models.DateField()
    spotify_url = models.URLField(max_length=200)
    performer = models.CharField(max_length=255)
    id = models.CharField(max_length=100, primary_key=True)

class Vote(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()  # True for upvote, False for downvote
    created_at = models.DateTimeField(auto_now_add=True)

