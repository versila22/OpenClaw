# Monitoring
- If the current time is between 04:00 and 05:00 (Europe/Paris), check `/data/.openclaw/workspace/maintenance.log`.
- If there is no log entry for today's date (YYYY-MM-DD), execute `/data/.openclaw/workspace/daily_maintenance.sh`.
- Do not run if already executed today.

# Spotify SACEM Logging
- Execute `/data/.openclaw/workspace/spotify_env/bin/python /data/.openclaw/workspace/sacem_logger.py` to track music usage. Note: This requires an active OAuth token in .cache.
