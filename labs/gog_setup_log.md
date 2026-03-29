# Log Technique : Configuration Google Workspace CLI (gog)

## 1. Contexte & Provisioning
- **Outil :** `gog` (Google Workspace CLI)
- **Objectif :** Intégration Google Drive pour pipeline RAG juridique.
- **Date de configuration initiale :** Mars 2026
- **Environnement :** OpenClaw (Node environment)

## 2. Configuration GCP (Google Cloud Console)
- **Projet :** `openclaw-assistant-489321`
- **Type d'application :** Desktop App (Installed)
- **Scopes Requis :**
  - `https://www.googleapis.com/auth/gmail.modify`
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/drive`
  - `https://www.googleapis.com/auth/contacts`
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/documents`

## 3. Déploiement Local
- **Fichier de secrets :** `client_secret.json` (racine du workspace).
- **Importation initiale :**
  ```bash
  gog auth credentials client_secret.json
  ```
- **Fichiers de configuration générés :**
  - `~/.config/gogcli/config.json` : Définit le backend (`{"keyring_backend": "file"}`).
  - `~/.config/gogcli/credentials.json` : Contient le Client ID et Client Secret.

## 4. Gestion des Jetons & Sécurité
- **Backend Keyring :** `file` (stocké dans `~/.config/gogcli/keyring/`).
- **Contrainte :** Nécessite la variable d'environnement `GOG_KEYRING_PASSWORD` pour les exécutions non-interactives (CI/CD / Agent).
- **Compte authentifié :** `jerome.jacq@gmail.com` (GOG_ACCOUNT).

## 5. Procédure de Réplication
1. Placer `client_secret.json` dans le nouveau workspace.
2. Installer `gog` via Homebrew : `brew install steipete/tap/gogcli`.
3. Exécuter l'importation des credentials.
4. Lancer l'authentification OAuth (nécessite une validation via navigateur) :
   ```bash
   gog auth add jerome.jacq@gmail.com --services gmail,calendar,drive,contacts,sheets,docs
   ```
5. Exporter/Importer les jetons du keyring si le navigateur n'est pas accessible sur la nouvelle instance.
