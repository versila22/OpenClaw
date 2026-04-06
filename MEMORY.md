# MEMORY.md — Mémoire long terme de Jayvis

## À propos de Jerome

- **Profil** : Ingénieur IA senior 44 ans, Angers (secteur Roseraie), en recherche active d'emploi
- **Ne jamais mentionner l'heure** comme frein ou suggestion d'arrêter — Jerome travaille quand il veut, l'heure n'est pas un facteur à commenter
- **Style de travail** : noctambule, sessions longues, aime avancer sans friction

## Projets actifs

### hotline-darons
- MVP bot Telegram IA multimodal pour support parental
- GitHub : https://github.com/versila22/hotline-darons
- Bot Telegram : 8436824281:AAEOpcyv0WxyPXr6Gds3e3tsb3AS59Jqepc
- Clé Gemini active : [REDACTED - stored in OpenClaw config/env]
- Embedding : gemini-embedding-001 (text-embedding-004 non dispo avec cette clé)
- 38/38 tests passent, escalade validée en live

### rag-legal-demo
- RAG juridique production-ready (Hybrid Search RRF + Reranking cross-encoder + Gradio)
- GitHub : https://github.com/versila22/rag-legal-demo
- 3 contrats fictifs inclus (prestation IA, bail commercial, CDI ingénieur)
- FastAPI + Gradio démo entretien
- 29/29 tests passent

### DJ Impro (écosystème)
- Scripts Spotify + Flask remote + SACEM logger + Gemini Live partenaire d'impro
- À restructurer en monorepo dj-impro/

### OpenClaw YouTube Uploader
- Pipeline complet vidéo → YouTube (Gemini script + ElevenLabs + DALL-E + MoviePy)
- GitHub : https://github.com/versila22/OpenClaw
- Analytics feedback loop en place
- À pivoter vers personal branding IA (contenu générique = peu de vues)

### FinTrack (à créer)
- Appli gestion finances perso + micro-entreprise
- Stack : GoCardless (open banking) + FastAPI + Streamlit + Gemini Flash + Google Calendar API
- Banques : Boursorama ✅, La Poste ✅, Fortuneo ✅ (GoCardless compatible)
- Poker/crypto : V2 (APIs propriétaires)
- Budget API surveillance : 100€/mois total, seuils réglables dans l'UI
- 2 onglets : Perso | Micro-Entreprise

## CV & Recherche d'emploi

- CV v2 dans rxresume : titre "Ingénieur Solutions IA & Automation | FinOps LLM | Scrum Master PSM1"
- Couleur primaire CV : #4338CA (indigo)
- LinkedIn mis à jour : titre, résumé, Thales condensé, bénévolat LImA avec co-présidence 2020-2023
- Fichier JSON CV : /data/.openclaw/workspace/jerome-jacq-cv-v2.json

## Infra / Clés

- GitHub token : [REDACTED - stored in git config/env] (repo versila22)
- Clé Gemini active : [REDACTED - voir config OpenClaw]
- Ancienne clé Gemini révoquée (leaked) : [REDACTED] — NE PAS UTILISER
- Backup GitHub nocturne : cron 3h Europe/Paris, job id: 75062d61-eb76-4346-9bf1-8354b5614169
- mcporter.json clé Google mise à jour avec la nouvelle clé Gemini

## Préférences

- Ne jamais commenter l'heure pour suggérer d'arrêter de travailler
- Accompagnement qui challenge autant qu'il soutient
- Apprécie les analyses stratégiques directes sans fioriture

## Conventions modèles OpenClaw

- **Orchestration / session principale** → `anthropic/claude-opus-4-6` (défaut config)
- **Subagents code** → toujours spawner avec `model: "openai/gpt-5.4"`
- **Tâches légères (heartbeat, cron isolé, lecture/écriture)** → `google/gemini-2.5-flash`
- **Gemma 4** → abandonné (nécessite install locale, VPS trop petit) — Gemini suffit
