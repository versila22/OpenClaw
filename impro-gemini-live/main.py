import asyncio
import os
import sys
import pyaudio
from google import genai
from google.genai import types

# --- Configuration Audio (Standard RTC) ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # 16kHz est optimal pour les modèles vocaux
CHUNK = 512

# --- Le "Cerveau" de l'Impro ---
SYSTEM_INSTRUCTION = """
Tu es mon partenaire de théâtre d'improvisation. 
Règle 1 : Applique toujours le principe du "Oui, et..." (accepte mon offre et construis par-dessus).
Règle 2 : Tu dois incarner DEUX personnages distincts dans cette scène.
- Personnage A : "Le Vieux", cynique, parle lentement, soupire souvent, utilise un vocabulaire soutenu.
- Personnage B : "Le Jeune", surexcité, parle très vite, pose plein de questions, utilise un langage familier.
Règle 3 : Exagère énormément tes intonations, ton débit de parole et tes tics de langage. C'est critique car tu n'as qu'une seule voix de synthèse. On doit comprendre immédiatement qui parle juste à l'attitude.
"""

async def audio_loop():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Erreur] Variable GEMINI_API_KEY manquante. Utilise: export GEMINI_API_KEY='ta_cle'")
        sys.exit(1)

    # Initialisation du client (Google GenAI Live SDK)
    client = genai.Client()
    
    # Setup PyAudio pour le flux I/O
    p = pyaudio.PyAudio()
    
    print("[Système] Initialisation des flux audio...")
    mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    speaker_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

    print("[Système] Connexion à Gemini Live API en cours...")
    
    # Architecture de la session Live (full duplex)
    config = types.LiveConnectConfig(
        system_instruction=types.Content(parts=[types.Part.from_text(text=SYSTEM_INSTRUCTION)]),
        response_modalities=[types.LiveModality.AUDIO]
    )

    try:
        async with client.aio.live.connect(model="gemini-2.5-flash", config=config) as session:
            print("[Système] Connecté ! C'est à toi de jouer. (Ctrl+C pour quitter)")
            
            # Tâche 1 : Capturer le micro et l'envoyer au modèle
            async def send_mic_audio():
                while True:
                    data = mic_stream.read(CHUNK, exception_on_overflow=False)
                    await session.send(types.LiveClientRealtimeInput(
                        media_chunks=[types.Blob(data=data, mime_type="audio/pcm;rate=16000")]
                    ))
                    await asyncio.sleep(0.001)

            # Tâche 2 : Recevoir l'audio du modèle et le jouer
            async def receive_and_play_audio():
                async for message in session.receive():
                    if isinstance(message, types.LiveServerModelTurn):
                        for part in message.parts:
                            if part.inline_data:
                                speaker_stream.write(part.inline_data.data)

            # Exécution concurrente des deux flux
            await asyncio.gather(send_mic_audio(), receive_and_play_audio())

    except KeyboardInterrupt:
        print("\n[Système] Fin de l'impro.")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        speaker_stream.stop_stream()
        speaker_stream.close()
        p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(audio_loop())
    except KeyboardInterrupt:
        pass
