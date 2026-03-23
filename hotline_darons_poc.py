import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# In-memory store pour lier une photo à un message vocal envoyé juste après
# Format: { user_id: {"photo_bytes": bytes, "timestamp": datetime} }
user_context = {}
CONTEXT_EXPIRATION_MINUTES = 5

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation Gemini
if GEMINI_API_KEY:
    ai_client = genai.Client()
else:
    logger.error("GEMINI_API_KEY manquante.")

SYSTEM_PROMPT = """Tu es l'assistant technique de niveau 1 pour mes parents.
Règles strictes :
1. Sois extrêmement patient, rassurant et utilise des mots simples (pas de jargon technique).
2. Si tu vois une information bancaire (IBAN, solde, carte) ou un mot de passe sur l'image, signale-le immédiatement et refuse de traiter l'image pour des raisons de sécurité.
3. Si le problème semble critique (panique, piratage, système bloqué), dis que tu vas transférer le dossier à Jay.
4. Réponds toujours de manière concise, étape par étape.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Coucou ! Je suis l'assistant de Jay. Si tu as un souci avec la télé, l'ordinateur ou le téléphone, "
        "envoie-moi une note vocale pour m'expliquer, et une photo de l'écran si tu peux !"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # On stocke la photo temporairement en RAM (Zero-Retention sur disque)
    user_context[user_id] = {
        "photo_bytes": photo_bytes,
        "timestamp": datetime.now()
    }
    
    await update.message.reply_text("J'ai bien reçu la photo. Dis-moi ce qui coince (par texte ou par note vocale) !")

async def handle_voice_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    # Message de patientement (Latence UX)
    status_msg = await update.message.reply_text("Je regarde ça, donne-moi une seconde...")
    
    contents = [types.Part.from_text(text=SYSTEM_PROMPT)]
    
    # Vérifier si on a une photo récente en contexte
    context_data = user_context.get(user_id)
    if context_data:
        if datetime.now() - context_data["timestamp"] < timedelta(minutes=CONTEXT_EXPIRATION_MINUTES):
            contents.append(types.Part.from_bytes(
                data=bytes(context_data["photo_bytes"]),
                mime_type="image/jpeg"
            ))
        # Purge de la photo après utilisation
        del user_context[user_id]

    # Traitement de l'entrée utilisateur
    if update.message.voice:
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        contents.append(types.Part.from_bytes(
            data=bytes(voice_bytes),
            mime_type="audio/ogg" # Format natif Telegram
        ))
    elif update.message.text:
        contents.append(types.Part.from_text(text=update.message.text))

    try:
        # Appel Gemini 2.5 Flash Multimodal
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        answer = response.text
        
        # Escalade (Niveau 2) - Détection par mot-clé basique pour le POC
        if any(word in answer.lower() for word in ["transférer à jay", "dossier à jay", "urgence"]):
            # Ici on pourrait envoyer un message via context.bot.send_message(JAY_ID, "Alerte parents...")
            pass
            
        await status_msg.edit_text(answer)
        
    except Exception as e:
        logger.error(f"Erreur IA : {e}")
        await status_msg.edit_text("Oups, j'ai eu un petit bug en réfléchissant. Tu peux répéter ?")

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.error("La variable d'environnement TELEGRAM_BOT_TOKEN est requise.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE | filters.TEXT & ~filters.COMMAND, handle_voice_or_text))

    print("🤖 Bot Hotline Darons démarré. En attente de messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
