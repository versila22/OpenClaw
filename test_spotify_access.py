import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
# Nouvelle Redirect URI générique pour le mode développement
REDIRECT_URI = "https://example.com/callback"

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ SPOTIPY_CLIENT_ID ou SPOTIPY_CLIENT_SECRET manquantes dans l'environnement.")
    exit(1)

def get_spotify_client():
    # Scopes minimaux pour la création de playlist en mode développement
    scope = "playlist-modify-private playlist-modify-public"
    try:
        auth_manager = SpotifyOAuth(client_id=CLIENT_ID, 
                                    client_secret=CLIENT_SECRET, 
                                    redirect_uri=REDIRECT_URI, 
                                    scope=scope, 
                                    open_browser=False)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("✅ Connexion Spotify réussie !")
        user = sp.current_user()
        print(f"Connecté en tant que : {user['display_name']}")
        return sp
    except Exception as e:
        print(f"❌ Erreur de connexion Spotify : {e}")
        return None

if __name__ == "__main__":
    sp_client = get_spotify_client()
    if sp_client:
        # Tentative de lister quelques playlists pour confirmer
        try:
            # Créer une playlist temporaire pour tester les scopes
            user_id = sp_client.current_user()['id']
            test_playlist_name = f"Test Playlist {os.urandom(4).hex()}"
            sp_client.user_playlist_create(user=user_id, name=test_playlist_name, public=False, description="Playlist de test temporaire")
            print(f"✅ Création de la playlist '{test_playlist_name}' confirmée.")
            # On peut la supprimer après si on veut, mais pour le test c'est suffisant
        except Exception as e:
            print(f"❌ Erreur lors de la création de playlist (scopes insuffisants ?) : {e}")
