import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time

# Chargement des variables d'environnement
load_dotenv()

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def find_playlist(sp, name):
    results = sp.current_user_playlists()
    for item in results['items']:
        if name.lower() in item['name'].lower():
            return item
    return None

def start_impro_session(playlist_name="Impro"):
    sp = get_spotify_client()
    
    # 1. Trouver la playlist
    playlist = find_playlist(sp, playlist_name)
    if not playlist:
        print(f"❌ Playlist '{playlist_name}' non trouvée.")
        return

    print(f"🎵 Playlist trouvée : {playlist['name']}")

    # 2. Vérifier les devices actifs
    devices = sp.devices()['devices']
    active_device = next((d for d in devices if d['is_active']), None)
    
    if not active_device:
        if devices:
            active_device = devices[0]
            print(f"⚠️ Aucun device actif. Tentative de transfert sur : {active_device['name']}")
            sp.transfer_playback(device_id=active_device['id'], force_play=False)
        else:
            print("❌ Aucun device Spotify détecté. Ouvre Spotify sur un appareil.")
            return

    # 3. Lancer la lecture
    print(f"🚀 Lancement de la lecture sur : {active_device['name']}")
    try:
        sp.start_playback(device_id=active_device['id'], context_uri=playlist['uri'])
        sp.shuffle(state=True, device_id=active_device['id'])
        print("✅ Lecture en cours (Mode Aléatoire activé).")
    except Exception as e:
        print(f"❌ Erreur lors du lancement : {e}")

if __name__ == "__main__":
    start_impro_session()
