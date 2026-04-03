# SAFE_GIT.md

Règles simples pour éviter une 3e fuite.

## Ne jamais committer
- `.env`, `.env.*` (sauf `.env.example`)
- tokens GitHub / API keys
- `credentials.json`
- `mcporter.json`
- clés privées (`*.pem`, `*.key`)
- bases locales (`*.db`, `*.sqlite*`)

## Workflow minimal avant commit
1. `git status`
2. relire les fichiers stagés : `git diff --cached`
3. commit normal (les hooks bloquent les secrets évidents)

## Workflow minimal avant push
1. `git status`
2. `git diff origin/main...HEAD` (ou branche cible)
3. push normal (le hook pre-push rescane les fichiers trackés)

## Auth GitHub
- préférer `gh auth login`
- ne jamais mettre un token dans l'URL du remote
- remote attendu : `https://github.com/<owner>/<repo>.git`

## En cas de doute
- si une valeur ressemble à un secret, la sortir du repo
- mettre un placeholder dans les fichiers suivis
- garder le vrai secret dans l'environnement local
