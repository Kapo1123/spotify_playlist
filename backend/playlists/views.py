# backend/playlists/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Playlist, Song, Vote
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import openai
import config
client_id = config.SPOTIFY_CLIENT_ID
client_secret = config.SPOTIFY_CLIENT_SECRET
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
def index(request):
    if request.method == 'POST':
        types = request.POST.getlist('type[]')
        names = request.POST.getlist('name[]')
        limits = request.POST.getlist('limit[]')

        user_inputs = []
        for type, name, limit in zip(types, names, limits):
            user_inputs.append({
                'type': type,
                'name': name,
                'limit': int(limit)
            })
        playlist_name, description, song_list = generate_playlist_general(user_inputs)
        playlist = Playlist.objects.create(name=playlist_name, description=description, spotify_url='https://open.spotify.com/playlist/...')
        
        for song in song_list:
            Song.objects.create(playlist=playlist, title=song['title'], artist=song['artist'], spotify_url=song['spotify_url'])
        
        return redirect('index')

    playlists = Playlist.objects.all()
    return render(request, 'index.html', {'playlists': playlists})

def generate_playlist_withAI(user_input, num_songs):
    # Call OpenAI API to generate playlist name and description
    openai.api_key = config.OPENAI_API_KEY

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=f'Generate a spotify query using the {user_input}.Here are some examples:',
        max_tokens=50
    )

    playlist_name = response['choices'][0]['text'].strip()

    # Call Spotify API to get songs
    results = spotify.search(q=user_input, limit=num_songs, type='track')
    song_list = [{'title': track['name'], 'artist': track['artists'][0]['name'], 'spotify_url': track['external_urls']['spotify']} for track in results['tracks']['items']]
    response_topic = openai.Completion.create(
        model="text-davinci-002",
        prompt=f"Generate the playlist topic: {user_input}",
        max_tokens=50
    )
    description = f"{user_input}"
    return playlist_name, description, song_list

def generate_playlist_general(user_input):
    # Call OpenAI API to generate playlist name and description
    openai.api_key = config.OPENAI_API_KEY
    results=[]
    for input in user_input:
        type = input['type']
        name = input['name']
        num = input['limit']
        results.append(spotify.search(q=f'{type}:{name}', limit=num, type='track'))
    
    song_list = [{'title': track['name'], 'artist': track['artists'][0]['name'], 'spotify_url': track['external_urls']['spotify']} for track in results['tracks']['items']]
    response_topic = openai.Completion.create(
        model="text-davinci-002",
        prompt=f"Generate a sptify playlist name according to the following user input : {user_input}, Also this is number {len(Playlist.objects.all())}",
        max_tokens=50
    )
    description = f"{user_input}"
    return response_topic, description, song_list

def about(request):
    return render(request, 'about.html')
