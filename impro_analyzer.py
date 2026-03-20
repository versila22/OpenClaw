import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time

load_dotenv()

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def get_track_mood_llm(sp, track_name, artist_name):
    """Utilise l'intelligence de PA pour déduire le mood sans l'API Audio Features."""
    # Ici, dans un vrai script, on pourrait faire un appel LLM.
    # Pour ce test, on va simuler une analyse basée sur le nom/artiste
    # ou simplement laisser PA le faire dans la réponse finale.
    return "Analyse sémantique requise"

def analyze_current_impro():
    sp = get_spotify_client()
    playback = sp.current_playback()
    
    if not playback or not playback['item']:
        print("📭 Rien ne joue. Lance 'impro_launcher.py' d'abord.")
        return

    track = playback['item']
    artist = track['artists'][0]['name']
    title = track['name']
    
    print(f"\n--- Analyse Impro Live ---")
    print(f"🎵 Titre  : {title}")
    print(f"🎤 Artiste: {artist}")
    print(f"--------------------------\n")

if __name__ == "__main__":
    analyze_current_impro()
