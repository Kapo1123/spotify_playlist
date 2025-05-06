# backend/playlists/views.py
from django.shortcuts import render, redirect,get_object_or_404

from .models import Playlist, Song, Vote,Episode
from django.http import HttpResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
import config
import json
openAiClient = OpenAI(
    api_key = config.OPENAI_API_KEY,
    organization = config.OPENAI_ORGID
)
sp_oauth = SpotifyOAuth(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public user-read-email"
    )
def login(request):
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)
def index(request):
    token_info = request.session.get('token_info', None)
    if not token_info:
        return redirect('login')
    print("Current user:", token_info)
    spotify = Spotify(auth=token_info['access_token'])
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type != 'using_ai':
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
            generate_playlist_general(user_inputs,spotify)
        else:
            user_inputs = {
                'description': request.POST.get('user_input'),
                'num_songs': int(request.POST.get('num_songs'))
            }
            generate_playlist_withAI(user_inputs,spotify)
        return redirect('index')

    playlists = Playlist.objects.all()
    return render(request, 'index.html', {'playlists': playlists})
def spotify_callback(request):
    code = request.GET.get('code')
    token_info = sp_oauth.get_access_token(code)
    
    if token_info:
        request.session['token_info'] = token_info
        return redirect('index')
    else:
        return HttpResponse('Authentication failed')
def generate_playlist_withAI(user_input,spotify):
    # Call OpenAI API to generate playlist name and description
    user_description = user_input['description']
    num_songs = user_input['num_songs']
    current_user = spotify.current_user()
    
    # Generate prompt for OpenAI API to create multiple queries
    prompt = (
    f"Based on the following user description, generate a Spotify playlist name, a description, and multiple Spotify search queries to find relevant tracks.\n"
    f"Please return the result in the following JSON format:\n"
    f"{{\n"
    f"    \"name\": \"<playlist_name>\",\n"
    f"    \"description\": \"<playlist_description>\",\n"
    f"    \"queries\": [\n"
    f"        {{ \"query\": \"<query_1>\", \"limit\": <limit_1>, \"type\": \"<type_1>\" }},\n"
    f"        {{ \"query\": \"<query_2>\", \"limit\": <limit_2>, \"type\": \"<type_2>\" }}\n"
    f"    ]\n"
    f"}}\n"
    f"The list in queries should contain multiple queries up to {num_songs} to search for tracks on Spotify. The query should be in the format of Spotify search query.\n"
    f"Total songs should equal to {num_songs}\n"
    f"Don't specify the language in query, the spotify doesn't work well with it. We are default in US area.\n"  
    f"All the queries should be in English.\n"
    f"Please provide the playlist name and description in all different languages in user input.\n"  
    f"If the user wants a type of playlist, like before sleep playlist, provide the indivual track name as one of the queries or the artist name as  one of the queries. instead of doing genre:sleep.\n" 
    f" If a track is provided, the limit should be 1, we don't want depulicate songs in the playlist.\n"
    f"If specify players provided with \"like\", add other same styles artists in the next query.\n"
    f"Do not do 'genre:driving language:zh' as the spotify doesn't work well with it.\n"
    f"Examples of Spotify queries:\n"
    f"1. If the user description is 'popular pop songs', the query should be \"queries\": [\n"
    f"        {{ \"query\": \"artist:Adele\", \"limit\": <limit_1>, \"type\": \"track\" }},\n"
    f"        {{ \"query\": \"artist:Ed Sheeran\", \"limit\": <limit_2>, \"type\": \"track\" }},\n"
    f"        {{ \"query\": \"artist:Sam Smith\", \"limit\": <limit_2>, \"type\": \"track\" }},\n"
    f"    ]\n"
    f"2. If the user description is 'classical music by Beethoven', the query should be '\"query\"=\"artist:Beethoven genre:classical\", \"limit\":20, \"type\":\"track\"'.\n"
    f"3. If the user description is 'workout songs with Cantonese and English song mix', the queries should be '\"query\"=\"genre:workout language:zh\", \"limit\":20, \"type\":\"track\"' and '\"query\"=\"genre:workout language:en\", \"limit\":20, \"type\":\"track\"'.\n"
    f"4. If the user description is 'albums by Taylor Swift', the query should be '\"query\"=\"artist:Taylor Swift\", \"limit\":20, \"type\":\"album\"'.\n"
    f"5. If the user description is 'podcasts about technology', the query should be '\"query\"=\"genre:technology\", \"limit\":20, \"type\":\"show\"'.\n"
    f"Return the JSON object only, do not include any other text."
    f"Finsih the prompt please do not stop in the middle of the sentence."
)
    message=(f"Description: {user_description}\n"
        f"User total wanted songs: {num_songs}\n")



    AI_reponse = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content":prompt},{"role": "user", "content":message}],
        max_tokens=600
    )

    response_text = AI_reponse.choices[0].message.content.strip('```json\n').strip('```')
    response_data = json.loads(response_text)
    playlist_name = response_data['name']
    description = response_data[ 'description']
    playlist_url = spotify.user_playlist_create(current_user['id'],playlist_name,True,True,description)
    playlist = Playlist.objects.create(id=playlist_url['id'] , name=playlist_name, spotify_url=playlist_url['external_urls']['spotify'], description = description)
    song_uri=[]
    episode_uri=[]

    # Call Spotify API to get songs
    queries = response_data['queries']
    for query in queries:
        q = query['query']
        limit = query['limit']
        type_ = query['type']

        # Search Spotify using the query parameters
        results = spotify.search(q=q, limit=limit, type=type_)

        # Extract tracks or episodes and add to the appropriate URI list
        if type_ == 'track':
            for item in results['tracks']['items']:
                song_uri.append(f"spotify:track:{item['id']}")
                if not Song.objects.filter(id=item['id']).exists():
                    Song.objects.create(
                        playlist=playlist,
                        title=item['name'],
                        artist=", ".join(artist['name'] for artist in item['artists']),
                        spotify_url=item['external_urls']['spotify'],
                        id=item['id']
                    )
        elif type_ == 'episode':
            for item in results['episodes']['items']:
                episode_uri.append(f"spotify:episode:{item['id']}")
                if not Song.objects.filter(id=item['id']).exists():
                    Song.objects.create(
                        playlist=playlist,
                        title=item['name'],
                        artist=", ".join(artist['name'] for artist in item['show']['publisher']),
                        spotify_url=item['external_urls']['spotify'],
                        id=item['id']
                    )

    # Add the songs and episodes to the Spotify playlist
    if song_uri:
        spotify.user_playlist_add_tracks(current_user['id'], playlist_url['id'], song_uri)
    if episode_uri:
        spotify.user_playlist_add_tracks(current_user['id'], playlist_url['id'], episode_uri)
    

def generate_playlist_general(user_input,spotify):
    # Call OpenAI API to generate playlist name and description
    songs=[]
    episodes=[]
    current_user = spotify.current_user()
    for input in user_input:
        type = input['type']
        name = input['name']
        num = input['limit']
        access= 'tracks'
        if type == 'episode':
            results = spotify.search(q=f'{type}:{name}', limit=num, type='episode')
            access='episodes'
        else:
            results = spotify.search(q=f'{type}:{name}', limit=num, type='track')
        for track in results[access]['items']:
            if access == 'tracks':
                songs.append({'title': track['name'], 'artist': ", ".join( artist['name'] for artist in track['artists']), 'id':track['id'], 'url':track['external_urls']['spotify']})
            elif  access=='episodes':
                episodes.append({'title': track['name'], 'performer':name, 'id':track['id'], 'url':track['external_urls']['spotify'], 'release_date':track['release_date']})

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
        f"Return the answer with the name and the description seperate by a * "
        f"Here is an example response 'playlist_name: Eason Chan's collection 陳奕迅合集 * playlist_description: A playlist featuring the top 10 songs by the artist Eason Chan. Enjoy hits like 愛情轉移(國), 浮誇, 淘汰 and more from this talented singer.'"
    )
    AI_reponse = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":prompt}],
        max_tokens=150
    )
    response_text = AI_reponse.choices[0].message.content.strip()
    response_parts = response_text.split("*", 1)
    playlist_name = response_parts[0][response_parts[0].find(':')+1:]
    description = response_parts[1][response_parts[1].find(':')+1:].strip() if len(response_parts) > 1 else ""
    playlist_url = spotify.user_playlist_create(current_user["id"],playlist_name,True,True,description)
    playlist = Playlist.objects.create(id=playlist_url['id'] , name=playlist_name, spotify_url=playlist_url['external_urls']['spotify'], description = description)
    song_uri=[]
    episode_uri=[]
    for song in songs:
        if not Song.objects.filter(id=song['id']).exists():
            Song.objects.create(playlist=playlist, title=song['title'], artist=song['artist'], spotify_url=song['url'], id=song['id'])
        song_uri.append(f'spotify:track:{song["id"]}')
    for episode in episodes:
        if not Episode.objects.filter(id=episode['id']).exists():
            Episode.objects.create(playlist=playlist, title=episode['title'], performer=episode['performer'], spotify_url=episode['url'], id=episode['id'], release_date=episode['release_date'])
        episode_uri.append(f'spotify:track:{episode["id"]}')
    if song_uri:
        spotify.user_playlist_add_tracks(current_user["id"],playlist_url['id'],song_uri)
    if episode_uri:
        spotify.user_playlist_add_tracks(current_user["id"],playlist_url['id'],episode_uri)

def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    token_info = request.session.get('token_info', None)
    
    if not token_info:
        return redirect('login')
    
    access_token = token_info['access_token']
    spotify = Spotify(auth=access_token)
    current_user = spotify.current_user()
    
    try:
        spotify.user_playlist_unfollow(current_user["id"], playlist_id)
        playlist.delete()
        return redirect('index')
    except Exception as e:
        return HttpResponse(f"Failed to delete playlist: {e}")    

def about(request):
    return render(request, 'about.html')
