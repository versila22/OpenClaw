import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import whisper
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import time

# Chargement des variables d'environnement
load_dotenv()

# Configuration
DURATION = 5  # Secondes d'écoute par cycle
SAMPLE_RATE = 16000
MODEL_SIZE = "base" # "base", "small", etc.
FILENAME = "/data/.openclaw/workspace/impro_voice.wav"

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def record_audio():
    print("🎤 Écoute en cours...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    write(FILENAME, SAMPLE_RATE, audio)
    return FILENAME

def process_command(text, sp):
    text = text.lower()
    print(f"💬 Analysé : {text}")
    
    # Logique de déclenchement ultra-simple (Patterns)
    if "musique" in text or "lance" in text:
        print("🚀 Déclenchement Musique !")
        os.system("/data/.openclaw/workspace/spotify_env/bin/python /data/.openclaw/workspace/impro_launcher.py")
        
    elif "stop" in text or "coupe" in text or "fin" in text:
        print("📉 Déclenchement Fondu !")
        os.system("/data/.openclaw/workspace/spotify_env/bin/python /data/.openclaw/workspace/spotify_fadeout.py")

def start_voice_control():
    print("🤖 Initialisation du modèle Whisper...")
    model = whisper.load_model(MODEL_SIZE)
    sp = get_spotify_client()
    
    print("✅ Prêt pour le spectacle. (Ctrl+C pour quitter)")
    
    try:
        while True:
            audio_path = record_audio()
            result = model.transcribe(audio_path, language="fr")
            process_command(result["text"], sp)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n👋 Arrêt du contrôle vocal.")

if __name__ == "__main__":
    start_voice_control()
