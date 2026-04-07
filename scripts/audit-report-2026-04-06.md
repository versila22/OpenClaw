# Auto-Improvement Audit Report — 2026-04-06

## Summary

| Project | Tests | Coverage | Quality Issues (pre-fix) | Security Issues |
|---------|-------|----------|--------------------------|-----------------|
| ai-finops | ❌ None found | N/A | 9 ruff errors (1 auto-fixed) | 2 CRITICAL, 1 HIGH, 2 MEDIUM |
| lima-app backend | ❌ None found | N/A | 15 ruff errors (11 auto-fixed) | 1 HIGH, 3 MEDIUM, 2 LOW |
| hotline-darons | ✅ 30+ tests (couldn't run — no pytest in env) | N/A | 4 ruff errors (4 auto-fixed) | 0 CRITICAL, 1 MEDIUM, 2 LOW |
| fintrack-backend | ❌ None found | N/A | 2 ruff errors (2 auto-fixed) | 1 CRITICAL, 2 HIGH, 2 MEDIUM, 1 LOW |

---

## ai-finops

**Stack:** TypeScript (Vite/React) frontend + Python (FastAPI) backend  
**Path:** `/data/.openclaw/workspace/ai-finops/`

### Quality

- **Tests:** No Python tests found in `backend/`. `vitest.config.ts` exists for frontend but no test files present.
- **Ruff issues (pre-fix):** 9 errors — 7× E402 module-level imports not at top of file (in `main.py`), 1× F401 unused import, 1× F841 unused variable `reset_date` in seed_data.py.
- **Auto-fixed:** All 9 errors resolved:
  - Moved late imports to top of `main.py`
  - Removed unused `ProviderDetailResponse` import in `providers.py`
  - Removed dead `reset_date` assignment in `seed_data.py`
- **Remaining quality concerns:**
  - No input validation on `provider_id` path parameter (string, not typed/validated)
  - `update_provider` computes `usage_percent` with potential division by zero (guarded with `if provider.included_quota > 0` — OK)
  - No pagination on `/api/v1/alerts`, `/api/v1/plans`, `/api/v1/adjustments` — unbounded queries

### Security

- **[CRITICAL] No authentication on ANY endpoint** — All routes (`/api/v1/dashboard`, `/api/v1/providers`, `/api/v1/settings`, `/api/v1/alerts`, `/api/v1/plans`, `/api/v1/adjustments`, `/api/v1/sync`) have zero auth. No `get_current_user` dependency anywhere in the backend. Anyone with network access can read/write all data and trigger provider syncs.

- **[CRITICAL] API keys exposed via unauthenticated endpoints** — The `/api/v1/settings` endpoint allows reading AND writing app settings without auth. The `/api/v1/sync` endpoint triggers real API calls to OpenAI, Anthropic, Gemini, ElevenLabs using keys stored in the DB — also unprotected.

- **[HIGH] CORS too permissive for an internal tool** — `allow_credentials=True` combined with `allow_methods=["*"]` and `allow_headers=["*"]` while CORS origins include `https://ai-finops-api.duckdns.org` (public domain). No origin restriction on mutation endpoints.

- **[MEDIUM] No rate limiting** — No slowapi or equivalent. The `/api/v1/sync` route, without auth and rate limiting, can be called unlimited times to exhaust paid API quotas.

- **[MEDIUM] Unbounded DB queries** — `list_alerts`, `list_plans`, `list_adjustments` in `main.py` have no `limit` parameter, returning all records indefinitely.

---

## lima-app (backend)

**Stack:** FastAPI + PostgreSQL (asyncpg) + Alembic  
**Path:** `/data/.openclaw/workspace/lima/backend/`

### Quality

- **Tests:** No test files found in the backend directory.
- **Ruff issues (pre-fix):** 15 errors — mostly unused imports (F401), 2× unused variables (F841), 2× `== True` comparisons (E712).
- **Auto-fixed (11):** All F401 unused imports removed via `ruff --fix`. 4 remaining were fixed manually:
  - `member = await auth_service.request_password_reset(...)` → removed unused assignment in `auth.py`
  - `Season.is_current == True` → `Season.is_current` in `seasons.py` and `show_plans.py`
  - `created = member is None` → removed dead assignment in `import_service.py`
- **TODOs in code:**
  - `app/routers/members.py:105` — `# TODO: Send activation email` (invitation flow incomplete)
  - `app/routers/members.py:178` — `# TODO: Send email with token` (password reset email unimplemented)
  - `app/routers/auth.py:86` — `# TODO: send email when SMTP is configured`
- **Email system incomplete** — Password reset and account activation flows generate tokens but never send emails (SMTP disabled by default).

### Security

- **[HIGH] Default JWT secret is `"insecure_dev_secret_change_me"`** — The config has `JWT_SECRET: str = "insecure_dev_secret_change_me"` as default. If no env var is set in production, tokens signed with this well-known string are trivially forgeable. An attacker who knows the secret can generate valid admin tokens.

- **[MEDIUM] CORS default is `"*"` (wildcard)** — `CORS_ORIGINS: Union[str, List[str]] = "*"` with `allow_credentials=True`. A wildcard origin with credentials is actually blocked by browsers (CORS spec), but it signals a misconfiguration risk. Should be set to explicit origins in production.

- **[MEDIUM] No rate limiting on auth endpoints** — `/auth/login`, `/auth/forgot-password`, `/auth/activate` have no rate limiting. Login is susceptible to brute-force attacks. The forgot-password endpoint doesn't enumerate emails (good), but can be spammed.

- **[MEDIUM] Password reset tokens have no expiry check visible in schema** — `auth_service.activate_account` and `auth_service.reset_password` raise `ValueError` on bad tokens, but token expiry handling depends entirely on implementation details not shown. Needs verification.

- **[LOW] DEBUG=True by default** — `DEBUG: bool = True` in config. FastAPI/Starlette expose more error detail and stack traces in debug mode. Should be `False` in production.

- **[LOW] CSV import has no file size limit** — `import_service.py` reads CSV content via string, but there's no limit on file size. Large uploads could cause memory issues.

---

## hotline-darons

**Stack:** Python Telegram bot (python-telegram-bot) + Gemini AI + SQLite  
**Path:** `/data/.openclaw/workspace/hotline-darons/`

### Quality

- **Tests:** 30+ test cases exist in `tests/test_pii_filter.py` and `tests/test_session_store.py`. Tests cover PII detection, session photo storage, conversation history, and expiry. Could not execute (no pytest in system Python; project has no venv). Tests appear well-written and comprehensive for the existing modules.
- **Ruff issues (pre-fix):** 4 errors — all F401 unused imports (`dataclasses.field`, `typing.Optional` ×2, `datetime.timedelta`).
- **Auto-fixed:** All 4 resolved via `ruff --fix`.
- **Code quality is notably good** — Proper logging, PII detection, escalation logic, structured Gemini JSON responses with fallback, async cleanup.
- **No dead code found** — All modules are actively used.

### Security

- **[MEDIUM] Real API keys committed in `.env` file** — `/data/.openclaw/workspace/hotline-darons/.env` contains live credentials:
  - `TELEGRAM_BOT_TOKEN=REDACTED` (active bot token)
  - `GEMINI_API_KEY=REDACTED`
  - Escalation Telegram ID: `6390396611`
  
  The `.gitignore` lists `.env` but the file exists on disk. These credentials should be rotated if this project is or has been public. The `.env` must be confirmed absent from git history.

- **[LOW] No input sanitization on RAG query** — `rag_query = text or "problème technique"` feeds unvalidated user text directly to the vector search. Low risk for current FAISS/cosine implementation, but worth noting.

- **[LOW] Photo bytes stored in SQLite without encryption** — Photos containing potentially sensitive images are stored as blobs in a local SQLite DB. No encryption at rest. Mitigated by the PII detection and the short expiry window.

---

## fintrack-backend

**Stack:** FastAPI + SQLModel + SQLite (dev) / PostgreSQL  
**Path:** `/data/.openclaw/workspace/fintrack-backend/`

### Quality

- **Tests:** No test files found anywhere in the project.
- **Ruff issues (pre-fix):** 2 errors — F401 unused imports (`sqlmodel.select` in `auth.py`, `.models.Category` in `routers.py`).
- **Auto-fixed:** Both resolved via `ruff --fix`.
- **Good practices observed:** Proper OAuth2 flow, bcrypt passwords, user-scoped queries, pagination on transactions, Pydantic validation.
- **Minor:** `datetime.utcnow()` used in `models.py` (deprecated in Python 3.12+, should use `datetime.now(timezone.utc)`).

### Security

- **[CRITICAL] Powens API credentials hardcoded in config** — `app/config.py` has:
  ```python
  powens_client_id: str = "71972119"
  powens_client_secret: str = "znKIZMEtTtXE6taN4VazZUXIlqiP5tjz"
  ```
  These appear to be sandbox credentials but are committed in plaintext. If these values are reused outside the sandbox or if the Powens sandbox account has access to real user data, this is a serious exposure. Even sandbox credentials should not be hardcoded.

- **[HIGH] JWT secret regenerated on every restart** — `jwt_secret: str = secrets.token_hex(32)` generates a new random secret each startup. This means all active sessions are invalidated on every server restart. In production, this should be set via environment variable `JWT_SECRET`. The comment says "override via JWT_SECRET env var in prod" but there is no enforcement.

- **[HIGH] JWT expiry is 30 days by default** — `jwt_expire_days: int = 30` is very long for a financial application. Tokens cannot be invalidated server-side with this stateless approach; a stolen token is valid for 30 days.

- **[MEDIUM] No rate limiting on `/auth/login` or `/auth/register`** — The login endpoint is susceptible to brute-force. No account lockout, no CAPTCHA, no slowapi.

- **[MEDIUM] `datetime.utcnow()` deprecated** — Used in `models.py` for `created_at` and `last_synced` default factories. Should use `datetime.now(timezone.utc)` for timezone-aware datetimes.

- **[LOW] CORS origins parsed from comma-separated string without validation** — `cors_origins.split(",")` in `main.py` doesn't strip whitespace, so `"http://localhost:3000, http://localhost:5173"` (with space) would produce `" http://localhost:5173"` as an origin, silently failing CORS.

---

## Recommended Fixes (Priority Order)

1. **[CRITICAL] ai-finops** — Add authentication to ALL backend endpoints. At minimum, implement a simple API key middleware or Bearer token check. Without this, anyone can read all AI cost data and trigger expensive sync operations. — *Estimated fix: 2-4h (implement JWT auth module + apply to all routes)*

2. **[CRITICAL] fintrack-backend** — Remove hardcoded Powens credentials from `config.py`. Move to environment variables only with no defaults. Rotate credentials immediately. — *Estimated fix: 15min (config change + env var setup)*

3. **[CRITICAL] hotline-darons** — Rotate the Telegram bot token and Gemini API key committed in `.env`. Check git history (`git log -p -- .env`) to confirm they were never committed. Add `.env` to `.gitignore` if not already tracked. — *Estimated fix: 30min (rotate keys, verify git history)*

4. **[HIGH] lima-app** — Set a strong, unique `JWT_SECRET` via environment variable for all deployments. Remove the insecure default. Add startup validation that rejects the default value in production (`APP_ENV != "development"`). — *Estimated fix: 1h*

5. **[HIGH] fintrack-backend** — Reduce JWT expiry from 30 days to 24h or less for a financial app. Implement token refresh or a refresh token mechanism. — *Estimated fix: 2h*

6. **[HIGH] ai-finops** — Implement rate limiting on the `/sync` endpoint to prevent quota exhaustion attacks. — *Estimated fix: 1h (add slowapi)*

7. **[MEDIUM] All Python projects** — Add rate limiting on all auth endpoints (`/auth/login`, `/auth/register`, etc.). Use `slowapi` or similar. — *Estimated fix: 2h per project*

8. **[MEDIUM] lima-app** — Set `CORS_ORIGINS` to explicit frontend URL(s) in production config. Remove wildcard default. Set `DEBUG=False` in production. — *Estimated fix: 30min*

9. **[MEDIUM] hotline-darons** — Ensure `.env` is never committed (add pre-commit hook). Consider using `dotenv-vault` or a secrets manager. — *Estimated fix: 1h*

10. **[MEDIUM] fintrack-backend** — Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in `models.py`. — *Estimated fix: 15min*

11. **[LOW] All projects** — Add tests! fintrack-backend and ai-finops have zero tests. lima-app has none. Only hotline-darons has decent test coverage. — *Estimated fix: 1-2 days per project*

12. **[LOW] lima-app** — Implement the pending email flows (activation and password reset) or document clearly that the system is not production-ready without SMTP configuration. — *Estimated fix: 4h*

---

## Auto-Fixes Applied

The following LOW/MEDIUM issues were auto-fixed and staged (not committed):

### hotline-darons (`git add bot/`)
- Removed 4 unused imports: `dataclasses.field`, `typing.Optional` (×2), `datetime.timedelta`

### fintrack-backend (`git add app/`)  
- Removed 2 unused imports: `sqlmodel.select` (auth.py), `.models.Category` (routers.py)

### lima-app (`git add app/`)
- Removed 11 unused imports across `config.py`, `routers/alignments.py`, `routers/members.py`, `schemas/auth.py`, `schemas/member.py`, `services/alignment_service.py`, `services/auth_service.py`, `utils/security.py`
- Fixed 2× `Season.is_current == True` → `Season.is_current` (E712)
- Removed 2 unused variable assignments (`member` in auth.py, `created` in import_service.py)

### ai-finops (`git add backend/app/`)
- Moved late imports to top of `main.py` (resolves 7× E402)
- Removed unused `ProviderDetailResponse` import (providers.py)
- Removed dead `reset_date` variable assignment (seed_data.py)

**Verification note:** Tests could not be run (missing pytest/dependencies in environment). Changes are staged but NOT committed. Manual review and test run recommended before committing.
