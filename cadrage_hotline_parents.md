# Cadrage Architecture : Projet "Hotline Darons" (Family IT Helpdesk)

## 1. Framing (Périmètre)
**Objectif :** Remplacer le support informatique asynchrone (les appels paniqués) par un agent de Niveau 1 multimodal, accessible via une interface que les parents maîtrisent déjà.
**Canal :** WhatsApp (via Twilio ou Meta API) ou Telegram (plus simple et gratuit à prototyper).
**Inputs :** Messages vocaux (plaintes/explications) + Photos de l'écran (TV, tablette, PC).
**Scope de support :** IPTV, Spotify, navigation web, applications bancaires.

## 2. Constraints (Sécurité, Cost, Latency)

### 2.1 Sécurité (Critique)
- **Le problème bancaire :** Les parents vont prendre des photos de leur écran avec des IBAN, soldes ou mots de passe visibles.
- **Patch :** 
  - *NeMo Guardrails* ou prompt strict interdisant la lecture/répétition des données personnelles.
  - *Zero-Retention Policy* : Les images sont traitées en mémoire et purgées immédiatement.
  - Interdiction absolue pour le bot de donner des conseils d'investissement ou d'autoriser des virements.

### 2.2 Cost (Tokenomics)
- Le traitement d'images et d'audio en continu peut exploser le budget si on utilise GPT-4o.
- **Patch :** **Gemini 2.5 Flash**. C'est le roi actuel du multimodal low-cost. Il peut ingérer le fichier audio natif (`.ogg` de Telegram/WhatsApp) ET l'image `.jpg` dans le *même* prompt, pour un coût dérisoire et une vitesse fulgurante.

### 2.3 Latency & UX
- Les parents n'ont pas de patience face à un bot qui "charge".
- **Patch :** Accusé de réception immédiat ("Je regarde ton image, donne-moi une seconde..."). 

## 3. The Technical Solution (Architecture)

### Composant A : L'Interface (Telegram Bot)
Le bot écoute les webhooks. Dès qu'un message arrive :
- Si texte -> Traitement normal.
- Si audio (Voice Note) -> Récupération du fichier.
- Si photo -> Récupération du fichier.
*Note : On stocke l'état de la conversation (Mem0 ou un simple Redis) pour lier une photo envoyée juste après un vocal.*

### Composant B : Le Cerveau (Gemini 2.5 Flash Multimodal)
Au lieu de faire `Whisper (Audio -> Texte) + Vision (Image -> Texte) + LLM`, on fait un tir groupé :
```python
prompt = [
    "Tu es l'assistant technique des parents de Jay. Sois patient et rassurant.",
    "Voici ce qu'ils disent :", audio_blob,
    "Voici ce qu'ils voient :", image_blob
]
response = model.generate_content(prompt)
```

### Composant C : RAG (Knowledge Base Spécifique)
Un LLM généraliste ne connaît pas *leur* configuration. Il faut un RAG avec :
- Le modèle exact de leur télécommande.
- Le nom de l'appli IPTV qu'ils utilisent.
- Leurs identifiants génériques (ex: "Le code PIN de la télé est 0000").
*Approche :* Semantic Chunking sur une doc Markdown que tu as rédigée pour eux.

### Composant D : Escalade (Niveau 2)
Si l'intention détectée est "panique", "fraude bancaire", ou "système bloqué" :
- Le bot répond : "Je préviens Jay tout de suite."
- Le bot t'envoie un résumé direct sur ton Telegram avec la photo et le diagnostic pré-calculé.

## Prochaines étapes (Implémentation)
1. Choisir l'interface (Telegram est le plus rapide pour valider le POC).
2. Rédiger le `system_prompt` "Patience & Pédagogie".
3. Créer un mock en Python (Bot Telegram + Gemini).
