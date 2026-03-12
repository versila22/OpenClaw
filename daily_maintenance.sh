#!/bin/bash

# Configuration
WEBHOOK_URL="https://discordapp.com/api/webhooks/1479604609478692925/ZbafnHoxKYTuntCsZvu9PBTg8gFrtaRDJdXXfnH8e7W7F-wuJuWjsdKEZr1s3GXm9FEz"
LOG_FILE="/data/.openclaw/workspace/maintenance.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

# Fonction pour envoyer un message Discord
send_discord() {
    local status="$1"
    local message="$2"
    local color=""
    local title=""

    if [ "$status" == "success" ]; then
        color=3066993 # Vert
        title="✅ Maintenance Réussie"
    else
        color=15158332 # Rouge
        title="❌ Échec de la Maintenance"
    fi

    clean_message=$(echo "$message" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g' | cut -c 1-1900)

    json_payload=$(cat <<EOF
{
  "embeds": [{
    "title": "$title",
    "description": "$clean_message",
    "color": $color,
    "footer": {
      "text": "OpenClaw Maintenance • $DATE"
    }
  }]
}
EOF
)

    curl -H "Content-Type: application/json" -d "$json_payload" "$WEBHOOK_URL"
}

echo "[$DATE] Démarrage de la maintenance..." > "$LOG_FILE"

# 1. Mise à jour via sudo npm install -g (au lieu du user local npm)
echo "Exécution de la mise à jour (sudo npm install)..." >> "$LOG_FILE"
UPDATE_OUTPUT=$(sudo -n npm install -g openclaw@latest 2>&1)
EXIT_CODE=$?

echo "$UPDATE_OUTPUT" >> "$LOG_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Mise à jour réussie." >> "$LOG_FILE"
    
    VERSION_INFO=$(openclaw --version)
    
    # 2. Redémarrage du Gateway via signal SIGUSR1 (plus fiable que D-Bus systemctl)
    echo "Redémarrage du Gateway (SIGUSR1)..." >> "$LOG_FILE"
    pkill -SIGUSR1 -f "openclaw-gateway"
    RESTART_OUTPUT="Signal de redémarrage (SIGUSR1) envoyé à OpenClaw."
    echo "$RESTART_OUTPUT" >> "$LOG_FILE"
    
    # 3. Sauvegarde Git quotidienne (Secure)
    echo "Exécution du backup Git sécurisé..." >> "$LOG_FILE"
    node /data/.openclaw/workspace/scripts/secure_backup.js >> "$LOG_FILE" 2>&1
    BACKUP_STATUS=$?
    
    if [ $BACKUP_STATUS -eq 0 ]; then
        BACKUP_MSG="\n\n✅ **Backup Git :** Sécurisé & Poussé"
    else
        BACKUP_MSG="\n\n⚠️ **Backup Git :** Échec (Voir logs)"
    fi

    REPORT="**Mise à jour terminée avec succès.**\n\n**Version actuelle :** $VERSION_INFO\n\n**Détails :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`\n\n**Statut du redémarrage :**\n$RESTART_OUTPUT$BACKUP_MSG"
    
    send_discord "success" "$REPORT"
else
    echo "Erreur lors de la mise à jour." >> "$LOG_FILE"
    
    SUGGESTION="Vérifiez les logs ou exécutez 'sudo npm install -g openclaw@latest' manuellement."
    
    REPORT="**Erreur critique lors de la mise à jour.**\n\n**Code :** $EXIT_CODE\n\n**Sortie :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`\n\n👉 **Action requise :** $SUGGESTION"
    
    send_discord "failure" "$REPORT"
fi
