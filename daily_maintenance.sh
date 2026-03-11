#!/bin/bash

# Configuration
WEBHOOK_URL="https://discordapp.com/api/webhooks/1479604609478692925/ZbafnHoxKYTuntCsZvu9PBTg8gFrtaRDJdXXfnH8e7W7F-wuJuWjsdKEZr1s3GXm9FEz"
LOG_FILE="/data/.openclaw/workspace/maintenance.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

# Patch pour permettre à systemctl --user de fonctionner en tâche de fond (cron)
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

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

    # Échapper les guillemets et les retours à la ligne pour le JSON
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

# 1. Mise à jour d'OpenClaw via npm (remplace 'openclaw update' pour les installations non-git)
echo "Exécution de la mise à jour..." >> "$LOG_FILE"
UPDATE_OUTPUT=$(npm install -g openclaw@latest 2>&1)
EXIT_CODE=$?

echo "$UPDATE_OUTPUT" >> "$LOG_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    # Succès
    echo "Mise à jour réussie." >> "$LOG_FILE"
    
    # Extraction de la version
    VERSION_INFO=$(openclaw --version)
    
    # 2. Redémarrage du service Gateway
    echo "Redémarrage du Gateway..." >> "$LOG_FILE"
    RESTART_OUTPUT=$(openclaw gateway restart 2>&1)
    
    # 3. Sauvegarde Git quotidienne (Secure)
    echo "Exécution du backup Git sécurisé..." >> "$LOG_FILE"
    
    # Run the secure node script
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
    # Échec
    echo "Erreur lors de la mise à jour." >> "$LOG_FILE"
    
    SUGGESTION="Veuillez vérifier les logs dans $LOG_FILE ou exécuter 'npm install -g openclaw@latest' manuellement pour diagnostiquer le problème."
    
    REPORT="**Erreur critique lors de la mise à jour.**\n\n**Code de sortie :** $EXIT_CODE\n\n**Sortie de la commande :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`\n\n👉 **Action requise :** $SUGGESTION"
    
    send_discord "failure" "$REPORT"
fi
