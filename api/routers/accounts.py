from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.orm import Account, Flag
from models.schemas import AccountOut, FlagOut, StatusUpdate

router = APIRouter()

# valid statuses an acount can move through in the investigation queue
VALID_STATUSES = {"clean", "flagged", "reviewing", "confirmed", "dismissed"}
 
 
@router.get("/", response_model=list[AccountOut])
async def list_accounts(
    min_risk: float = Query(0.0, description="filter by minimum risk score"),
    status: str = Query(None, description="filter by status"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    returns all accounts, optionally filtered by risk, score or status
    the frontend uses it for the flagged table
    """
    query = select(Account).where(Account.risk_score >= min_risk)
    
    if status:
        query = query.where(Account.status == status)
        
    # sort by risk score descending so the most sus come first
    query = query.order_by(Account.risk_score.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """retuns a single account by id"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="account not found")
    
    return account


@router.get("/{account_id}/flags", response_model=list[FlagOut])
async def get_account_flags(account_id: str, db: AsyncSession = Depends(get_db)):
    """
    returns all flags for a specific account, used on the accoun detail page
    so you can see what each detection layer caught and when
    """
    result = await db.execute(
        select(Flag)
        .where(Flag.account_id == account_id)
        .order_by(Flag.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{account_id}/status", response_model=AccountOut)
async def update_account_status(
    account_id: str,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    moves an account through the investigation workdlow
    thats what the frontend call when you action something in the queue
    """
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"invalid status, must be one of {VALID_STATUSES}",
        )
        
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="account not found")
    
    await db.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(status=body.status)
    )
    await db.commit()
    
    # re fetch the account to return the updated version
    result = await db.execute(select(Account).where(Account.id == account_id))
    return result.scalar_one()
    
    