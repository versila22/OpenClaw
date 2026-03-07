const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// --- CONFIG ---
const WORKSPACE_DIR = '/data/.openclaw/workspace';
const CONFIG_FILE = '/data/.openclaw/openclaw.json';
const BACKUP_CONFIG_FILE = path.join(WORKSPACE_DIR, 'openclaw_config_sanitized.json');
const DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1479604609478692925/ZbafnHoxKYTuntCsZvu9PBTg8gFrtaRDJdXXfnH8e7W7F-wuJuWjsdKEZr1s3GXm9FEz"; // From daily_maintenance.sh

// --- SECRETS PATTERNS ---
const SECRET_PATTERNS = [
    { name: 'OPENAI_API_KEY', regex: /sk-[a-zA-Z0-9]{32,}/g },
    { name: 'CLAUDE_API_KEY', regex: /sk-ant-[a-zA-Z0-9\-\_]{32,}/g },
    { name: 'GITHUB_TOKEN', regex: /(gh[pous]_[a-zA-Z0-9]{36,})/g },
    { name: 'DISCORD_TOKEN', regex: /[MKN][a-zA-Z0-9_-]{23,}\.[a-zA-Z0-9_-]{6,}\.[a-zA-Z0-9_-]{27,}/g },
    { name: 'GENERIC_TOKEN', regex: /([a-z0-9]{32,})/gi, exclude: true } // Careful with generic
];

function log(msg) {
    console.log(`[Backup] ${msg}`);
}

function sendDiscord(status, message) {
    if (!DISCORD_WEBHOOK) return;
    const color = status === 'success' ? 3066993 : 15158332;
    const payload = {
        embeds: [{
            title: status === 'success' ? "✅ Secure Backup Complete" : "❌ Backup Failed",
            description: message,
            color: color,
            footer: { text: "OpenClaw Security • " + new Date().toISOString() }
        }]
    };
    try {
        execSync(`curl -H "Content-Type: application/json" -d '${JSON.stringify(payload)}' "${DISCORD_WEBHOOK}"`, { stdio: 'ignore' });
    } catch (e) {
        log("Failed to send Discord notification");
    }
}

function sanitizeText(text) {
    let sanitized = text;
    for (const pattern of SECRET_PATTERNS) {
        if (pattern.exclude) continue; // Skip generic for now to avoid false positives in hashes
        sanitized = sanitized.replace(pattern.regex, `[REDACTED_${pattern.name}]`);
    }
    return sanitized;
}

function sanitizeConfig(configPath) {
    if (!fs.existsSync(configPath)) {
        log("Config file not found: " + configPath);
        return;
    }
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        // Deep traverse and mask sensitive keys
        const maskSensitive = (obj) => {
            for (const key in obj) {
                if (typeof obj[key] === 'object' && obj[key] !== null) {
                    maskSensitive(obj[key]);
                } else if (typeof obj[key] === 'string') {
                    if (/token|secret|password|key|auth/i.test(key)) {
                        obj[key] = `[REDACTED_${key.toUpperCase()}]`;
                    }
                }
            }
        };
        
        maskSensitive(config);
        fs.writeFileSync(BACKUP_CONFIG_FILE, JSON.stringify(config, null, 2));
        log("Config sanitized and saved to workspace.");
    } catch (e) {
        log("Error sanitizing config: " + e.message);
        throw e;
    }
}

function scanWorkspace() {
    log("Scanning workspace for leaked secrets...");
    const files = fs.readdirSync(WORKSPACE_DIR).filter(f => f.endsWith('.md') || f.endsWith('.json') || f.endsWith('.js') || f.endsWith('.sh'));
    
    let leaksFound = 0;
    
    files.forEach(file => {
        if (file === 'openclaw_config_sanitized.json') return; // Skip our safe file
        const filePath = path.join(WORKSPACE_DIR, file);
        if (fs.lstatSync(filePath).isDirectory()) return;

        let content = fs.readFileSync(filePath, 'utf8');
        let originalContent = content;
        
        content = sanitizeText(content);
        
        if (content !== originalContent) {
            log(`⚠️  Secrets found and redacted in ${file}`);
            fs.writeFileSync(filePath, content);
            leaksFound++;
        }
    });
    
    if (leaksFound > 0) {
        log(`Cleaned ${leaksFound} files.`);
    } else {
        log("No leaks found in workspace files.");
    }
}

function gitBackup() {
    try {
        process.chdir(WORKSPACE_DIR);
        
        // 1. Sanitize Config
        sanitizeConfig(CONFIG_FILE);
        
        // 2. Scan Workspace
        scanWorkspace();
        
        // 3. Git Operations
        execSync('git add .');
        
        // Check for changes
        try {
            execSync('git diff-index --quiet HEAD --');
            log("No changes to commit.");
            return; // Nothing to do
        } catch (e) {
            // Changes exist, proceed
        }

        const date = new Date().toISOString().split('T')[0];
        const commitMsg = `chore: secure backup ${date}`;
        
        execSync(`git commit -m "${commitMsg}"`);
        log("Committed changes.");
        
        execSync('git push origin main');
        log("Pushed to GitHub.");
        
        sendDiscord("success", `Backup pushed successfully to GitHub.\nConfig sanitized.\nWorkspace scanned.`);
        
    } catch (e) {
        log("Backup failed: " + e.message);
        sendDiscord("failure", `Error during backup:\n\`${e.message}\``);
        process.exit(1);
    }
}

// Run
gitBackup();
