import os
import sys
import json
import subprocess
import argparse
import google.generativeai as genai

def setup_env():
    """Vérifie la présence de la clé API Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erreur: La variable d'environnement GEMINI_API_KEY n'est pas définie.")
        print("Exportez-la via: export GEMINI_API_KEY='votre_cle'")
        sys.exit(1)
    genai.configure(api_key=api_key)

def run_command(command, desc="Exécution"):
    """Exécute une commande shell avec gestion d'erreur basique."""
    print(f"-> {desc}...")
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de: {desc}")
        print(f"Commande: {command}")
        sys.exit(1)

def transcribe_full_video(video_path):
    """Génère le transcript complet pour l'analyse sémantique."""
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = "temp_processing"
    os.makedirs(out_dir, exist_ok=True)
    
    txt_path = os.path.join(out_dir, f"{base_name}.txt")
    
    # Si le transcript existe déjà (cache), on le réutilise pour gagner du temps
    if os.path.exists(txt_path):
        print("-> Transcript complet trouvé en cache.")
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()

    run_command(f"whisper \"{video_path}\" --model base --output_format txt --output_dir \"{out_dir}\"", "Transcription de la vidéo source (Whisper)")
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_viral_segments(transcript):
    """Envoie le transcript à Gemini pour extraire les Hooks."""
    print("-> Analyse sémantique par Gemini 2.5 Flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Tu es un expert en viralité YouTube Shorts et TikTok.
    Voici le transcript d'une vidéo. Ta mission est d'identifier les 2 meilleurs segments (entre 30 et 60 secondes) 
    qui ont un fort potentiel viral (une accroche forte, du rythme, et une conclusion claire).
    
    Format de sortie exigé (STRICTEMENT JSON, aucun autre texte) :
    [
      {{
        "titre_seo": "Titre accrocheur",
        "start_time": "00:01:15",
        "end_time": "00:02:00",
        "explication": "Pourquoi ce passage retient l'attention."
      }}
    ]
    
    Transcript :
    {transcript}
    """
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Nettoyage basique des balises markdown si Gemini en ajoute
    if raw_text.startswith("```json"):
        raw_text = raw_text.replace("```json\n", "").replace("```", "")
        
    try:
        segments = json.loads(raw_text)
        return segments
    except json.JSONDecodeError:
        print("Erreur: Gemini n'a pas retourné un JSON valide.")
        print("Output brut:", raw_text)
        sys.exit(1)

def process_short(video_path, segment, index):
    """Découpe, génère les sous-titres sync, et incruste."""
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = "export_shorts"
    temp_dir = "temp_processing"
    os.makedirs(out_dir, exist_ok=True)
    
    start = segment['start_time']
    end = segment['end_time']
    safe_title = "".join(x for x in segment['titre_seo'] if x.isalnum() or x in " -_").replace(" ", "_")
    
    print(f"\n--- Traitement du Short {index}: {segment['titre_seo']} ---")
    print(f"-> Extraction temporelle: {start} à {end}")
    
    # 1. Découpage et Crop 9:16 (sans sous-titres)
    # Explication mathématique du crop : ih*9/16 (largeur calculée pour ratio 9:16), ih (hauteur max conservée).
    # Cela centre automatiquement l'image sur le sujet principal (généralement au centre).
    cropped_mp4 = os.path.join(temp_dir, f"short_{index}_cropped.mp4")
    crop_filter = "crop=ih*9/16:ih"
    cmd_crop = f"ffmpeg -y -i \"{video_path}\" -ss {start} -to {end} -vf \"{crop_filter}\" -c:a aac -b:a 192k \"{cropped_mp4}\""
    run_command(cmd_crop, f"Découpage et recadrage 9:16")

    # 2. Re-Transcription du Short pour un SRT parfaitement synchronisé
    # Astuce d'architecte : Calculer les offsets SRT est un enfer source de bugs. 
    # Repasser Whisper sur un extrait de 60s prend 2 secondes et garantit un sync parfait.
    run_command(f"whisper \"{cropped_mp4}\" --model base --output_format srt --output_dir \"{temp_dir}\"", "Génération des sous-titres synchronisés")
    srt_file = os.path.join(temp_dir, f"short_{index}_cropped.srt")

    # 3. Incrustation (Burn-in) des sous-titres
    final_mp4 = os.path.join(out_dir, f"{base_name}_{safe_title}.mp4")
    
    # Formatage du filtre subtitles pour FFmpeg (échappement des chemins sous Windows/Linux)
    # On ajoute un style basique : Police de taille 24 (relative), centrée, bordure noire.
    srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")
    style = "Fontname=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=20"
    cmd_burn = f"ffmpeg -y -i \"{cropped_mp4}\" -vf \"subtitles='{srt_escaped}':force_style='{style}'\" -c:a copy \"{final_mp4}\""
    run_command(cmd_burn, "Incrustation dynamique des sous-titres (Burn-in)")
    
    print(f"-> Terminé ! Fichier généré : {final_mp4}")

def main():
    parser = argparse.ArgumentParser(description="Automatisation d'extraction de YouTube Shorts via OpenClaw.")
    parser.add_argument("video", help="Chemin vers la vidéo source 16:9")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Erreur: Le fichier {args.video} n'existe pas.")
        sys.exit(1)

    setup_env()
    
    print("=== Démarrage du Pipeline Shorts Extractor ===")
    
    transcript = transcribe_full_video(args.video)
    segments = get_viral_segments(transcript)
    
    print(f"\nGemini a identifié {len(segments)} segments viables.")
    
    for i, seg in enumerate(segments, 1):
        process_short(args.video, seg, i)
        
    print("\n=== Pipeline terminé avec succès ===")

if __name__ == "__main__":
    main()