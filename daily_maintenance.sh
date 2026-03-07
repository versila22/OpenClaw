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

# 1. Mise à jour d'OpenClaw (sans redémarrage auto pour contrôler le flux)
echo "Exécution de la mise à jour..." >> "$LOG_FILE"
UPDATE_OUTPUT=$(openclaw update --yes --no-restart 2>&1)
EXIT_CODE=$?

echo "$UPDATE_OUTPUT" >> "$LOG_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    # Succès
    echo "Mise à jour réussie." >> "$LOG_FILE"
    
    # Extraction de la version (tentative simple)
    VERSION_INFO=$(openclaw --version)
    
    # 2. Redémarrage du service Gateway
    echo "Redémarrage du Gateway..." >> "$LOG_FILE"
    RESTART_OUTPUT=$(openclaw gateway restart 2>&1)
    
    # 3. Sauvegarde Git quotidienne
    echo "Exécution du backup Git..." >> "$LOG_FILE"
    git add . >> "$LOG_FILE" 2>&1
    if ! git diff-index --quiet HEAD --; then
        git commit -m "chore: auto-backup $(date +%Y-%m-%d)" >> "$LOG_FILE" 2>&1
        PUSH_OUTPUT=$(git push origin main 2>&1)
        PUSH_STATUS=$?
        if [ $PUSH_STATUS -eq 0 ]; then
            BACKUP_MSG="\n\n✅ **Backup Git :** Succès"
        else
            BACKUP_MSG="\n\n⚠️ **Backup Git :** Échec (Push impossible - Vérifier auth)\n\`\`\`\n$PUSH_OUTPUT\n\`\`\`"
        fi
    else
        BACKUP_MSG="\n\nℹ️ **Backup Git :** Aucun changement à sauvegarder."
    fi

    REPORT="**Mise à jour terminée avec succès.**\n\n**Version actuelle :** $VERSION_INFO\n\n**Détails :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`\n\n**Statut du redémarrage :**\n$RESTART_OUTPUT$BACKUP_MSG"
    
    send_discord "success" "$REPORT"
else
    # Échec
    echo "Erreur lors de la mise à jour." >> "$LOG_FILE"
    
    SUGGESTION="Veuillez vérifier les logs dans $LOG_FILE ou exécuter 'openclaw update' manuellement pour diagnostiquer le problème."
    
    REPORT="**Erreur critique lors de la mise à jour.**\n\n**Code de sortie :** $EXIT_CODE\n\n**Sortie de la commande :**\n\`\`\`\n$UPDATE_OUTPUT\n\`\`\`\n\n👉 **Action requise :** $SUGGESTION"
    
    send_discord "failure" "$REPORT"
fi
