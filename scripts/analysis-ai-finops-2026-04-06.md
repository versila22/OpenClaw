# Analyse technique & fonctionnelle — AI FinOps
**Date :** 2026-04-06  
**Auteur :** Jayvis (subagent OpenClaw)  
**Projet :** `/data/.openclaw/workspace/ai-finops/`  
**Objectif :** Analyse exhaustive pour entretiens portfolio ingénieur IA

---

## Table des matières

1. [Architecture générale](#1-architecture-générale)
2. [Qualité technique](#2-qualité-technique)
3. [Analyse fonctionnelle](#3-analyse-fonctionnelle)
4. [Propositions concrètes](#4-propositions-concrètes)

---

## 1. Architecture générale

### 1.1 Vue d'ensemble — Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERNET (HTTPS)                             │
└─────────────────────────────────────────────────────────────────────┘
         │ ai-finops.duckdns.org            │ ai-finops-api.duckdns.org
         ▼                                  ▼
┌─────────────────────┐        ┌─────────────────────┐
│     Traefik         │        │     Traefik          │
│  (TLS termination)  │        │  (TLS termination)   │
└─────────┬───────────┘        └──────────┬───────────┘
          │ :80                            │ :8001
          ▼                               ▼
┌─────────────────────┐        ┌──────────────────────────┐
│    Nginx (Docker)   │        │    FastAPI / Uvicorn      │
│  Static SPA         │        │   (Docker container)      │
│  dist/index.html    │        │                           │
│  dist/assets/*.js   │        │  ┌────────────────────┐  │
│                     │        │  │  api/v1/routes/    │  │
│  /api/v1/* →        │        │  │  auth.py           │  │
│  proxy to backend   │        │  │  dashboard.py      │  │
└─────────────────────┘        │  │  providers.py      │  │
          │                    │  │  settings.py       │  │
          │ (SPA in browser)   │  │  health.py         │  │
          │ Authorization:     │  └────────┬───────────┘  │
          │ Bearer <JWT>       │           │               │
          └────────────────────┤  ┌────────▼───────────┐  │
                               │  │  services/         │  │
                               │  │  dashboard_service │  │
                               │  │  notification_svc  │  │
                               │  │  sync/ (connectors)│  │
                               │  └────────┬───────────┘  │
                               │           │               │
                               │  ┌────────▼───────────┐  │
                               │  │  SQLite (WAL=off)  │  │
                               │  │  finops.db         │  │
                               │  │  (volume mount)    │  │
                               │  └────────────────────┘  │
                               └──────────────────────────┘
                                          │ httpx async calls
                               ┌──────────▼───────────────────┐
                               │  External Provider APIs       │
                               │  - OpenAI /v1/organization/   │
                               │    costs (admin key)          │
                               │  - OpenAI /v1/usage (fallback)│
                               │  - Anthropic /v1/messages     │
                               │    (key validation only)      │
                               │  - ElevenLabs /v1/user/       │
                               │    subscription               │
                               └──────────────────────────────┘
```

### 1.2 Stack Frontend (React/Vite)

**Fichiers clés :** `src/`, `vite.config.ts`, `package.json`

| Couche | Technologie | Version |
|--------|-------------|---------|
| Framework | React | 18.3.1 |
| Bundler | Vite + SWC | 5.4.19 |
| Routing | react-router-dom | 6.30.1 |
| State/Cache | TanStack Query | 5.83.0 |
| UI Components | Radix UI / ShadCN | Various |
| Styling | Tailwind CSS | 3.4.17 |
| Charts | Recharts | 2.15.4 |
| Forms | react-hook-form + zod | 7.61.1 / 3.25 |
| i18n | custom (src/i18n/) | — |
| Auth token | localStorage | — |

**Flux d'authentification frontend (`src/lib/auth.ts`, `src/lib/api.ts`) :**
```
1. POST /api/v1/auth/login → { accessToken, tokenType, user }
2. setToken(accessToken) → localStorage["ai-finops.jwt"]
3. Toutes les requêtes : Authorization: Bearer <token>
4. 401 reçu → clearToken() + redirect /login
```

**Organisation des pages (`src/pages/`) :**
- `Index.tsx` → Dashboard principal (KPIs, risques, alertes)
- `Providers.tsx` → Liste providers
- `ProviderDetail.tsx` → Détail provider + usage journalier
- `Alerts.tsx` → Centre d'alertes
- `Plans.tsx` → Vue des plans
- `Adjustments.tsx` → Ajustements manuels
- `Login.tsx`, `Register.tsx` → Auth
- `NotFound.tsx` → 404

**Hooks API (`src/hooks/use-api.ts`) :**
```typescript
// staleTime configurés :
useDashboard()    → staleTime: 30_000ms  (30s)
useProviders()    → staleTime: 60_000ms  (60s)
useProvider(id)   → staleTime: 60_000ms  (60s)
useAlerts()       → staleTime: 60_000ms  (60s)
usePlans()        → staleTime: 60_000ms  (60s)
useAdjustments()  → staleTime: 60_000ms  (60s)
```
Il n'y a **aucun polling automatique** (pas de `refetchInterval`). Les données ne se rafraîchissent que sur navigation ou invalidation manuelle.

### 1.3 Stack Backend (FastAPI)

**Fichiers clés :** `backend/app/`

```
app/
├── main.py                    # Entrypoint FastAPI + lifespan
├── auth.py                    # JWT creation/verification
├── api/v1/routes/
│   ├── auth.py                # POST /auth/register, /auth/login
│   ├── dashboard.py           # GET /dashboard
│   ├── providers.py           # CRUD + /sync/*
│   ├── settings.py            # GET/PUT /settings
│   └── health.py              # GET /health
├── core/
│   ├── config.py              # Settings (pydantic-settings)
│   ├── db.py                  # SQLAlchemy engine + get_db()
│   ├── enums.py               # SyncStatus, PlanType, etc.
│   └── rate_limit.py          # slowapi Limiter
├── models/                    # SQLAlchemy ORM models
│   ├── user.py
│   ├── provider.py            # 27 colonnes, flat (no timestamps)
│   ├── alert.py
│   ├── adjustment.py
│   ├── plan.py
│   └── settings.py
├── schemas/
│   ├── dashboard.py           # Pydantic v2 schemas (camelCase)
│   ├── provider.py
│   └── settings.py
├── services/
│   ├── dashboard_service.py   # compute_kpis(), generate_daily_usage()
│   ├── notification_service.py # check_and_notify_alerts()
│   └── sync/
│       ├── sync_service.py    # Orchestrateur
│       ├── openai_sync.py     # Connecteur OpenAI
│       ├── anthropic_sync.py  # Connecteur Anthropic (key-only)
│       └── elevenlabs_sync.py # Connecteur ElevenLabs
└── seed/seed_data.py          # Données initiales Jerome
```

**Lifespan FastAPI (`main.py`, lignes 29-37) :**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed()
    asyncio.create_task(_background_sync())  # sync 2s après démarrage
    yield
```
Les 3 syncs (OpenAI, Anthropic, ElevenLabs) s'exécutent séquentiellement au démarrage.

### 1.4 Architecture Docker

**Fichier :** `docker-compose.prod.yml`

```yaml
services:
  backend:          # Python FastAPI, :8001
    volumes:
      - ./backend/finops.db:/app/finops.db   # ⚠️ BIND MOUNT direct
    networks: [internal, traefik_default]

  frontend:         # Nginx static + proxy
    networks: [internal, traefik_default]

networks:
  internal:         # réseau isolé backend↔frontend
  traefik_default:  # externe, géré par Traefik
    external: true
```

**Points notables :**
- Traefik gère TLS Let's Encrypt (labels)
- `finops.db` = **bind mount**, non-volume Docker → backup non automatisé
- Pas de `healthcheck:` défini sur le backend
- Pas de `--workers N` sur uvicorn → **single-process** en prod
- Frontend utilise nginx comme proxy pour `/api/v1/*` → simplifie CORS

**Architecture nginx (`nginx.conf`) :**
```nginx
location /api/v1/ {
    proxy_pass http://backend:8001/api/v1/;
    # headers X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
}
location /assets/ {
    expires 30d;          # cache navigateur 30 jours
    add_header Cache-Control "public, immutable";
}
```

### 1.5 Pipeline de sync par provider

**Fichier :** `backend/app/services/sync/sync_service.py`

```
sync_all_providers(db)
    ├─ _sync_openai(db)
    │   ├─ fetch_openai_usage()
    │   │   ├─ Method 1: /organization/costs (OPENAI_ADMIN_KEY)
    │   │   └─ Method 2: /v1/usage per-day estimation (OPENAI_API_KEY)
    │   ├─ UPDATE provider SET consumed, usage_percent, sync_status
    │   └─ _compute_recommendation(usage_percent, days_until_reset)
    │
    ├─ _sync_anthropic(db)
    │   ├─ fetch_anthropic_usage()
    │   │   └─ POST /v1/messages (1 token) → validate key only
    │   └─ UPDATE provider SET sync_status="synced" ONLY (consumed unchanged)
    │
    └─ _sync_elevenlabs(db)
        ├─ fetch_elevenlabs_usage()
        │   └─ GET /v1/user/subscription → character_count, character_limit
        ├─ UPDATE provider SET consumed, remaining, usage_percent
        └─ _compute_recommendation(...)

Après chaque sync:
    check_and_notify_alerts(db)
        ├─ usage_percent >= 80 → alert "High Usage"
        ├─ overage > 0         → alert "Overage"
        └─ usage_percent < 30  → alert "Underused Plan"
```

### 1.6 Flux JWT (Frontend ↔ Backend)

```
Frontend (browser)
    │
    │ POST /api/v1/auth/login { email, password }
    ▼
FastAPI /auth/login (auth.py)
    │ authenticate_user(db, email, password)
    │ → bcrypt/pbkdf2_sha256 verify
    │ create_access_token(user.email)
    │ → jwt.encode({ sub: email, exp: now+60min }, JWT_SECRET, HS256)
    │
    ◄── { accessToken, tokenType: "bearer", user: { id, email } }
    │
    │ localStorage.setItem("ai-finops.jwt", accessToken)
    │
    │ Toutes requêtes suivantes:
    │ Authorization: Bearer <token>
    ▼
FastAPI get_current_user() (auth.py:74)
    │ jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    │ payload["sub"] → email
    │ db.query(User).filter_by(email=email).first()
    └─ return user | raise 401
```

**Points de sécurité :**
- Token stocké en **localStorage** → vulnérable XSS (meilleure pratique = httpOnly cookie)
- Pas de **refresh token** → expiration silencieuse à 60 min
- Pas de **token revocation** (liste noire)
- JWT_SECRET est un **Field(...)** requis → pas de valeur par défaut (bon point)
- `algorithm=HS256` → symétrique, acceptable pour MVP

---

## 2. Qualité technique

### 2.1 SQLite — Limitations pour un app FinOps multi-utilisateur

**Fichier :** `backend/app/core/db.py`

```python
engine = create_engine(
    settings.DATABASE_URL,         # "sqlite:///./finops.db"
    connect_args={"check_same_thread": False},
    echo=False,
)
```

**Problèmes identifiés :**

| Problème | Détail | Sévérité |
|----------|--------|----------|
| Pas de WAL mode | SQLite par défaut = DELETE journal → locks exclusifs en écriture | 🔴 Haut |
| Pas de pool de connexions | StaticPool non configuré en prod → 1 connexion partagée | 🟡 Moyen |
| Bind mount (pas de volume Docker) | `./backend/finops.db` → pas de backup automatique | 🔴 Haut |
| Pas de migrations | Alembic absent → `create_tables()` au démarrage → schema drift impossible à gérer | 🟡 Moyen |
| Concurrent writes | Avec uvicorn single-process, OK. Avec `--workers N`, corruption possible | 🔴 Haut (si scale) |
| Pas de `PRAGMA journal_mode=WAL` | Writes concurrents bloquent les reads | 🟡 Moyen |

**Migration path vers PostgreSQL :**
1. Remplacer `DATABASE_URL = "sqlite:///./finops.db"` par `postgresql+psycopg2://...`
2. Supprimer `connect_args={"check_same_thread": False}` (SQLite-specific)
3. Ajouter Alembic pour migrations
4. Ajouter service PostgreSQL dans docker-compose.prod.yml
5. Remplacer `String` PKs et les enums string par des vrais UUID et enums PostgreSQL

**Quick fix SQLite (sans migrer) :**
```python
# core/db.py — activer WAL + foreign keys
@event.listens_for(engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### 2.2 Sync Reliability — Que se passe-t-il si un provider est down?

**Fichier :** `backend/app/services/sync/sync_service.py`

**Analyse :**

```python
async def _sync_openai(db: Session) -> dict:
    try:
        result = await fetch_openai_usage()
        ...
    except Exception as e:
        logger.error(f"OpenAI sync exception: {e}")
        try:
            provider = db.query(Provider).filter_by(id="openai").first()
            if provider:
                provider.sync_status = "error"   # ✅ marque l'erreur
                provider.last_sync = _now_iso()
                db.commit()
        except Exception:
            pass                                  # ⚠️ silently ignores DB errors
        return {"provider": "openai", "status": "error", "reason": str(e)}
```

**Ce qui manque :**

1. **Pas de retry avec backoff exponentiel** — si l'API OpenAI est temporairement down, la sync échoue et c'est tout. Aucun retry programmé.

2. **Syncs séquentielles sans parallélisme** (`sync_service.py:164-168`) :
   ```python
   results = [
       await _sync_openai(db),
       await _sync_anthropic(db),     # attend que OpenAI finisse
       await _sync_elevenlabs(db),    # attend que Anthropic finisse
   ]
   ```
   Si OpenAI met 20s, ElevenLabs attend. Devrait utiliser `asyncio.gather()`.

3. **Pas de circuit breaker** — une API down va être rappelée à chaque sync même si elle échoue depuis 10 fois.

4. **Timeout httpx global = 15-20s par appel** (`timeout=15` dans fetch_openai_usage ligne 73) — acceptable mais pas configurable.

5. **OpenAI fallback = jour par jour** (`openai_sync.py`, méthode 2) — si le mois a 30 jours = 30 requêtes HTTP séquentielles pour une sync.

6. **Pas de sync périodique automatique** — la sync ne se déclenche qu'au démarrage et sur action utilisateur. Pas de tâche cron/schedule.

**Recommandation :**
```python
# Paralléliser avec gather
results = await asyncio.gather(
    _sync_openai(db),
    _sync_anthropic(db),
    _sync_elevenlabs(db),
    return_exceptions=True
)
```

### 2.3 Absence de cache — Dashboard recalculé à chaque requête

**Fichier :** `backend/app/api/v1/routes/dashboard.py`

```python
@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), ...):
    providers = db.query(Provider).all()    # 1 query
    alerts = db.query(Alert).all()          # 1 query
    kpis = compute_kpis(db)                 # 3 queries (providers + alerts + settings)
    return DashboardResponse(...)           # serialisation complète
```

**Impact :** 5 requêtes SQLite + sérialisation Pydantic complète à chaque GET `/dashboard`. Le frontend appelle cet endpoint avec `staleTime: 30_000ms` — donc en théorie pas plus d'une fois toutes les 30s par session browser. Mais avec plusieurs utilisateurs simultanés = N fois par 30s.

**Solution simple (sans Redis) :**
```python
from functools import lru_cache
from datetime import datetime, timedelta

_dashboard_cache: dict = {}
_CACHE_TTL = timedelta(seconds=30)

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), ...):
    cache_key = "dashboard"
    cached = _dashboard_cache.get(cache_key)
    if cached and datetime.utcnow() - cached["ts"] < _CACHE_TTL:
        return cached["data"]
    # ... compute ...
    _dashboard_cache[cache_key] = {"data": result, "ts": datetime.utcnow()}
    return result
```

**Solution robuste :** Ajouter Redis + `fastapi-cache2` pour cache distribué compatible multi-workers.

### 2.4 Bundle Frontend — 880KB JS, opportunités de code splitting

**Fichier :** `dist/assets/index-DPQr8URn.js` (880 694 bytes = ~860KB)

```
dist/assets/
├── index-DPQr8URn.js    880 694 B  ← tout en un seul chunk !
└── index-DMW9JJ44.css    68 134 B
```

**Causes principales :**
- Toutes les pages chargées d'un coup (pas de lazy loading)
- Recharts (~300KB minifié) inclus globalement
- Radix UI = ~50KB par composant, tous importés
- ShadCN components = 50+ composants dans `src/components/ui/`
- `src/data/mockData.ts` toujours importé (types ET données statiques)

**Recommandations :**

```typescript
// vite.config.ts — activer code splitting par page
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-charts': ['recharts'],
          'vendor-radix': [/* tous les @radix-ui/... */],
        }
      }
    }
  }
})

// App.tsx — lazy loading des pages
const Index = lazy(() => import('./pages/Index'));
const ProviderDetail = lazy(() => import('./pages/ProviderDetail'));
// ... etc avec <Suspense>
```

**Gain estimé :** Bundle principal → ~120KB. Pages chargées à la demande.

**Autre point :** `src/data/mockData.ts` contient des données statiques JSON (providers fictifs) ET les types TypeScript. Ces données sont encore importées via le type `Provider` dans `src/lib/api.ts` (ligne 6). À terme, extraire les types vers `src/types/` et supprimer les données mock du bundle prod.

### 2.5 Couverture de tests — Analyse des 36 tests

**Fichiers :** `backend/tests/`

```
test_auth.py         9 tests  ✅ login, register, JWT expired
test_providers.py   14 tests  ✅ CRUD, sync, 404
test_dashboard.py    2 tests  ⚠️ seulement happy path + auth
test_alerts.py       3 tests  ⚠️ minimal
test_plans.py        3 tests  ⚠️ minimal
test_adjustments.py  3 tests  ⚠️ minimal
test_settings.py     6 tests  ✅ GET/PUT + erreurs
```

**Ce qui manque (exhaustif) :**

| Domaine | Tests manquants | Priorité |
|---------|----------------|---------|
| **Sync services** | Tests unitaires pour `fetch_openai_usage()`, `fetch_elevenlabs_usage()` avec mocks httpx | 🔴 Critique |
| **notification_service** | Test `check_and_notify_alerts()` — quel seuil déclenche quoi? | 🔴 Critique |
| **dashboard_service** | Test `compute_kpis()` avec données diverses | 🟡 Moyen |
| **Concurrence** | Test 2 users simultanés sur même provider | 🟡 Moyen |
| **Rate limiting** | Test que `/sync/all` retourne 429 après 5 appels/min | 🟡 Moyen |
| **JWT expire** | Test token expiré sur tous les endpoints (pas que dashboard) | 🟡 Moyen |
| **Seed idempotency** | Test que seed() ne duplique pas si appelé 2 fois | 🟡 Moyen |
| **API pagination** | Test limit/offset sur tous les endpoints list | 🟢 Bas |
| **Frontend** | `src/test/example.test.ts` existe mais ne teste presque rien | 🟡 Moyen |
| **E2E** | playwright.config.ts existe mais aucun test playwright `.spec.ts` | 🟡 Moyen |
| **Error states UI** | Comportement si API down (erreur réseau) | 🟡 Moyen |

**Test manquant critique — notification_service :**
```python
# Les seuils sont HARDCODÉS dans notification_service.py
HIGH_USAGE_THRESHOLD = 80      # ligne 8
UNDERUSED_THRESHOLD = 30       # ligne 9
# Mais Settings a alert_threshold_warning=75, alert_threshold_critical=90
# → Les valeurs Settings NE SONT PAS utilisées pour les alertes !
# BUG : l'utilisateur peut changer les seuils dans Settings mais ça n'a aucun effet.
```

### 2.6 Rate Limiting — Analyse de complétude

**Fichier :** `backend/app/core/rate_limit.py` + `backend/app/api/v1/routes/providers.py`

```python
# Rate limit appliqué UNIQUEMENT sur :
@router.post("/sync")
@router.post("/sync/all")
@limiter.limit("5/minute")     # providers.py ligne 107
async def sync_all(request, ...):
```

**Endpoints NON rate-limités :**
- `POST /api/v1/auth/register` → brute force création de comptes
- `POST /api/v1/auth/login` → brute force password
- `GET /api/v1/dashboard` → peut être appelé en boucle
- `GET /api/v1/providers` → idem
- `PUT /api/v1/providers/{id}` → idem

**Risque :** Login brute force sans limitation. Un attaquant peut tester des milliers de mots de passe sans blocage.

**Solution immédiate :**
```python
# auth.py route login
@router.post("/auth/login")
@limiter.limit("10/minute")    # par IP
def login(request: Request, payload: AuthRequest, ...):
```

### 2.7 Error Handling — Sync failures

**Analyse du comportement sur failure :**

**OpenAI down :**
- Exception catchée (`sync_service.py:58-69`)
- `provider.sync_status = "error"` → visuel dans le dashboard ✅
- `provider.consumed` reste **inchangé** → affichage de données potentiellement périmées ⚠️
- `last_sync` mis à jour même en erreur → confusion sur "quand était la dernière sync réussie" ⚠️

**ElevenLabs down :**
- `return {"synced": False}` si exception (`elevenlabs_sync.py:45`)
- Dans `sync_service.py:100-103` : si `result.get("synced")` est False → `provider.sync_status = "error"` ✅
- Mais si `result` est None (pas de clé API) → `return {"provider": "elevenlabs", "status": "skipped"}` — pas d'erreur UI ⚠️

**Anthropic :**
- Le sync ne met JAMAIS à jour `consumed` (by design — pas d'API billing Anthropic)
- Mais le status passe à "synced" même si les données consommées sont manuelles
- → Confusion utilisateur : "synced" suggère que les données sont fraîches

**Recommandation :** Distinguer `sync_status = "key_valid"` vs `"synced"` pour Anthropic.

---

## 3. Analyse fonctionnelle

### 3.1 Ce qu'un vrai utilisateur FinOps attend

Un FinOps Engineer cherche à :
1. **Voir l'évolution des coûts dans le temps** (pas juste l'état courant)
2. **Comparer des périodes** (ce mois vs mois dernier)
3. **Projeter** les coûts en fin de cycle avec trend analysis
4. **Recevoir des alertes proactives** par email/Slack avant d'atteindre un seuil
5. **Exporter** des rapports pour la direction
6. **Gérer des équipes** avec des budgets par projet/service

Le projet couvre partiellement les points 1 à 3 pour l'état courant uniquement.

### 3.2 Multi-utilisateur — Architecture mono-tenant effective

**Modèle User (`backend/app/models/user.py`) :**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
```

**Tous les autres modèles :**
```python
class Provider(Base):         # pas de user_id
class Alert(Base):            # pas de user_id
class ManualAdjustment(Base): # pas de user_id
class Plan(Base):             # pas de user_id
class Settings(Base):         # id="global" — une seule ligne
```

**Conséquence :** Si 2 utilisateurs s'inscrivent, ils voient **exactement les mêmes providers, alertes et budget**. `get_current_user()` valide l'authentification mais n'isole pas les données. C'est effectivement une application **mono-tenant avec auth partagée**.

**Pour rendre vraiment multi-tenant :**
1. Ajouter `user_id = Column(String, ForeignKey("users.id"))` à tous les modèles
2. Filtrer toutes les requêtes par `current_user.id`
3. Settings → une ligne par user, pas juste "global"
4. Migration Alembic pour ajouter les colonnes + backfill

### 3.3 Historical Tracking — Stockage courant uniquement

**Provider model :** 27 colonnes, toutes représentent l'**état courant** du provider.

```python
class Provider(Base):
    consumed = Column(Float)      # coût/usage ACTUEL ce mois
    remaining = Column(Float)     # quota restant ACTUEL
    usage_percent = Column(Float) # pourcentage ACTUEL
    last_sync = Column(String)    # ISO datetime de la dernière sync
    # → PAS de timestamp de création
    # → PAS d'historique journalier en DB
```

**`generate_daily_usage()` dans `dashboard_service.py` :**
```python
def generate_daily_usage(provider: Provider) -> list[DailyUsageResponse]:
    base_daily = provider.consumed / 30
    random.seed(hash(provider.id))  # déterministique mais FAUX
    # génère 30 jours de données SIMULÉES basées sur le total actuel
    # retourne seulement 4 points (Apr 1-4)
    return data
```

**⚠️ Le graphique de consommation journalière est ENTIÈREMENT SIMULÉ.** Il ne représente pas l'historique réel.

**Pour un vrai tracking historique :**
```sql
-- Nouvelle table à créer
CREATE TABLE usage_snapshots (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    consumed REAL NOT NULL,
    remaining REAL,
    usage_percent REAL,
    monthly_cost REAL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider_id, snapshot_date)
);
```
Insérer une snapshot par provider après chaque sync réussie.

### 3.4 Budget Alerts — Vraiment déclenchées? Comment?

**`notification_service.py` — analyse complète :**

```python
HIGH_USAGE_THRESHOLD = 80     # hardcodé, IGNORÉ Settings.alert_threshold_warning
UNDERUSED_THRESHOLD = 30      # hardcodé, IGNORÉ Settings.alert_threshold_critical

def check_and_notify_alerts(db: Session) -> list[Alert]:
    # Crée des alerts en DB → rien d'autre
    # Pas d'email
    # Pas de webhook
    # Pas de push notification
    # Pas de Slack
    # Juste un INSERT dans la table alerts
```

**Flux complet :**
1. `sync_all_providers(db)` déclenche `check_and_notify_alerts(db)` 
2. Si `usage_percent >= 80` et pas d'alerte "High Usage" active → INSERT Alert
3. L'alerte est visible dans `/api/v1/alerts` et sur le dashboard
4. **Fin.** Aucune notification externe.

**Bug critique identifié :**
```python
# Settings model
alert_threshold_warning = Column(Integer, default=75)
alert_threshold_critical = Column(Integer, default=90)

# notification_service.py
HIGH_USAGE_THRESHOLD = 80  # ← fixe, ne lit jamais Settings !
```
L'utilisateur peut modifier les seuils dans `/settings` → ces valeurs sont sauvegardées en DB → mais n'ont **aucun effet** sur la logique d'alerte. C'est un bug fonctionnel.

**Fix :**
```python
def check_and_notify_alerts(db: Session) -> list[Alert]:
    settings = db.query(Settings).filter_by(id="global").first()
    high_threshold = settings.alert_threshold_warning if settings else 80
    low_threshold = 30  # pas de setting pour underused actuellement
    ...
```

### 3.5 Missing Provider Sync

| Provider | Sync | API disponible? | Notes |
|----------|------|----------------|-------|
| OpenAI | ✅ Auto | ✅ `/organization/costs` | Nécessite admin key |
| Anthropic | ⚠️ Partiel | ❌ Pas d'API billing | Validation clé uniquement |
| ElevenLabs | ✅ Auto | ✅ `/v1/user/subscription` | Fonctionnel |
| Google Gemini | ❌ Manuel | ⚠️ Oui (Cloud Billing API) | Mais complexe (OAuth2) |
| Lovable | ❌ Manuel | ❌ Pas d'API publique | Web scraping possible mais fragile |

**Google Gemini sync possible via :**
- Google Cloud Billing API (nécessite Service Account + OAuth2)
- `google-cloud-billing` Python library
- Endpoint : `billing.googleapis.com/v1/billingAccounts/{account}/skus`

**Anthropic** : Pas d'API publique. L'alternative est le scraping de `console.anthropic.com` (fragile) ou attendre leur API usage (annoncée mais pas disponible au 2026-04-06).

### 3.6 Export / Reporting — Absents

**Ce qui manque pour un usage professionnel :**

| Feature | Valeur business | Effort |
|---------|----------------|--------|
| Export CSV providers + KPIs | Partage avec équipe/direction | Petit |
| Export PDF rapport mensuel | Présentation budget | Moyen |
| API publique (OpenAPI docs) | Intégration tier tools | Petit (Swagger auto) |
| Webhook sur alerte | Slack/Teams/email | Moyen |
| Rapport comparatif mois/mois | Vision trend | Grand (nécessite historique) |

---

## 4. Propositions concrètes

### 4.1 Quick Wins (< 1 jour chacun)

#### QW1 — Activer WAL mode SQLite
**Fichier :** `backend/app/core/db.py`  
**Effort :** 15 minutes  
**Impact :** Lectures concurrent aux écritures, performances +30% sur reads  

```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
```

---

#### QW2 — Rate limiting sur les routes auth
**Fichier :** `backend/app/api/v1/routes/auth.py`  
**Effort :** 30 minutes  
**Impact :** Protège contre brute force password, sécurité basique  

```python
from fastapi import Request
from app.core.rate_limit import limiter

@router.post("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, payload: AuthRequest, db: Session = Depends(get_db)):
    ...

@router.post("/auth/register")
@limiter.limit("5/minute")
def register(request: Request, payload: AuthRequest, db: Session = Depends(get_db)):
    ...
```

---

#### QW3 — Fix bug seuils d'alerte non utilisés
**Fichier :** `backend/app/services/notification_service.py`  
**Effort :** 1 heure  
**Impact :** La feature "custom thresholds" dans Settings devient fonctionnelle  

```python
def check_and_notify_alerts(db: Session) -> list[Alert]:
    from app.models.settings import Settings
    settings = db.query(Settings).filter_by(id="global").first()
    high_threshold = getattr(settings, 'alert_threshold_warning', 80)
    critical_threshold = getattr(settings, 'alert_threshold_critical', 90)
    
    for provider in providers:
        if provider.usage_percent >= critical_threshold:
            # alert "critical"
        elif provider.usage_percent >= high_threshold:
            # alert "warning"
```

---

#### QW4 — Paralléliser les syncs avec asyncio.gather
**Fichier :** `backend/app/services/sync/sync_service.py`  
**Effort :** 2 heures  
**Impact :** Temps de sync 3x plus rapide (3 providers en parallèle)  

```python
async def sync_all_providers(db: Session) -> list[dict]:
    results = await asyncio.gather(
        _sync_openai(db),
        _sync_anthropic(db),
        _sync_elevenlabs(db),
        return_exceptions=True
    )
    # normaliser les exceptions en dicts d'erreur
    normalized = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append({"status": "error", "reason": str(r)})
        else:
            normalized.append(r)
    check_and_notify_alerts(db)
    return normalized
```

---

#### QW5 — Code splitting Vite + lazy loading pages
**Fichier :** `vite.config.ts`, `src/App.tsx`  
**Effort :** 2-4 heures  
**Impact :** Bundle initial ~120KB au lieu de 880KB (-85%)  

```typescript
// App.tsx
import { lazy, Suspense } from 'react';
const Index = lazy(() => import('./pages/Index'));
const ProviderDetail = lazy(() => import('./pages/ProviderDetail'));
const Alerts = lazy(() => import('./pages/Alerts'));

// vite.config.ts — manualChunks
manualChunks: {
  'vendor-react': ['react', 'react-dom', 'react-router-dom'],
  'vendor-charts': ['recharts'],
  'vendor-ui': ['@tanstack/react-query', 'sonner'],
}
```

---

#### QW6 — Ajouter healthcheck Docker et restart policy backend
**Fichier :** `docker-compose.prod.yml`  
**Effort :** 30 minutes  
**Impact :** Redémarrage automatique si le backend crash  

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/api/v1/health"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 10s
  restart: unless-stopped
  command: >
    uvicorn app.main:app
    --host 0.0.0.0
    --port 8001
    --workers 2         # au lieu de 1 (attention SQLite write locks)
    --access-log
```

---

#### QW7 — Tests unitaires pour notification_service
**Fichier :** `backend/tests/` → nouveau `test_notifications.py`  
**Effort :** 3 heures  
**Impact :** Couverture du bug seuils + régression protection  

```python
@pytest.mark.asyncio
async def test_high_usage_alert_created(db_session):
    provider = Provider(id="x", usage_percent=85, overage=0, ...)
    db_session.add(provider)
    db_session.commit()
    
    alerts = check_and_notify_alerts(db_session)
    assert len(alerts) == 1
    assert alerts[0].type == "High Usage"

@pytest.mark.asyncio
async def test_no_duplicate_alert(db_session):
    # Call twice → still 1 alert
    check_and_notify_alerts(db_session)
    alerts = check_and_notify_alerts(db_session)
    assert db_session.query(Alert).filter_by(type="High Usage").count() == 1
```

---

### 4.2 V1 Features (1-3 jours chacun)

#### V1.1 — Historical Usage Snapshots
**Effort :** 2 jours  
**Impact utilisateur :** Vision tendance réelle, graphiques journaliers vrais (vs simulés)  

**Implémentation :**
1. Nouveau modèle `UsageSnapshot` (provider_id, date, consumed, cost, snapshot_at)
2. Après chaque sync réussie → `upsert` snapshot du jour
3. Nouveau endpoint `GET /api/v1/providers/{id}/history?period=30d`
4. Frontend : remplacer `generate_daily_usage()` par l'endpoint réel
5. Graphique Recharts `<LineChart>` sur données réelles

---

#### V1.2 — Isolation multi-utilisateur (user_id FK)
**Effort :** 2-3 jours  
**Impact utilisateur :** Plusieurs utilisateurs avec leurs propres providers/budgets  

**Implémentation :**
1. Ajouter Alembic : `alembic init alembic`
2. Migration : `ALTER TABLE providers ADD COLUMN user_id TEXT`
3. Même pour alerts, adjustments, plans, settings
4. Toutes les routes : `db.query(Provider).filter_by(user_id=current_user.id)`
5. Settings → une ligne par user_id

---

#### V1.3 — Webhook/Email notifications sur alertes
**Effort :** 1-2 jours  
**Impact utilisateur :** Alertes reçues même sans être connecté à l'app  

**Implémentation :**
1. Ajouter `webhook_url` et `alert_email` dans le modèle Settings
2. Dans `check_and_notify_alerts()` : si nouvelle alerte → POST webhook JSON
3. Option email : `smtp` Python stdlib ou `resend` API
4. Frontend : page Settings avec champ webhook URL + test button

```python
# notification_service.py
import httpx

async def _fire_webhook(url: str, alert: Alert):
    payload = {
        "event": "alert.created",
        "provider": alert.provider_name,
        "type": alert.type,
        "severity": alert.severity.value,
        "description": alert.description,
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.warning(f"Webhook delivery failed: {e}")
```

---

#### V1.4 — Sync périodique automatique (APScheduler)
**Effort :** 1 jour  
**Impact utilisateur :** Données toujours fraîches sans action manuelle  

```python
# requirements.txt
apscheduler

# main.py lifespan
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_sync,
        'interval',
        hours=1,              # sync toutes les heures
        id='auto_sync',
        replace_existing=True
    )
    scheduler.start()
    yield
    scheduler.shutdown()

async def _scheduled_sync():
    db = SessionLocal()
    try:
        await sync_all_providers(db)
    finally:
        db.close()
```

---

#### V1.5 — Export CSV / JSON
**Effort :** 1 jour  
**Impact utilisateur :** Partage avec équipe, import dans Excel/sheets  

```python
# Nouveau endpoint
@router.get("/export/providers.csv")
def export_providers_csv(db: Session = Depends(get_db), ...):
    import csv, io
    providers = db.query(Provider).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "plan", "monthly_cost", "consumed", "usage_percent", "overage"])
    for p in providers:
        writer.writerow([p.id, p.name, p.plan, p.monthly_cost, p.consumed, p.usage_percent, p.overage])
    return Response(content=output.getvalue(), media_type="text/csv",
                   headers={"Content-Disposition": "attachment; filename=providers.csv"})
```

---

#### V1.6 — Alembic pour migrations de schéma
**Effort :** 1 jour  
**Impact :** Évolution du schéma sans perdre les données en production  

```bash
pip install alembic
alembic init alembic
# Configurer alembic.ini avec sqlalchemy.url
# Générer première migration depuis l'état actuel
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
Remplacer `create_tables()` dans `lifespan()` par `alembic upgrade head`.

---

### 4.3 V2 / Stratégique

#### V2.1 — Migration PostgreSQL + multi-workers
**Valeur :** Scalabilité, concurrence réelle, backups natifs (pg_dump)  

- Remplacer SQLite par PostgreSQL 16 dans docker-compose
- `uvicorn --workers 4` avec Gunicorn + uvicorn workers
- Connection pooling via `pgbouncer` ou SQLAlchemy pool
- `DATABASE_URL = "postgresql+asyncpg://..."` pour full async
- Hébergement : Supabase (free tier), Neon, ou pg Docker

---

#### V2.2 — Architecture AI Cost Intelligence
**Valeur :** Différenciation forte, valeur unique pour portfolio  

- ML model simple (Linear Regression) sur historique → prédiction fin de mois
- Détection d'anomalies sur consommation journalière (spike detection)
- Recommandations automatiques basées sur patterns : "Vous n'utilisez Gemini qu'en début de mois — downgrade possible"
- Score FinOps global (0-100) par provider et global

---

#### V2.3 — Tableau de bord multi-providers API enrichi
**Valeur :** Couverture plus large = plus utile pour les FinOps engineers  

| Provider | API possible |
|----------|-------------|
| Google Cloud AI | Cloud Billing API v1 |
| Azure OpenAI | Azure Cost Management API |
| Mistral AI | Dashboard API (si disponible) |
| Cohere | Usage API |
| Together AI | Usage API |
| Perplexity | API usage endpoint |

Architecture plugin : `BaseConnector` avec `fetch_usage() -> UsageResult`. Chaque provider implémente l'interface. Configuration via YAML.

---

#### V2.4 — Mobile-friendly + PWA
**Valeur :** Accès alertes depuis smartphone, notifications push  

- Manifest PWA + service worker (Vite PWA plugin)
- Push notifications browser (Web Push API)
- Responsive déjà en place (Tailwind), mais à optimiser sur mobile
- Biometrics auth via WebAuthn

---

#### V2.5 — API publique documentée + SDK
**Valeur stratégique :** Intégration dans d'autres outils, Zapier, etc.  

- FastAPI génère OpenAPI 3.0 automatiquement → `/docs` et `/redoc`
- Ajouter versioning API (`/api/v2/`)
- Python SDK (`pip install ai-finops-client`)
- Terraform provider (pour GitOps des budgets)

---

## Résumé exécutif

### Forces du projet

| Force | Détail |
|-------|--------|
| **Architecture propre** | FastAPI + SQLAlchemy bien structurés, séparation models/schemas/services |
| **Auth solide** | JWT HS256, passwords bcrypt/pbkdf2, HTTPBearer |
| **Tests backend sérieux** | 36 tests async, fixtures bien organisées, mocks httpx |
| **UI moderne** | ShadCN + Tailwind, responsive, i18n FR/EN |
| **Deploy Docker** | Traefik + Let's Encrypt, bind mount pour DB |
| **Sync réels** | OpenAI et ElevenLabs avec vrais APIs |
| **Error handling sync** | Try/except + status="error" en DB |

### Faiblesses critiques

| Faiblesse | Fichier | Impact |
|-----------|---------|--------|
| **Pas de WAL SQLite** | `core/db.py` | Corruption possible sous charge |
| **Données historiques simulées** | `dashboard_service.py:28` | Dashboard non fiable |
| **Bug seuils alertes ignorés** | `notification_service.py:8-9` | Feature cassée |
| **Pas de retry sync** | `sync_service.py` | Sync fragile |
| **Bundle 880KB** | `dist/assets/` | UX lente sur mobile |
| **Multi-user fictif** | Tous les modèles | Données partagées |
| **Token en localStorage** | `auth.ts` | XSS vulnérabilité |
| **Anthropic sync = no-op** | `anthropic_sync.py` | Données manuelles marquées "synced" |
| **Pas de sync périodique** | `main.py` | Données stales entre syncs manuels |

### Priorité des actions

```
Semaine 1 (Quick Wins) :
  ✅ WAL SQLite (15 min)
  ✅ Rate limit auth (30 min)
  ✅ Fix bug seuils alertes (1h)
  ✅ Paralléliser syncs (2h)
  ✅ Code splitting Vite (4h)

Mois 1 (V1 Features) :
  📦 Usage snapshots historiques
  📦 Sync périodique APScheduler
  📦 Export CSV
  📦 Alembic migrations

Mois 2-3 (V2 Stratégique) :
  🚀 Migration PostgreSQL
  🚀 Isolation multi-tenant
  🚀 Notifications webhook/email
  🚀 AI Cost Intelligence layer
```

---

*Analyse générée le 2026-04-06 par Jayvis — OpenClaw subagent*  
*Basée sur l'inspection complète de 35 fichiers source Python/TypeScript*
