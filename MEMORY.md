# MEMORY.md — Mémoire long terme de Jayvis

## À propos de Jerome

- **Profil** : Ingénieur IA senior 44 ans, Angers (secteur Roseraie), en recherche active d'emploi
- **Ne jamais mentionner l'heure** comme frein ou suggestion d'arrêter — Jerome travaille quand il veut, l'heure n'est pas un facteur à commenter
- **Style de travail** : noctambule, sessions longues, aime avancer sans friction

## Projets actifs

### ai-finops ⭐
- Dashboard FinOps pour surveiller les coûts LLM/API (OpenAI, Anthropic, Google, ElevenLabs, Lovable)
- GitHub : https://github.com/versila22/ai-finops
- Frontend : React + Vite + shadcn sur Lovable (https://ai-finops.lovable.app/)
- Backend : FastAPI + SQLAlchemy + SQLite, dockerisé
- HTTPS via Traefik + Let's Encrypt sur https://ai-finops-api.duckdns.org
- Connecteurs réels : OpenAI (usage API), ElevenLabs (subscription API), reste en mode manuel
- ⚠️ Bug en cours : dashboard vide après rebuild Docker (seed/DB path issue)

### lima-app ⭐
- App web gestion Ligue d'Improvisation du Maine-et-Loire (~60 adhérents)
- GitHub backend : https://github.com/versila22/lima-backend
- GitHub frontend : https://github.com/versila22/lima-app
- Stack : FastAPI + PostgreSQL (Railway) + React (Lovable)
- Railway domain : api-production-e15b.up.railway.app
- Login admin : admin@lima-impro.fr / Admin1234!
- Activity logging middleware ajouté (2026-04-06) + endpoints admin analytics
- Intégration Notion API configurée (2026-04-06)

### hotline-darons
- MVP bot Telegram IA multimodal pour support parental
- GitHub : https://github.com/versila22/hotline-darons
- Embedding : gemini-embedding-001
- 38/38 tests passent, escalade validée en live

### fintrack-backend
- Backend FastAPI pour gestion finances perso + micro-entreprise
- GitHub : https://github.com/versila22/fintrack-backend
- JWT auth implémenté (register/login, user-scoped data)
- Stack cible : GoCardless (open banking) + FastAPI + Streamlit + Gemini Flash

### rag-legal-demo
- RAG juridique production-ready (Hybrid Search RRF + Reranking cross-encoder + Gradio)
- GitHub : https://github.com/versila22/rag-legal-demo
- 29/29 tests passent

### DJ Impro (écosystème)
- Scripts Spotify + Flask remote + SACEM logger + Gemini Live partenaire d'impro
- À restructurer en monorepo dj-impro/

### OpenClaw YouTube Uploader
- Pipeline vidéo → YouTube (Gemini script + ElevenLabs + DALL-E + MoviePy)
- À pivoter vers personal branding IA (contenu générique = peu de vues)

## CV & Recherche d'emploi

- CV v2 dans rxresume : titre "Ingénieur Solutions IA & Automation | FinOps LLM | Scrum Master PSM1"
- Couleur primaire CV : #4338CA (indigo)
- LinkedIn mis à jour : titre, résumé, Thales condensé, bénévolat LImA avec co-présidence 2020-2023
- Fichier JSON CV : /data/.openclaw/workspace/jerome-jacq-cv-v2.json

## Infra / Montages

- **VPS → conteneur OpenClaw** : `/docker/openclaw-nmtd/data/` → `/data/` dans le conteneur
  - Donc `/data/.openclaw/workspace/...` côté conteneur = `/docker/openclaw-nmtd/data/.openclaw/workspace/...` côté VPS SSH

## Infra / Clés

- GitHub token : [REDACTED - stored in git config/env] (repo versila22)
- GitHub auth conteneur : credential helper lisant `/data/.openclaw/.gh/hosts.yml`
- Clé Gemini active : [REDACTED - voir config OpenClaw]
- Ancienne clé Gemini révoquée (leaked) : [REDACTED] — NE PAS UTILISER
- Backup GitHub nocturne : cron 3h Europe/Paris, job id: 75062d61-eb76-4346-9bf1-8354b5614169
- Notion API : clé dans ~/.config/notion/api_key (chmod 600), intégration connectée
- DuckDNS : compte via GitHub (versila22), domaine ai-finops-api.duckdns.org → 72.61.196.210
- Docker OpenClaw : /opt/openclaw/docker-compose.yml, .env contient toutes les clés API
- Traefik : /docker/traefik/docker-compose.yml (network_mode: host, Let's Encrypt)

## Automatisations

- **Brief IA matinal** : cron 8h30 Europe/Paris, Gemini Flash, isolated, Telegram (id: 498ebd08)
- **Boucle auto-amélioration** : audit QA + Red Team quotidien sur ai-finops, lima-app, hotline-darons, fintrack — commit auto low/medium, PR pour critical/high
- **Backup GitHub** : cron 3h Europe/Paris

## Préférences

- Ne jamais commenter l'heure pour suggérer d'arrêter de travailler
- Accompagnement qui challenge autant qu'il soutient
- Apprécie les analyses stratégiques directes sans fioriture

## Conventions modèles OpenClaw

- **Orchestration / session principale** → `anthropic/claude-opus-4-6` (défaut config)
- **Subagents code structuré** → `anthropic/claude-sonnet-4-6` (préférence Jerome)
- **Subagents code lourd** → `openai/gpt-5.4`
- **Tâches légères (heartbeat, cron isolé, veille)** → `google/gemini-2.5-flash`
- **Red Team / audit sécurité** → `anthropic/claude-sonnet-4-6` (créatif pour les failles)
- **Gemma 4** → abandonné (nécessite install locale, VPS trop petit)

## Boucles auto-amélioration (actives depuis 2026-04-06)

- **Boucle 1** — Cron `auto-improve-daily` 23h : audit QA + sécu si code a bougé (Gemini Flash)
- **Boucle 2** — HEARTBEAT.md : maintenance mémoire 3j + skill audit hebdo
- **Boucle 3** — Cron `morning-ai-brief` 8h30 : veille IA HN/arxiv/GitHub (Gemini Flash → Telegram)

## Tests par projet

- ai-finops : 36 tests ✅
- lima-app : 95 tests ✅
- fintrack-backend : 15 tests (dont IDOR) ✅
- hotline-darons : 30+ tests ✅

## Leçons apprises

- passlib + bcrypt cassé sous Python 3.13 → utiliser pbkdf2_sha256 comme scheme primaire
- aiosqlite + async SQLAlchemy tests → désactiver middlewares qui écrivent en DB async (sinon database locked)
- Subagents GPT-5.4 timeout parfois sur le push git → vérifier et finir manuellement
