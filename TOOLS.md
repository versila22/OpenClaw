# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## Workspace Tool Access

### GitHub
- `gh` installé sur le VPS principal
- Auth GitHub CLI configurée et fonctionnelle (`gh auth status` OK)
- Règle: ne jamais utiliser de PAT dans les URLs remote

### Git / sécurité
- `gitleaks` installé via Linuxbrew dans le conteneur OpenClaw
- Binaire: `/data/linuxbrew/.linuxbrew/bin/gitleaks`
- Version validée: `8.30.1`
- Si PATH incomplet dans un shell, utiliser le chemin absolu ci-dessus

### Notion
- Notion API configurée sur le VPS principal
- Clé stockée dans `~/.config/notion/api_key`
- Permissions de fichier attendues: `600`
- L'intégration Notion peut lire/écrire dans la page `OpenClaw`
- Usage validé en lecture + écriture en avril 2026

### Google Workspace
- `gog` est installé via Linuxbrew dans le conteneur OpenClaw
- Binaire: `/data/linuxbrew/.linuxbrew/bin/gog`
- Version validée: `v0.12.0`
- Config locale: `~/.config/gogcli`
- Auth Drive déjà configurée et utilisée avec succès
- Log technique: `/data/.openclaw/workspace/labs/gog_setup_log.md`
- À continuer sans stocker de secrets dans le workspace Git

### OpenClaw workspace security
- Hooks anti-secrets installés sur les repos Git du workspace
- Attention: sur le repo racine OpenClaw, ignorer les chemins système locaux comme `config/identity/` et `1/` pour éviter les faux positifs
- Référence pratique: `SAFE_GIT.md`

