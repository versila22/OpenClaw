# Analyse technique, architecturale et fonctionnelle — LIMA App
**Date :** 2026-04-06  
**Analysé par :** Jayvis (subagent)  
**Scope :** `/data/.openclaw/workspace/lima/` (backend FastAPI) + `/data/.openclaw/workspace/lima-app/` (frontend React/TS)  
**Objectif :** Plan d'action pour un projet portfolio, niveau entretien sénior.

---

## 1. Architecture

### 1.1 Diagramme de flux de données

```
┌─────────────────────────────────────────────────────────────────────┐
│                          BROWSER (SPA)                              │
│                                                                     │
│  React + TanStack Query + React Router DOM                          │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐  │
│  │ AuthContext  │  │ Pages/         │  │ lib/api.ts              │  │
│  │ (JWT, user) │  │ Components     │  │ (fetch wrapper, ApiError)│  │
│  └──────┬───────┘  └───────┬───────┘  └──────────┬──────────────┘  │
│         │                  │                     │                  │
│         └──────────────────┴─────────────────────┘                  │
│                            │ HTTP / JSON                            │
└────────────────────────────┼────────────────────────────────────────┘
                             │ (Bearer JWT)
┌────────────────────────────▼────────────────────────────────────────┐
│                         FastAPI (ASGI)                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Middleware                                                   │   │
│  │  - CORSMiddleware                                            │   │
│  │  - ActivityTrackerMiddleware (async fire-and-forget)         │   │
│  │  - SlowAPI rate limiter (IP-based)                           │   │
│  └───────────────────────────┬──────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Routers (présentation / contrôleurs)                           ││
│  │  auth · members · seasons · events · venues                   ││
│  │  alignments · commissions · show_plans · settings · admin     ││
│  └──────────────────────────┬──────────────────────────────────────┘│
│                             │ Depends(get_db)                       │
│  ┌──────────────────────────▼──────────────────────────────────────┐│
│  │ Services (métier)                                              ││
│  │  auth_service · alignment_service · import_service            ││
│  │  email_service                                                ││
│  └──────────────────────────┬──────────────────────────────────────┘│
│                             │ SQLAlchemy async ORM                  │
│  ┌──────────────────────────▼──────────────────────────────────────┐│
│  │ Models (données)                                               ││
│  │  Member · Season · Event · Venue · Alignment · ShowPlan       ││
│  │  MemberSeason · MemberCommission · Commission · ActivityLog   ││
│  └──────────────────────────┬──────────────────────────────────────┘│
│                             │                                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │ asyncpg
                    ┌─────────▼──────────┐
                    │  PostgreSQL 16      │
                    │  (Railway / local)  │
                    └────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  SMTP (aiosmtplib) │
                    │  (activation mail,  │
                    │   reset password)   │
                    └────────────────────┘
```

### 1.2 Séparation des couches

| Couche | Fichiers | Qualité |
|--------|----------|---------|
| **Présentation** | `app/routers/*.py` | ✅ Responsabilité unique, DI correcte |
| **Métier** | `app/services/*.py` | ⚠️ Partielle — beaucoup de logique reste dans les routers |
| **Données** | `app/models/*.py` + `app/database.py` | ✅ Modèles propres, async correct |
| **Schemas** | `app/schemas/*.py` | ✅ Pydantic v2, séparation Create/Read/Update |

**Observation :** `alignment_service.py` et `auth_service.py` sont bien factorisés. Mais `events.py`, `members.py`, `seasons.py`, `commissions.py`, `venues.py` mélangent encore logique métier et contrôleur (queries SQLAlchemy directement dans le router, sans service dédié). C'est un défaut d'uniformité, pas un défaut bloquant.

### 1.3 Points de couplage forts / dépendances fragiles

#### 🔴 CRITIQUE : `settings.py` — stockage JSON dans `/tmp`
**Fichier :** `app/routers/settings.py`, ligne 22  
```python
SETTINGS_FILE = Path("/tmp/lima_settings.json")
```
- `/tmp` est effacé au redémarrage du conteneur sur Railway (et tout service cloud)
- Les settings sont perdus à chaque redeploy
- Pas de thread-safety : deux requêtes concurrentes peuvent corrompre le fichier
- **Couplage fort** entre le routeur et le filesystem — aucune abstraction

#### 🔴 CRITIQUE : `ActivityTrackerMiddleware` — `asyncio.create_task` sans loop guard
**Fichier :** `app/middleware/activity_tracker.py`, ligne 48
```python
asyncio.create_task(self._write_activity_log(activity_data))
```
- `create_task` peut lever `RuntimeError` si la boucle d'événements n'est pas active (ex. tests unitaires, shutdown)
- Les tasks orphelines peuvent ne pas être awaited avant la fermeture du serveur → perte de logs
- Pas de backpressure : sous forte charge, accumulation de tasks non résolues

#### 🟡 MOYEN : Import CSV en boucle (N+1 writes)
**Fichier :** `app/services/import_service.py`, ligne 180–260  
Pour chaque email dans le CSV, deux `execute()` sont lancés (SELECT Member + SELECT MemberSeason), puis un INSERT. Pour 50 membres = 150+ requêtes DB. Acceptable en V0 mais à corriger avant la montée en charge.

#### 🟡 MOYEN : `alignment_service.add_events_to_alignment` — N requêtes SELECT par event
**Fichier :** `app/services/alignment_service.py`, lignes 46–68  
```python
for i, event_id in enumerate(event_ids):
    ev_result = await db.execute(select(Event).where(Event.id == event_id))  # 1 requête par event
    ae_result = await db.execute(select(AlignmentEvent).where(...))           # 1 requête par event
```
Pour une grille de 10 événements = 20 requêtes. Devrait utiliser `WHERE id IN (...)`.

#### 🟡 MOYEN : `show_plans.py` — `list_show_plans` sans eager loading
**Fichier :** `app/routers/show_plans.py`, lignes 24–50  
Pas de `selectinload` pour `ShowPlan.event` ou `ShowPlan.created_by_member`. La réponse JSON ne les inclut pas (schemas ne les demandent pas), donc pas de vrai N+1 en sortie — mais si le schema évolue, le risque est immédiat.

#### 🟡 MOYEN : CabaretOrganizer entièrement déconnecté du backend
**Fichier :** `lima-app/src/pages/CabaretOrganizer.tsx`  
La page génère des plans avec `generateMockPlan()` (lib purement client, `// Simulate API call delay`). Les plans sont sauvés en localStorage uniquement. Aucun appel API. Le modèle `ShowPlan` et le routeur `/show-plans` existent côté backend mais ne sont jamais utilisés par le frontend.

#### 🟡 MOYEN : `member.is_active = True` par défaut à la création manuelle
**Fichier :** `app/routers/members.py`, ligne 99-112 + `app/models/member.py`, ligne 33  
Un nouveau membre créé manuellement est `is_active=True` dès la création, avant même qu'il ait activé son compte via email. Il peut donc se connecter si quelqu'un connaît son email et devine le mot de passe — sauf que `password_hash` est `NULL` jusqu'à l'activation, donc la connexion échoue correctement. Mais sémantiquement, `is_active` devrait être `False` jusqu'à l'activation.

### 1.4 Patterns async — SQLAlchemy async : est-ce utilisé correctement ?

**✅ Ce qui est correct :**
- `create_async_engine` + `async_sessionmaker` + `AsyncSession` partout
- `async with AsyncSessionLocal() as session` en contexte
- `await db.execute(select(...))` cohérent
- `expire_on_commit=False` sur la session — évite les lazy loads post-commit (pattern correct)
- `selectinload` utilisé dans les bons endroits pour éviter les lazy loads async

**⚠️ Ce qui est problématique :**

1. **`func.now()` vs `server_default`** dans plusieurs models (`Member`, `Season`, `Venue`, `ActivityLog` a les deux)  
   - `default=func.now()` = évalué côté Python à l'instanciation de l'objet, avant flush
   - `server_default=func.now()` = évalué par la DB au moment de l'INSERT  
   - Pour `ActivityLog.created_at`, les deux coexistent : `DateTime(timezone=True), server_default=func.now()` (migration) mais `default=func.now()` dans le modèle Python — incohérence potentielle

2. **`asyncio.create_task` dans middleware** (voir §1.3) — risque en ASGI

3. **Timezone handling inconsistent :**  
   `auth_service._utcnow_naive()` retourne du datetime naive intentionnellement pour SQLite en tests. Mais en prod avec PostgreSQL, les colonnes `TIMESTAMPTZ` stockent avec timezone. Mélange naive/aware lors des comparaisons :  
   ```python
   if member.activation_expires_at and member.activation_expires_at < _utcnow_naive():
   ```
   Si PostgreSQL retourne un datetime aware et qu'on compare avec naive → `TypeError` ou comparaison silencieusement incorrecte selon le driver.

4. **`await db.flush()` vs `await session.commit()`** — le flush est fait dans les routers/services, le commit est dans `get_db()` dependency. C'est le bon pattern pour une UoW (Unit of Work), mais aucun rollback explicite au niveau service — tout repose sur le `except Exception: rollback` dans `get_db()`. 

### 1.5 Contrat Frontend/Backend — risques de drift

| Domaine | État | Risque |
|---------|------|--------|
| Types TS vs schemas Pydantic | ✅ Alignés sur l'essentiel | Bas |
| `DailyActiveUserStat.day` (backend: `date`) vs `DailyActiveUserStat.date` (frontend: `string`) | 🔴 Champ renommé | **Drift actuel** — voir §2.6 |
| `LoginAttemptRead` : pas de champ `email`, `name`, `success` | 🔴 Manquant | **Drift actuel** — frontend compense dans `normalizeLoginAttempts()` |
| `EventRead` : pas de relation `venue` ou `alignments` | ✅ Intentionnel | - |
| `GET /events/{id}/cast` | 🔴 Endpoint inexistant | **Erreur silencieuse** dans EventDetailDialog |
| `settings` : backend retourne `Dict[str, Any]`, frontend type `AppSettings` | ⚠️ Loose typing | Bas si schema stable |

---

## 2. Qualité Technique

### 2.1 Risques N+1

| Lieu | Description | Sévérité |
|------|-------------|----------|
| `alignment_service.add_events_to_alignment` (l.46-68) | 2 SELECTs par event_id dans une boucle | 🟡 Moyen |
| `import_service.import_csv_helloasso` (l.180+) | SELECT + upsert pour chaque email (50 membres = ~150 req.) | 🟡 Moyen |
| `commissions.py` → `list_commissions` | Retourne des `Commission` sans charger `member_commissions` — ok car pas dans le schema de réponse | ✅ OK |
| `members.py` → `list_members` | Retourne `MemberSummary` (pas de member_seasons) — pas de lazy load déclenché | ✅ OK |
| `show_plans.py` → `list_show_plans` | Pas de selectinload sur `event` / `created_by_member` — ok car pas dans le schema | ✅ OK actuel |
| `get_current_user` (deps.py) | Chaque requête authentifiée fait un SELECT Member + selectinload member_seasons | ⚠️ Cumulatif |

**Note sur `get_current_user` :** Il charge `member_seasons` à chaque requête via `selectinload`. Pour la plupart des endpoints, `member_seasons` n'est pas utilisé — c'est du chargement inutile. Acceptable en V0, à optimiser avec un cache JWT ou en retirant le `selectinload` de `get_current_user` (le remettre uniquement dans les endpoints qui en ont besoin).

### 2.2 Index manquants

Les indexes existants couvrent bien les requêtes les plus fréquentes. Voici les manques :

| Table | Colonne | Requête concernée | Priorité |
|-------|---------|------------------|----------|
| `members` | `email` | `WHERE email = ?` (login, activation, reset, import) | 🔴 **CRITIQUE** — unique constraint existe mais pas d'index explicite (le UNIQUE crée un index implicite en PostgreSQL, donc OK) |
| `members` | `activation_token` | `WHERE activation_token = ?` | 🟡 Moyen — table petite |
| `members` | `reset_token` | `WHERE reset_token = ?` | 🟡 Moyen |
| `member_seasons` | `season_id` | `JOIN member_seasons WHERE season_id = ?` (list_members avec filtre saison) | 🟡 Moyen — pas d'index dédié |
| `member_seasons` | `member_id` | Lookup fréquent via FK | 🟡 Moyen — FK pas nécessairement indexée sur PostgreSQL |
| `alignments` | `season_id` | `WHERE season_id = ?` | 🟡 Moyen |
| `member_commissions` | `member_id`, `season_id` | Lookups fréquents | 🟡 Moyen |
| `activity_logs` | `(method, path)` composite | Requête login filter : `WHERE method='POST' AND path IN (...)` | 🟡 Moyen |

**Bonne nouvelle :** `events`, `alignment_assignments`, `activity_logs`, `show_plans` ont des indexes bien posés.

### 2.3 Lacunes de gestion d'erreurs

#### `/auth/reset-password` — pas de rate limiting
**Fichier :** `app/routers/auth.py`, ligne 107  
```python
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(...)
```
Pas de `@limiter.limit(...)` alors que `/auth/login` (5/min) et `/auth/forgot-password` (3/min) en ont. Un attaquant peut bruteforcer des tokens (32 bytes URL-safe → en pratique impossible, mais bonne pratique manquante).

#### `/auth/activate` — pas de rate limiting POST
**Fichier :** `app/routers/auth.py`, ligne 67  
```python
@router.post("/activate", ...)
@limiter.limit("5/minute")
```
OK — rate limiting présent.

#### `events.py` — pas de validation que `end_at > start_at`
**Fichier :** `app/schemas/event.py` — `EventCreate`/`EventUpdate` n'ont pas de `@model_validator` pour vérifier `end_at > start_at`. Un événement peut avoir une fin avant son début.

#### `seasons.py` — pas de vérification unicité du nom
**Fichier :** `app/routers/seasons.py` — deux saisons peuvent avoir le même `name` (ex. "2025-2026" deux fois).

#### `import_service.py` — gestion d'erreurs trop permissive
**Fichier :** `app/services/import_service.py`, ligne 220  
```python
except Exception as exc:
    report.errors.append(f"Erreur membre {email}: {exc}")
```
Un `IntegrityError` (FK manquante, violation de contrainte) est silencieusement absorbé et la transaction continue. Cela peut laisser la DB dans un état partiellement cohérent.

#### `commissions.py` — DELETE sans validation `season_id`
**Fichier :** `app/routers/commissions.py`, ligne 57  
```python
async def remove_member_from_commission(
    commission_id: UUID,
    member_id: UUID,
    season_id: UUID,  # Query parameter — pas dans le path
```
`season_id` est un query parameter mais n'est pas documenté comme required dans l'URL path. Facile à oublier côté client, résulte en 422 cryptique.

#### `show_plans.py` — `list_show_plans` sans season fallback cohérent
**Fichier :** `app/routers/show_plans.py`, lignes 39–50  
Si aucune saison courante n'existe (`current_season is None`), la query retourne **tous** les plans sans filtre de saison — comportement inattendu, peut exposer des données d'anciennes saisons.

### 2.4 Couverture de tests — chemins critiques

**Tests existants (1413 lignes au total) — bonne base :**

| Module testé | Couverture observée | Manques |
|-------------|---------------------|---------|
| `test_auth.py` (210 l) | Login, activation, reset, change_password, me, update_me | ✅ Bon |
| `test_members.py` (157 l) | CRUD, import CSV partiel, roles | ⚠️ Import CSV non testé end-to-end avec vrais fichiers |
| `test_alignments.py` (174 l) | CRUD, events, assign/unassign, publish | ✅ Bon |
| `test_events.py` (166 l) | CRUD, filters, visibility | ✅ Bon |
| `test_seasons.py` (102 l) | CRUD, is_current toggle | ✅ Bon |
| `test_admin_activity.py` (110 l) | Recent, stats, logins | ⚠️ Partiel |
| `test_venues.py` (59 l) | CRUD basique | ✅ Suffisant |
| `test_commissions.py` (50 l) | List, add/remove member | ✅ Suffisant |
| `test_show_plans.py` (67 l) | CRUD basique | ⚠️ Pas de test JSON config |
| `test_settings.py` (25 l) | GET/PUT basique | ⚠️ Très léger |

**Chemins critiques NON testés :**
- Import CSV avec fichiers réels HelloAsso (encoding BOM, délimiteur `;`, colonnes spécifiques)
- Import Excel calendrier
- Email de réinitialisation end-to-end (SMTP mocké)
- `activation_token` expiré vs valide avec différence de 1 seconde (edge case timezone)
- Comportement de `show_plans.list` quand aucune saison courante
- `AlignmentService.add_events_to_alignment` avec un `event_id` inexistant dans une liste mixte
- Concurrence : deux admins créent une saison avec `is_current=True` simultanément
- Tests de performance (N+1 détection)

### 2.5 Risques de dépendances

**Backend (`requirements.txt`) :**

| Package | Version | Risque |
|---------|---------|--------|
| `fastapi==0.111.0` | Pas la dernière (0.115+) | 🟡 Mineur — pas de CVE connue |
| `python-jose[cryptography]==3.3.0` | Dernière release 2022 — **projet peu maintenu** | 🔴 **À remplacer** par `PyJWT` + `cryptography` |
| `passlib[bcrypt]==1.7.4` | Dernière release 2022 — **bcrypt deprecation warning** en Python 3.12 | 🟡 Fonctionnel, surveiller |
| `sqlalchemy==2.0.30` | Version stable (2.0.x) | ✅ OK |
| `pydantic==2.7.1` | Pas la dernière (2.10+) | 🟡 Mineur |
| `uvicorn[standard]==0.29.0` | Pas la dernière (0.34+) | 🟡 Mineur |
| `openpyxl==3.1.2` | OK | ✅ |
| `aiosmtplib==3.0.2` | Récent | ✅ |

**⚠️ `python-jose` est le risque le plus sérieux :** plusieurs CVE historiques sur python-jose, projet abandonné. Recommandation : migrer vers `python-jwt` ou `PyJWT>=2.8`.

**Frontend (`package.json`) :**  
Dependabot a déjà détecté plusieurs alerts (branches `dependabot/*` visibles dans le git log) :
- `flatted`, `lodash`, `rollup`, `yaml` — patches de sécurité disponibles
- `lucide-react==0.462.0` — pas la dernière mais stable
- Stack React/Vite/TypeScript récente ✅

### 2.6 Failles de sécurité résiduelles

#### 🔴 Drift schéma `DailyActiveUserStat` : champ `day` vs `date`
**Backend** (`app/schemas/activity.py`) :
```python
class DailyActiveUserStat(BaseModel):
    day: date
    unique_users: int
```
**Frontend** (`types/index.ts`) :
```typescript
export interface DailyActiveUserStat {
  date: string;  // ← champ renommé
  count: number; // ← champ renommé
}
```
La fonction `normalizeDailyActiveUsers()` dans `api.ts` tente de réconcilier les deux :
```typescript
date: String(obj.date ?? obj.day ?? obj.label ?? ""),
count: Number(obj.count ?? obj.users ?? obj.value ?? 0),
```
C'est du code défensif pour combler un vrai drift. Le graphique DAU affichera des données vides si l'API change.

#### 🔴 `GET /events/{event_id}/cast` — Endpoint manquant
**Fichier :** `lima-app/src/pages/Agenda.tsx`, ligne 688  
```typescript
queryFn: () => api.get<CastMember[]>(`/events/${event.id}/cast`),
```
Cet endpoint n'existe pas dans le backend. La requête retourne systématiquement **404** (silencieux dans `EventDetailDialog` — `cast.length === 0` donc rien ne s'affiche). Le "casting" stocké dans `event.notes` via `CAST_DATA` JSON n'est jamais exposé via API — il est lu/écrit directement depuis le champ `notes` dans le frontend. L'alignement (`AlignmentAssignment`) est complètement séparé et jamais connecté à l'agenda view.

#### 🔴 Bug UI : Statut membre toujours "A" dans la liste
**Fichier :** `lima-app/src/pages/Members.tsx`, ligne 280  
```tsx
<StatusBadge status={m.app_role === "admin" ? "A" : "A"} />
```
Les deux branches retournent `"A"`. Jamais le vrai `player_status` affiché. Le statut (M/C/L/A) n'est pas dans `MemberSummary` (résultat de `GET /members`) — il faudrait soit :
1. Ajouter `player_status` à `MemberSummary` pour la saison courante
2. Ou faire un appel `GET /members/{id}` au clic pour avoir `MemberRead` avec `member_seasons`

#### 🟡 Rate limiting — couverture partielle
- ✅ `POST /auth/login` : 5/min
- ✅ `POST /auth/activate` : 5/min  
- ✅ `POST /auth/forgot-password` : 3/min
- ❌ `POST /auth/reset-password` : **pas de rate limit**
- ❌ `POST /members` (création manuelle) : **pas de rate limit**
- ❌ `POST /members/import` (upload CSV) : **pas de rate limit** — risque de DoS

#### 🟡 Tokens d'activation exposés dans les réponses API
**Fichier :** `app/routers/members.py`, ligne 199  
```python
return {"detail": "Email d'activation envoyé", "token": token}
```
`resend_activation` retourne le token en clair dans la réponse JSON. C'est pratique pour le dev mais dangereux si des logs HTTP sont capturés. En prod, ne pas retourner le token.

#### 🟡 CORS en développement
**Fichier :** `app/config.py`, ligne 15  
```python
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://localhost:5173"
```
Si `CORS_ORIGINS` n'est pas défini en prod, les origines locales sont refusées mais l'origine de prod doit être explicitement dans la variable d'env. C'est correct mais un oubli de config déploiement suffit à casser tout le frontend.

#### 🟡 Settings dans `/tmp` — perte au redémarrage
Voir §1.3 — critique pour la prod Railway.

#### 🟡 `Authorization: Bearer` dans les logs d'activité
**Fichier :** `app/middleware/activity_tracker.py`, méthode `_extract_user_id`  
Le middleware décode le JWT depuis `Authorization: Bearer`. Le token n'est pas loggué (bon). Mais `query_params` est loggué brut — si un token se retrouve dans un query param (mauvaise pratique mais possible), il serait stocké en DB.

---

## 3. Analyse Fonctionnelle

### 3.1 Cas d'usage non couverts pour un membre LIMA typique

| Besoin | État actuel | Impact |
|--------|-------------|--------|
| Voir dans quel(s) événement(s) je suis aligné cette saison | ❌ Pas de vue "mon planning" | 🔴 Critique — use case principal |
| Recevoir une notification quand je suis ajouté à une grille | ❌ Pas de système de notification | 🔴 Critique |
| Voir les infos de contact des autres membres | ❌ MemberSummary sans téléphone | 🟡 Moyen |
| Voir les membres d'une commission | ❌ `CommissionRead` sans `member_commissions` | 🟡 Moyen |
| Connaître le lieu d'un événement (adresse, contact) | ⚠️ `venue_id` dans Event mais pas de relation chargée dans `EventRead` | 🟡 Moyen |
| S'inscrire sur liste d'attente / déclarer une indisponibilité | ❌ Absent | 🟡 Moyen |
| Voir l'historique de mes cotisations | ⚠️ `member_seasons` accessible mais pas surfacé dans UI | 🟡 Moyen |
| Accéder au plan de spectacle de la soirée du soir | ⚠️ Plans existent en DB mais `CabaretOrganizer` est 100% local | 🟡 Moyen |
| Télécharger un plan en PDF | ❌ Absent | 🟡 Moyen |
| Voir les résultats de matchs passés | ❌ Pas de modèle `MatchResult` | 🟠 V2 |
| Gestion des présences/absences aux entraînements | ❌ Absent | 🟠 V2 |
| Chat / communication interne | ❌ Absent | 🟠 V2 |

### 3.2 Flux utilisateur incomplets

#### 🔴 Activation email — comportement is_active incohérent
**Flux actuel :**
1. Admin crée un membre → `is_active=True` (!) + `activation_token` généré + email envoyé
2. Membre clique le lien → `is_active=True` (déjà), `password_hash` set, token cleared

**Problème :** Un membre créé manuellement est techniquement `is_active=True` avant d'avoir activé. S'il n'a pas reçu l'email et qu'un admin tente de se connecter avec son email (test), `authenticate_member` retourne `None` à cause du `password_hash=None` → 401. Mais c'est un accident de conception, pas une protection intentionnelle.

**Flux attendu :**
1. Création → `is_active=False` jusqu'à l'activation

#### 🔴 Import CSV — pas d'envoi d'email d'activation aux nouveaux membres importés
**Fichier :** `app/services/import_service.py`, lignes 199–215  
Les membres créés par import CSV sont créés avec `is_active=True` et **sans** `activation_token`. Ils ne peuvent jamais se connecter car `password_hash=None`.
```python
member = Member(
    email=email,
    first_name=first_name,
    # ...
    # Pas d'activation_token !
    # is_active reste True par défaut
)
```
**Conséquence :** ~55 membres importés depuis HelloAsso ne peuvent pas accéder à l'app.

#### 🟡 Reset password — jamais testé en prod
Le flow fonctionne en tests unitaires (`test_auth.py`) mais n'a jamais été testé avec un vrai SMTP. Le `SMTP_HOST` est vide par défaut → `send_email` logge un warning et fait un `return` sans erreur. L'utilisateur reçoit un 200 mais jamais l'email.

#### 🟡 `CabaretOrganizer` — déconnecté du backend
La page principale de l'app pour les joueurs (`/cabaret`) génère des plans avec `generateMockPlan()` (algo client). Les plans sont sauvés dans `localStorage` (`usePlanHistory`). Le backend a un modèle `ShowPlan` complet avec `config` JSON et `generated_plan` text. Les deux systèmes ne sont jamais synchronisés.

#### 🟡 Agenda — casting non persisté via API
Le formulaire de création/modification d'événement dans l'agenda permet de saisir un "casting" (joueurs, DJ, MC, arbitre). Ces données sont sérialisées dans `event.notes` sous le format `--- CAST_DATA --- {...}`. Elles ne sont pas exposées via une API dédiée. `EventDetailDialog` tente de charger `GET /events/{id}/cast` qui n'existe pas → 404 silencieux.

### 3.3 Données en DB non surfacées dans l'UI

| Données | Modèle | UI actuelle | Potentiel |
|---------|--------|-------------|-----------|
| `member_seasons.player_status` (M/C/L/A) | `MemberSeason` | ❌ Bug ligne 280 Members.tsx | Afficher dans la liste membres |
| `member_seasons.membership_fee` + `player_fee` | `MemberSeason` | ❌ Jamais affiché | Dashboard cotisations |
| `member_seasons.asso_role` (co-prez, etc.) | `MemberSeason` | ❌ Jamais affiché | Trombinoscope |
| `member_seasons.helloasso_ref` | `MemberSeason` | ❌ Jamais affiché | Admin finances |
| `member_commissions` (membre × commission × saison) | `MemberCommission` | ❌ Aucune vue | Page commissions |
| `alignment_assignments` (rôles par événement) | `AlignmentAssignment` | ❌ Aucune vue dans Agenda | Vue "mon planning" |
| `venue.contact_info` | `Venue` | ❌ Aucune vue | Fiche lieu |
| `event.away_city` + `event.away_opponent` | `Event` | ❌ Non affiché dans Agenda | Badge "déplacement" |
| `show_plans` en DB | `ShowPlan` | ❌ CabaretOrganizer utilise localStorage | Historique partagé |
| `activity_logs` analytics | `ActivityLog` | ✅ Page Stats (admin) | - |
| `event.visibility` | `Event` | ❌ Pas affiché dans le calendrier | Différenciation visuelle |

---

## 4. Propositions concrètes

### Quick wins (< 1 jour chacun)

#### QW-1 — Corriger le bug "StatusBadge always A" dans Members.tsx
**Effort :** 2h | **Impact :** Affichage correct du statut joueur pour tous les membres

**Fichier :** `lima-app/src/pages/Members.tsx`, ligne 280  
Problème : `MemberSummary` ne contient pas `player_status`. Solution simple : ajouter un champ calculé.

Option A — Ajouter `player_status` à `MemberSummary` (backend + frontend) :
```python
# app/schemas/member.py
class MemberSummary(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    app_role: str
    is_active: bool
    current_player_status: Optional[str] = None  # "M" | "C" | "L" | "A"
```
Et dans `list_members`, joindre `MemberSeason` pour la saison courante.

Option B (plus simple, sans modifier le backend) : ne pas afficher le statut dans la liste principale, l'afficher dans le détail au clic.

---

#### QW-2 — Fixer le drift `DailyActiveUserStat.day` vs `.date`
**Effort :** 1h | **Impact :** Graphique DAU fonctionnel en prod

**Fichiers :** `app/schemas/activity.py` OU `lima-app/src/types/index.ts`  
Choisir une convention et l'aligner. Recommandation : harmoniser le frontend sur le schéma backend.

```typescript
// types/index.ts
export interface DailyActiveUserStat {
  day: string;         // ← renommer pour matcher le backend
  unique_users: number; // ← idem
}
```

---

#### QW-3 — Ajouter rate limiting sur `/auth/reset-password`
**Effort :** 30min | **Impact :** Sécurité

```python
# app/routers/auth.py
@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password(request: Request, ...):
```

---

#### QW-4 — Ne pas retourner le token dans la réponse `resend-activation`
**Effort :** 30min | **Impact :** Sécurité

**Fichier :** `app/routers/members.py`, ligne 199  
```python
# Avant
return {"detail": "Email d'activation envoyé", "token": token}
# Après
return {"detail": "Email d'activation envoyé"}
```
Le token ne doit voyager que par email.

---

#### QW-5 — Migrer settings de `/tmp` vers DB ou table de config
**Effort :** 3-4h | **Impact :** Perte de données en prod éliminée

Créer une table `app_settings` simple (key/value) ou utiliser une single-row config table :

```python
# app/models/app_config.py
class AppConfig(Base):
    __tablename__ = "app_config"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

Migration Alembic + réécriture de `settings.py` pour utiliser la DB async.

---

#### QW-6 — Corriger `is_active` à `False` à la création de membre
**Effort :** 2h | **Impact :** Cohérence sémantique + sécurité

**Fichier :** `app/routers/members.py`, lignes 99-112  
```python
member = Member(
    email=data.email.lower(),
    # ...
    is_active=False,  # ← False jusqu'à activation
)
```
Et dans `auth_service.activate_account` : `member.is_active = True` (déjà fait ✅)

Vérifier que le test `test_create_member_success` est mis à jour :  
```python
assert body["is_active"] is False  # (was True)
```

---

#### QW-7 — Ajouter `end_at > start_at` validator dans EventCreate
**Effort :** 1h | **Impact :** Intégrité des données

```python
# app/schemas/event.py
@model_validator(mode="after")
def end_after_start(self) -> "EventCreate":
    if self.end_at and self.start_at and self.end_at <= self.start_at:
        raise ValueError("end_at doit être postérieure à start_at")
    return self
```

---

#### QW-8 — Afficher `away_city` et `away_opponent` dans l'Agenda
**Effort :** 2h | **Impact :** UX — déplacements visibles dans le calendrier

**Fichier :** `lima-app/src/pages/Agenda.tsx` — dans les chips du calendrier, ajouter un indicateur "✈️" pour `is_away=true`.

---

### Features V1 (1-3 jours chacune)

#### V1-1 — Vue "Mon planning" pour les joueurs
**Effort :** 2 jours | **Impact utilisateur :** Critique — use case n°1

L'absence de cette vue est le trou fonctionnel le plus important. Un joueur doit pouvoir voir d'un coup d'œil les événements où il est aligné.

**Backend :** Créer un endpoint `GET /members/me/assignments` :
```python
# retourne la liste des AlignmentAssignment du membre courant
# avec les événements correspondants eager-loaded
@router.get("/me/assignments", response_model=List[MyAssignmentRead])
async def get_my_assignments(
    season_id: Optional[UUID] = Query(None),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AlignmentAssignment)
        .options(
            selectinload(AlignmentAssignment.event),
            selectinload(AlignmentAssignment.alignment),
        )
        .join(Alignment)
        .where(
            AlignmentAssignment.member_id == current_user.id,
            Alignment.status == "published",
        )
    )
    if season_id:
        query = query.where(Alignment.season_id == season_id)
    result = await db.execute(query)
    return result.scalars().all()
```

**Frontend :** Nouvelle page `/mon-planning` ou section dans l'Agenda — liste des événements avec le rôle assigné (JR/DJ/MJ_MC/AR/COACH).

---

#### V1-2 — Connecter CabaretOrganizer au backend (ShowPlan API)
**Effort :** 1.5 jours | **Impact utilisateur :** Haut — plans persistés et partagés

**Actuellement :** `generateMockPlan()` est 100% client, stocké en localStorage.  
**Cible :** `POST /show-plans` pour créer, `GET /show-plans` pour lister, plans visibles par tous les admins.

Changements nécessaires :
1. `CabaretOrganizer.tsx` : remplacer `generateMockPlan()` et `usePlanHistory()` par des mutations TanStack Query
2. `ShowPlanCreate` : mapper `CabaretFormData` → `ShowPlanCreate` (title, show_type, config, generated_plan)
3. `PlanHistory.tsx` : charger depuis `GET /show-plans` au lieu du hook localStorage

---

#### V1-3 — Endpoint `GET /events/{event_id}/cast` + migration casting vers AlignmentAssignment
**Effort :** 2 jours | **Impact utilisateur :** Moyen-haut — casting visible en UI

**Option A (rapide) :** Créer l'endpoint qui parse `event.notes` pour extraire le CAST_DATA JSON :
```python
@router.get("/{event_id}/cast", response_model=List[CastMemberRead])
async def get_event_cast(event_id: UUID, db: ..., _: Member = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event or not event.notes:
        return []
    # Parser le CAST_DATA JSON depuis event.notes
    return parse_cast_from_notes(event.notes)
```

**Option B (propre) :** Utiliser les `AlignmentAssignment` existants pour afficher le casting dans l'Agenda. Plus de travail mais élimine la duplication.

---

#### V1-4 — Envoi email d'activation pour les membres importés via CSV
**Effort :** 1 jour | **Impact utilisateur :** Critique pour l'onboarding

**Fichier :** `app/services/import_service.py`

Après création d'un nouveau membre :
```python
if member is None:
    member = Member(
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=False,  # ← correction QW-6
        # ...
    )
    db.add(member)
    await db.flush()
    token = await auth_service.generate_activation_token(db, member)
    # Appel email en batch ou fire-and-forget
    report.created += 1
    report.activation_tokens[email] = token  # pour retourner à l'admin
```

Note : les emails ne doivent pas être envoyés dans la transaction DB (les envoyer après le flush). Utiliser une liste de post-flush callbacks.

---

#### V1-5 — Afficher `player_status`, `asso_role`, commissions dans le profil membre
**Effort :** 1.5 jours | **Impact utilisateur :** Moyen — lisibilité de l'annuaire

**Backend :** Endpoint `GET /members/{member_id}/full` ou enrichir `MemberRead` avec commissions :
```python
class MemberReadFull(MemberRead):
    commissions: List[CommissionWithSeasonRead] = []
```

**Frontend :** Page détail membre (modal ou route `/membres/{id}`) avec :
- Statut joueur par saison (tableau `member_seasons`)
- Rôle asso (co-prez, etc.)
- Commissions

---

#### V1-6 — Corriger N+1 dans `alignment_service.add_events_to_alignment`
**Effort :** 0.5 jour | **Impact technique :** Performance

**Fichier :** `app/services/alignment_service.py`, lignes 44-68

```python
async def add_events_to_alignment(db, alignment, event_ids):
    # Vérifier tous les events en une seule query
    existing_events = await db.execute(
        select(Event.id).where(Event.id.in_(event_ids))
    )
    found_ids = {row[0] for row in existing_events.all()}
    missing = set(event_ids) - found_ids
    if missing:
        raise ValueError(f"Événements introuvables : {missing}")
    
    # Vérifier les AlignmentEvents existants en une seule query
    existing_aes = await db.execute(
        select(AlignmentEvent.event_id).where(
            AlignmentEvent.alignment_id == alignment.id,
            AlignmentEvent.event_id.in_(event_ids)
        )
    )
    already_added = {row[0] for row in existing_aes.all()}
    
    for i, event_id in enumerate(event_ids):
        if event_id in already_added:
            continue
        db.add(AlignmentEvent(alignment_id=alignment.id, event_id=event_id, sort_order=i))
    
    await db.flush()
```

---

#### V1-7 — Ajouter index sur `members.activation_token` et `members.reset_token`
**Effort :** 2h (migration Alembic) | **Impact :** Performance

```python
# Nouvelle migration Alembic
op.create_index("ix_members_activation_token", "members", ["activation_token"])
op.create_index("ix_members_reset_token", "members", ["reset_token"])
op.create_index("ix_member_seasons_season_id", "member_seasons", ["season_id"])
op.create_index("ix_alignments_season_id", "alignments", ["season_id"])
```

---

#### V1-8 — Migrer `python-jose` vers `PyJWT`
**Effort :** 1 jour | **Impact sécurité :** Haut

`python-jose` est unmaintained. Migration vers `PyJWT>=2.8` :

```python
# requirements.txt
# python-jose[cryptography]==3.3.0  ← supprimer
PyJWT==2.9.0

# app/utils/security.py
import jwt as pyjwt  # ← remplacer jose.jwt

def create_access_token(...) -> str:
    payload = {"sub": subject, "iat": now, "exp": expire, **(extra_claims or {})}
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
```

Mettre à jour `deps.py` pour capturer `pyjwt.exceptions.InvalidTokenError` au lieu de `JWTError`.

---

### V2 / Stratégique (> 3 jours)

#### V2-1 — Système de notifications push / email
**Valeur stratégique :** Engagement des membres

- Email automatique quand un joueur est ajouté à une grille d'alignement
- Rappel J-2 avant un événement (cron)
- Digest hebdomadaire de l'agenda
- Infrastructure : intégration Resend ou Mailgun + système de templates

---

#### V2-2 — Tableau de bord coach / bureau
**Valeur stratégique :** Réduction de la charge admin

- Vue par joueur : présences, absences, évolution saison
- Stats participation matchs vs cabarets
- Export CSV des alignements par trimestre
- Comparaison inter-saisons (tendances d'engagement)

---

#### V2-3 — App mobile-first (PWA ou React Native)
**Valeur stratégique :** Adoption des joueurs

Les membres vérifient leur planning depuis leur téléphone. L'app web actuelle est responsive mais pas optimisée mobile. Une PWA avec notifications push serait un vrai différenciateur.

---

#### V2-4 — IA pour la génération de grilles d'alignement
**Valeur stratégique :** Portfolio IA / différenciateur

Le backend `alignment_service` est la brique parfaite pour ajouter un système de suggestion d'alignement intelligent :
- Contraintes : disponibilités, équilibre des rôles, alternance joueurs
- LLM (Claude/GPT) pour suggérer une grille initiale à partir des contraintes textuelles
- Validation humaine obligatoire avant publication

C'est exactement le type de feature qui valorise ce projet dans un entretien IA engineer.

---

#### V2-5 — Résultats de matchs et statistiques joueurs
**Valeur stratégique :** Engagement communautaire

Nouveau modèle `MatchResult` avec scores équipe A/B, statistiques individuelles (votes public, awards). Feed de résultats sur la page d'accueil.

---

#### V2-6 — Internationalisation / multi-asso
**Valeur stratégique :** SaaS B2B

La LIMA n'est pas la seule ligue d'improvisation. L'architecture est prête pour du multi-tenant avec isolation par `organization_id`. Migration vers une offre SaaS pour les ligues de France.

---

## 5. Synthèse prioritaire

### Actions immédiates (cette semaine)

| Priorité | Action | Fichier | Effort |
|----------|--------|---------|--------|
| 🔴 P0 | Fix settings `/tmp` → DB | `routers/settings.py` | 4h |
| 🔴 P0 | Fix import CSV → `is_active=False` + token d'activation | `services/import_service.py` | 2h |
| 🔴 P0 | Fix bug StatusBadge toujours "A" | `pages/Members.tsx` | 2h |
| 🔴 P0 | Fix drift DailyActiveUserStat | `types/index.ts` | 1h |
| 🔴 P0 | Créer `GET /events/{id}/cast` | `routers/events.py` | 3h |
| 🟡 P1 | Rate limiting `reset-password` | `routers/auth.py` | 30min |
| 🟡 P1 | Ne pas retourner token en JSON | `routers/members.py` | 30min |
| 🟡 P1 | `is_active=False` à la création | `routers/members.py` | 2h |

### Pour la V1 consolidée

1. Vue "Mon planning" (V1-1) — use case n°1 des membres
2. Connecter CabaretOrganizer au backend (V1-2)
3. Emails d'activation à l'import CSV (V1-4)
4. Profil membre enrichi : statut, commissions (V1-5)
5. Migration `python-jose` → `PyJWT` (V1-8)
6. Index DB manquants (V1-7)

### Pour le portfolio / entretien

Les points les plus impressionnants à mettre en avant :
- **Architecture async correcte** : SQLAlchemy 2.0 async, sessions propres, UoW pattern
- **Tests bien structurés** : 1413 lignes, fixtures partagées, session-scoped DB
- **Sécurité by design** : JWT short-lived, bcrypt, anti-enumeration sur forgot-password, rate limiting
- **Import données réelles** : CSV HelloAsso + Excel calendrier avec déduplication
- **Middleware activity tracking** : analytics maison sans dépendance externe

**Les améliorations les plus valorisantes à montrer en entretien :**
1. Migration `python-jose` → `PyJWT` avec justification CVE
2. Correction N+1 avec `WHERE IN (...)` batch
3. Feature "Vue Mon Planning" avec query SQLAlchemy complexe
4. Feature IA de suggestion d'alignement (V2-4)

---

*Analyse produite le 2026-04-06 — À compléter avec les retours Jerome.*
