import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

def test_spotify_connection():
    # Définition du scope pour lire l'état de lecture et les devices
    scope = "user-read-playback-state user-modify-playback-state"
    
    auth_manager = SpotifyOAuth(scope=scope, open_browser=False)
    auth_url = auth_manager.get_authorize_url()
    print(f"URL_AUTH_START\n{auth_url}\nURL_AUTH_END")
    
    # On attendra que l'utilisateur fournisse l'URL de retour
    response_url = input("Colle l'URL complète de redirection ici : ")
    code = auth_manager.parse_response_code(response_url)
    token_info = auth_manager.get_access_token(code)
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.current_user()
    print(f"✅ Connecté en tant que : {user['display_name']}")
    
    devices = sp.devices()
    print("\n📱 Appareils détectés :")
    for device in devices['devices']:
        status = "🔥 ACTIF" if device['is_active'] else "💤 Inactif"
        print(f"   - {device['name']} ({device['type']}) - {status}")

if __name__ == "__main__":
    test_spotify_connection()
