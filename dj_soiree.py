import os
import sys
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private"
    try:
        return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))
    except Exception as e:
        print(f"❌ Erreur d'authentification Spotify: {e}")
        sys.exit(1)

def mode_assistant(sp):
    print("\n🎧 --- MODE AIDE À LA PROGRAMMATION --- 🎧")
    print("L'IA analyse le titre en cours et te suggère les prochains morceaux à jouer.")
    print("Appuie sur Ctrl+C pour quitter.\n")
    
    last_track_id = None
    
    try:
        while True:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                track_id = track['id']
                
                if track_id != last_track_id:
                    artist = track['artists'][0]['name']
                    title = track['name']
                    print(f"\n🎵 En cours d'écoute : {title} - {artist}")
                    print("🤖 Analyse en cours (Simulation IA)...")
                    # Ici l'IA ferait une recommandation basée sur le mood/genre
                    print(f"💡 Suggestion 1: Un titre dans la même vibe que {artist}.")
                    print(f"💡 Suggestion 2: Un classique pour relancer l'énergie.")
                    
                    last_track_id = track_id
            else:
                print("📭 Rien ne joue actuellement sur Spotify. En attente...")
                time.sleep(5)
                
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nFin du mode Assistant. Bonne soirée ! 🕺")

def mode_autonome(sp):
    print("\n🤖 --- MODE DJ AUTONOME --- 🤖")
    print("L'IA prend le contrôle des platines. Elle enchaîne les titres automatiquement.")
    print("Appuie sur Ctrl+C pour reprendre le contrôle.\n")
    
    last_track_id = None
    
    try:
        while True:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                track_id = track['id']
                progress_ms = playback.get('progress_ms', 0)
                duration_ms = track.get('duration_ms', 100000)
                is_playing = playback.get('is_playing', False)
                
                if track_id != last_track_id:
                    artist = track['artists'][0]['name']
                    title = track['name']
                    print(f"\n🎵 Le DJ IA joue : {title} - {artist}")
                    last_track_id = track_id
                
                # Vérifier si on arrive à la fin du morceau (ex: reste 10 secondes)
                if is_playing and (duration_ms - progress_ms) < 10000:
                    print("⚠️ Fin du titre imminente. Le DJ IA prépare la transition...")
                    # Ici l'IA ajouterait le titre suivant à la file d'attente (sp.add_to_queue)
                    # Pour l'instant, on laisse Spotify enchaîner ou on ajoute une logique de file.
                    time.sleep(10) # Attendre que la transition se fasse
                    
            else:
                print("📭 Aucun titre en cours. Le DJ IA cherche l'inspiration...")
                # Ici l'IA pourrait lancer une playlist par défaut
                time.sleep(5)
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nFin du mode DJ Autonome. Reprise du contrôle manuel. 🎧")

def main():
    print("========================================")
    print("🎉       DJ SOIRÉE APP - V1.0         🎉")
    print("========================================\n")
    print("Choisis le mode de fonctionnement :")
    print("1. 🎧 Aide à la programmation (L'IA écoute et suggère)")
    print("2. 🤖 DJ Autonome (L'IA gère les transitions et la playlist)")
    print("3. Quitter")
    
    try:
        choice = input("\n👉 Ton choix (1/2/3) : ").strip()
    except KeyboardInterrupt:
        print("\nA plus tard !")
        sys.exit(0)
        
    if choice == '3':
        print("A plus tard !")
        sys.exit(0)
        
    sp = get_spotify_client()
    
    if choice == '1':
        mode_assistant(sp)
    elif choice == '2':
        mode_autonome(sp)
    else:
        print("❌ Choix invalide.")

if __name__ == "__main__":
    main()
