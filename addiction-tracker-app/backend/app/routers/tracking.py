from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_graph.state_graph import AddictionState, AddictionSupportGraph
from app.database import get_db
from app.models.daily_log import DailyLog
from app.models.substance import Substance
from app.models.user import User
from app.schemas.tracking import AssessmentInput, DailyLogCreate, SubstanceCreate, UserCreate

router = APIRouter(prefix="/api", tags=["tracking"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        for user in users
    ]


@router.post("/users")
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=payload.password_hash,
    )
    db.add(user)
    await db.flush()
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.get("/substances")
async def list_substances(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Substance).order_by(Substance.name.asc()))
    substances = result.scalars().all()
    return [
        {
            "id": substance.id,
            "name": substance.name,
            "category": substance.category,
            "description": substance.description,
            "risk_level": substance.risk_level,
        }
        for substance in substances
    ]


@router.post("/substances")
async def create_substance(payload: SubstanceCreate, db: AsyncSession = Depends(get_db)):
    substance = Substance(
        name=payload.name,
        category=payload.category,
        description=payload.description,
        risk_level=payload.risk_level,
    )
    db.add(substance)
    await db.flush()
    return {
        "id": substance.id,
        "name": substance.name,
        "category": substance.category,
        "description": substance.description,
        "risk_level": substance.risk_level,
    }


@router.get("/daily-logs")
async def list_daily_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyLog).order_by(DailyLog.log_date.desc(), DailyLog.created_at.desc()))
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "substance_id": log.substance_id,
            "log_date": log.log_date.isoformat(),
            "craving_level": log.craving_level,
            "quantity_used": log.quantity_used,
            "mood_score": log.mood_score,
            "cbt_notes": log.cbt_notes,
            "trigger_notes": log.trigger_notes,
        }
        for log in logs
    ]


@router.post("/daily-logs")
async def create_daily_log(payload: DailyLogCreate, db: AsyncSession = Depends(get_db)):
    log = DailyLog(
        user_id=payload.user_id,
        substance_id=payload.substance_id,
        log_date=payload.log_date,
        craving_level=payload.craving_level,
        quantity_used=payload.quantity_used,
        mood_score=payload.mood_score,
        cbt_notes=payload.cbt_notes,
        trigger_notes=payload.trigger_notes,
    )
    db.add(log)
    await db.flush()
    return {
        "id": log.id,
        "user_id": log.user_id,
        "substance_id": log.substance_id,
        "log_date": log.log_date.isoformat(),
        "craving_level": log.craving_level,
        "quantity_used": log.quantity_used,
        "mood_score": log.mood_score,
        "cbt_notes": log.cbt_notes,
        "trigger_notes": log.trigger_notes,
    }


@router.post("/assessment")
async def run_assessment(payload: AssessmentInput):
    graph = AddictionSupportGraph()
    result = graph.run(
        AddictionState(
            craving_level=payload.craving_level,
            substance_name=payload.substance_name,
            city=payload.city,
            postal_code=payload.postal_code,
            cbt_notes=payload.cbt_notes,
        )
    )
    return result
