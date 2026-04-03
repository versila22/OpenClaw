# Addiction Tracker App

Initialisation d'une nouvelle application basée sur la stack réellement observée dans `lima-app` et `moni-muse-app`.

## Stack retenue

### Frontend
- Vite
- React 18
- TypeScript
- React Router
- TanStack Query
- Tailwind CSS

### Backend
- Python
- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- Pydantic Settings

## Domaine
Application de suivi d'addiction multi-substances avec :
- `User`
- `Substance`
- `DailyLog`
- graphe d'état IA pour routage `Évaluation -> Exercice_TCC | Alerte_Locale`

## Endpoints
- `GET /api/health`
- `POST /api/users`
- `POST /api/substances`
- `POST /api/daily-logs`
- `POST /api/assessment`
