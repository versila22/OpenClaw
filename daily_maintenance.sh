#!/bin/bash

# --- CONFIGURATION (Chemins Absolus) ---
WEBHOOK_URL="https://discordapp.com/api/webhooks/1479604609478692925/ZbafnHoxKYTuntCsZvu9PBTg8gFrtaRDJdXXfnH8e7W7F-wuJuWjsdKEZr1s3GXm9FEz"
DOCKER_DIR="/docker/openclaw-nmtd"
BASE_DATA_DIR="/docker/openclaw-nmtd/data/.openclaw/workspace"
LOG_FILE="$BASE_DATA_DIR/maintenance.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

# Fonction Discord
send_discord() {
    local status="$1"
    local message="$2"
    local color=$([ "$status" == "success" ] && echo "3066993" || echo "15158332")
    local title=$([ "$status" == "success" ] && echo "✅ Maintenance Réussie" || echo "❌ Échec de la Maintenance")
    clean_message=$(echo "$message" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g' | cut -c 1-1900)
    json_payload="{\"embeds\": [{\"title\": \"$title\", \"description\": \"$clean_message\", \"color\": $color, \"footer\": {\"text\": \"OpenClaw Docker • $DATE\"}}]}"
    curl -s -H "Content-Type: application/json" -d "$json_payload" "$WEBHOOK_URL" > /dev/null
}

echo "[$DATE] Démarrage de la maintenance..." > "$LOG_FILE"

# 1. Mise à jour Docker
if cd "$DOCKER_DIR"; then
    echo "Pulling images..." >> "$LOG_FILE"
    UPDATE_OUTPUT=$(docker compose pull 2>&1)
    docker compose up -d >> "$LOG_FILE" 2>&1
    
    # Récupération de la version
    VERSION_INFO=$(docker exec openclaw-nmtd-openclaw-1 openclaw --version 2>/dev/null || echo "v2026.x")
    
    # 2. Sauvegarde Git
    echo "Backup Git via Docker." >> "$LOG_FILE"
    # Note : On utilise le chemin absolu vers le script node
    docker exec -e GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" openclaw-nmtd-openclaw-1 node /data/.openclaw/workspace/scripts/secure_backup.js >> "$LOG_FILE" 2>&1
    
    REPORT="**Mise à jour effectuée.**\n\n**Version :** $VERSION_INFO\n\n**Logs :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`"
    send_discord "success" "$REPORT"
else
    send_discord "failure" "Impossible d'accéder au dossier $DOCKER_DIR"
fi
