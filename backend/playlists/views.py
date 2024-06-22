# backend/playlists/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Playlist, Song, Vote
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import openai

def index(request):
    if request.method == 'POST':
        user_input = request.POST['user_input']
        playlist_name, description, song_list = generate_playlist_from_input(user_input)
        playlist = Playlist.objects.create(name=playlist_name, description=description, spotify_url='https://open.spotify.com/playlist/...')
        
        for song in song_list:
            Song.objects.create(playlist=playlist, title=song['title'], artist=song['artist'], spotify_url=song['spotify_url'])
        
        return redirect('index')

    playlists = Playlist.objects.all()
    return render(request, 'index.html', {'playlists': playlists})

def about(request):
    return render(request, 'about.html')

def generate_playlist_from_input(user_input):
    # Call OpenAI API to generate playlist name and description
    openai.api_key = 'your-openai-api-key'
    response = openai.Completion.create(
      model="text-davinci-002",
      prompt=f"Generate a playlist based on: {user_input}",
      max_tokens=50
    )
    playlist_name = response['choices'][0]['text'].strip()

    # Call Spotify API to get songs
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='your-client-id', client_secret='your-client-secret', redirect_uri='your-redirect-uri', scope='playlist-modify-public'))
    results = sp.search(q=user_input, limit=20, type='track')
    song_list = [{'title': track['name'], 'artist': track['artists'][0]['name'], 'spotify_url': track['external_urls']['spotify']} for track in results['tracks']['items']]

    description = f"A playlist generated based on the input: {user_input}"
    return playlist_name, description, song_list
