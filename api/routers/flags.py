from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.orm import Flag
from models.schemas import FlagOut

router = APIRouter()


@router.get("/", response_model=list[FlagOut])
async def list_flags(
    limit: int = Query(50, le=200),
    source: str = Query(None, description="filter by detection layer"),
    min_score: float = Query(0.0, description="filter by minimum score"),
    db: AsyncSession = Depends(get_db),
):
    """
    returns recent flags across all accounts, newest first
    the frontend uses it to populate the live feed table on load
    the websocket then appends new flags in real time as they come in
    """
    query = (
        select(Flag)
        .where(Flag.score >= min_score)
        .order_by(Flag.created_at.desc())
        .limit(limit)
    )
    
    if source:
        query = query.where(Flag.source == source)
        
        
    result = await db.execute(query)
    return result.scalars().all()