# backend/playlists/views.py
from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse
from .models import Playlist, Song, Vote
from django.http import HttpResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials,SpotifyOAuth
from openai import OpenAI
import config
client_id = config.SPOTIFY_CLIENT_ID
client_secret = config.SPOTIFY_CLIENT_SECRET
# spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
openAiClient = OpenAI(
    api_key = config.OPENAI_API_KEY,
    organization = config.OPENAI_ORGID
)
spotyfy_id ='31w2e7ljo6jmke3rthgxk6wzpigy'
sp_oauth = SpotifyOAuth(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
    redirect_uri=config.SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public"
)
def index(request):
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    access_token = token_info['access_token']
    spotify = Spotify(auth=access_token)
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
        form_type = request.POST.get('form_type')
        if form_type != 'ai':
            generate_playlist_general(user_inputs,spotify)
        else:
            generate_playlist_withAI(user_inputs,spotify)
        
        return redirect('index')

    playlists = Playlist.objects.all()
    return render(request, 'index.html', {'playlists': playlists})
def spotify_callback(request):
    code = request.GET.get('code')
    token_info = sp_oauth.get_access_token(code)
    
    if token_info:
        access_token = token_info['access_token']
        spotify = Spotify(auth=access_token)
        
        user_id = spotify.me()['id']
        request.session['access_token'] = access_token
        request.session['user_id'] = user_id
        
        return redirect('index')
    else:
        return HttpResponse('Authentication failed')
def generate_playlist_withAI(user_input):
    # Call OpenAI API to generate playlist name and description

    response = openAiClient.chat.Completion.create(
        model="text-davinci-002",
        prompt=f'Generate a spotify query using the {user_input}.Here are some examples:',
        max_tokens=50
    )

    playlist_name = response['choices'][0]['text'].strip()

    # Call Spotify API to get songs
    results = spotify.search(q=user_input, limit=num_songs, type='track')
    song_list = [{'title': track['name'], 'artist': track['artists'][0]['name'], 'spotify_url': track['external_urls']['spotify']} for track in results['tracks']['items']]
    response_topic = openAiClient.chat.Completion.create(
        model="text-davinci-002",
        prompt=f"Generate the playlist topic: {user_input}",
        max_tokens=50
    )
    description = f"{user_input}"
    return playlist_name, description, song_list

def generate_playlist_general(user_input,spotify):
    # Call OpenAI API to generate playlist name and description
    songs=[]
    for input in user_input:
        type = input['type']
        name = input['name']
        num = input['limit']
        results = spotify.search(q=f'{type}:{name}', limit=num, type='track')
        for track in results['tracks']['items']:
            songs.append({'title': track['name'], 'artist': ", ".join( artist['name'] for artist in track['artists']), 'id':track['id'], 'url':track['external_urls']['spotify']})    
    playlists_name = []
    playlists = Playlist.objects.all()
    for playlist in playlists:
        playlists_name.append(playlist.name)
    
    prompt = (
        f"Generate a Spotify playlist name and description according to the following user input: {user_input}. "
        f"This is the number of the playlists created: {len(Playlist.objects.all())}. "
        f"Here are the names of the playlists: {playlists_name}. Do not use the existed playlsit name"
        f" Here are the songs in this playlist: {songs}. "
        f"First, provide a new playlist name ccording to the user input, if it is a chinese songer, provide english and chinese playlist name like Eason Chan's collection 陳奕迅合集. Look at the existed playlist name and do not duplicate" 
        f"Then, provide the description according to the user input. like 浮誇, 淘汰 and more from this talented singer.'"
        f"Return the answer by just the name and the description seperate by a , not saying like Playlist Name: Bieber Fever"
        f"Here is an example response 'Eason Chan's collection 陳奕迅合集, A playlist featuring the top 10 songs by the artist Eason Chan. Enjoy hits like 愛情轉移(國), 浮誇, 淘汰 and more from this talented singer.'"
    )
    AI_reponse = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":prompt}],
        max_tokens=150
    )
    response_text = AI_reponse.choices[0].message.content.strip()
    response_parts = response_text.split(",", 1)
    playlist_name = response_parts[0]
    description = response_parts[1].strip() if len(response_parts) > 1 else ""
    playlist_url = spotify.user_playlist_create(spotyfy_id,playlist_name,True,True,description)
    playlist = Playlist.objects.create(id=playlist_url['id'] , name=playlist_name, spotify_url=playlist_url['external_urls']['spotify'], description = description)
    song_uri=[]
    for song in songs:
        if not Song.objects.filter(id=song['id']).exists():
            Song.objects.create(playlist=playlist, title=song['title'], artist=song['artist'], spotify_url=song['url'], id=song['id'])
            song_uri.append(f'spotify:track:{song["id"]}')
    spotify.user_playlist_add_tracks(spotyfy_id,playlist_url['id'],song_uri)    

def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    access_token = token_info['access_token']
    spotify = Spotify(auth=access_token)
    
    try:
        spotify.user_playlist_unfollow(spotyfy_id, playlist_id)
        playlist.delete()
        return redirect('index')
    except Exception as e:
        return HttpResponse(f"Failed to delete playlist: {e}")    

def about(request):
    return render(request, 'about.html')
