# backend/playlists/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Playlist, Song, Vote
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import openai
import config

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
        num_songs = int(request.POST.get('num_songs', 50))
        playlist_name, description, song_list = generate_playlist_from_input(user_input, num_songs)
        playlist = Playlist.objects.create(name=playlist_name, description=description, spotify_url='https://open.spotify.com/playlist/...')
        
        for song in song_list:
            Song.objects.create(playlist=playlist, title=song['title'], artist=song['artist'], spotify_url=song['spotify_url'])
        
        return redirect('index')

    playlists = Playlist.objects.all()
    return render(request, 'index.html', {'playlists': playlists})

def generate_playlist_from_input(user_input, num_songs):
    # Call OpenAI API to generate playlist name and description
    openai.api_key = config.OPENAI_API_KEY

    # response = openai.Completion.create(
    #     model="text-davinci-002",
    #     prompt=f"Generate a spotify query using the {user_input}.
    #     Here are some examples:
        
    
    
    # ",
    #     max_tokens=50
    # )

    # playlist_name = response['choices'][0]['text'].strip()

    # Call Spotify API to get songs
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config.SPOTIFY_CLIENT_ID, client_secret=config.SPOTIFY_CLIENT_SECRET))
    results = sp.search(q=user_input, limit=num_songs, type='track')
    song_list = [{'title': track['name'], 'artist': track['artists'][0]['name'], 'spotify_url': track['external_urls']['spotify']} for track in results['tracks']['items']]
    response_topic = openai.Completion.create(
        model="text-davinci-002",
        prompt=f"Generate the playlist topic: {user_input}",
        max_tokens=50
    )
    description = f"{user_input}"
    return playlist_name, description, song_list

def about(request):
    return render(request, 'about.html')
