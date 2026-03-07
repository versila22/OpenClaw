# Monitoring
- If the current time is between 04:00 and 05:00 (Europe/Paris), check `/data/.openclaw/workspace/maintenance.log`.
- If there is no log entry for today's date (YYYY-MM-DD), execute `/data/.openclaw/workspace/daily_maintenance.sh`.
- Do not run if already executed today.
