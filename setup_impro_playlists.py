import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time

load_dotenv()

def get_spotify_client():
    # Suppression du cache pour forcer un nouveau jeton avec les autorisations fraîches
    if os.path.exists(".cache"):
        os.remove(".cache")
        
    scope = "playlist-modify-public playlist-modify-private playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def create_or_get_playlist(sp, name):
    user_id = sp.current_user()['id']
    playlists = sp.current_user_playlists()
    for pl in playlists['items']:
        if pl['name'] == name:
            print(f"✅ Playlist trouvée : {name}")
            return pl['id']
    
    print(f"🆕 Création de la playlist : {name}")
    new_pl = sp.user_playlist_create(user_id, name, public=False)
    return new_pl['id']

def add_tracks_by_queries(sp, playlist_id, queries):
    track_ids = []
    for q in queries:
        results = sp.search(q=q, type='track', limit=1)
        if results['tracks']['items']:
            track_ids.append(results['tracks']['items'][0]['id'])
            print(f"   + Ajouté : {results['tracks']['items'][0]['name']} - {results['tracks']['items'][0]['artists'][0]['name']}")
    
    if track_ids:
        sp.playlist_add_items(playlist_id, track_ids)

def setup_impro_playlists():
    sp = get_spotify_client()
    
    # 1. Cabaret +16 ans
    cabaret_queries = [
        "Miley Cyrus Flowers", "Sabrina Carpenter Espresso", "Billie Eilish Birds of a Feather",
        "Sophie Ellis-Bextor Murder on the Dancefloor", "Liza Minnelli Mein Herr",
        "Nancy Sinatra These Boots Are Made for Walkin'", "Portishead Glory Box",
        "The White Stripes Seven Nation Army", "Lady Gaga Abracadabra", "Amy Winehouse Back to Black"
    ]
    pl_cabaret = create_or_get_playlist(sp, "Impro - Cabaret +16")
    add_tracks_by_queries(sp, pl_cabaret, cabaret_queries)

    # 2. Match +9 ans
    match_queries = [
        "Rosé Bruno Mars APT", "Benson Boone Beautiful Things", "Queen Don't Stop Me Now",
        "ABBA Dancing Queen", "Daft Punk Get Lucky", "Taylor Swift Fortnight",
        "Natasha Bedingfield Unwritten", "Pharrell Williams Happy",
        "Justin Timberlake Can't Stop the Feeling", "Earth Wind & Fire September"
    ]
    pl_match = create_or_get_playlist(sp, "Impro - Match +9")
    add_tracks_by_queries(sp, pl_match, match_queries)

    print("\n🚀 Playlists configurées avec succès.")

if __name__ == "__main__":
    setup_impro_playlists()
