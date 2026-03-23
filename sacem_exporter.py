import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time
import json
import csv
from datetime import datetime

load_dotenv()

LOG_FILE = "/data/.openclaw/workspace/sacem_log.json"
GOG_ACCOUNT = "jerome.jacq@gmail.com"

def get_spotify_client():
    scope = "user-read-playback-state"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def export_to_sheets():
    if not os.path.exists(LOG_FILE):
        return
    
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
    
    rows = []
    for tid, info in data.items():
        first = datetime.fromtimestamp(info['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
        rows.append([info['title'], info['artist'], int(info['duration_sec']), first])
    
    # Création du fichier temporaire pour gog
    # Note: gog n'a pas de commande directe 'create spreadsheet', on va donc 
    # soit utiliser un ID existant soit suggérer l'upload du CSV sur le Drive.
    
    csv_path = "/data/.openclaw/workspace/sacem_export.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Titre", "Artiste", "Secondes", "Date"])
        writer.writerows(rows)
    
    print(f"✅ Export CSV prêt pour Drive : {csv_path}")

if __name__ == "__main__":
    export_to_sheets()
