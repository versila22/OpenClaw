import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import random
import os

CACHE_PATH = '/data/.openclaw/workspace/.cache'
LIBRARY_PATH = '/data/.openclaw/workspace/impro_music_library.json'

def get_sp():
    auth_manager = SpotifyOAuth(
        scope='playlist-modify-public playlist-modify-private playlist-read-private user-read-playback-state',
        cache_path=CACHE_PATH,
        open_browser=False
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def create_show_playlist(show_name, requested_categories, tracks_per_cat=3):
    sp = get_sp()
    with open(LIBRARY_PATH, 'r') as f:
        lib = json.load(f)
    
    final_tracks = []
    
    # 1. Ajout des Protocoles (Entrée MC, Joueurs, Fin)
    for proto in ['mc_entry', 'player_entry', 'show_end']:
        track_query = random.choice(lib['protocols'][proto])
        final_tracks.append(track_query)
    
    # 2. Ajout des Catégories demandées
    for cat in requested_categories:
        cat_key = cat.lower().replace(' ', '_')
        if cat_key in lib['categories']:
            pool = lib['categories'][cat_key]
            # On prend N titres aléatoires dans la catégorie
            selected = random.sample(pool, min(tracks_per_cat, len(pool)))
            final_tracks.extend(selected)
    
    # 3. Résolution des URIs Spotify
    uris = []
    print(f"--- Résolution des titres pour {show_name} ---")
    for track_name in final_tracks:
        results = sp.search(q=track_name, limit=1, type='track')
        items = results.get('tracks', {}).get('items', [])
        if items:
            uris.append(items[0]['uri'])
            print(f"✅ Trouvé : {track_name}")
        else:
            print(f"❌ Non trouvé : {track_name}")
    
    # 4. Création de la Playlist
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, f"SPECTACLE : {show_name}", public=False)
    sp.playlist_add_items(playlist['id'], uris)
    
    print(f"\n🚀 Playlist '{playlist['name']}' créée avec succès (ID: {playlist['id']})")
    return playlist['external_urls']['spotify']

if __name__ == "__main__":
    # Exemple d'usage via CLI (sera piloté par PA)
    import sys
    if len(sys.argv) > 2:
        create_show_playlist(sys.argv[1], sys.argv[2:])
