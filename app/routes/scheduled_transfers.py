from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Account, ScheduledTransfer
from app.schemas import ScheduledTransferCreate, ScheduledTransferResponse

router = APIRouter()

VALID_FREQUENCIES = ["weekly", "biweekly", "monthly"]
VALID_STATUSES    = ["active", "paused", "cancelled"]


@router.post("", response_model=ScheduledTransferResponse, status_code=201)
def create_scheduled_transfer(
    payload: ScheduledTransferCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if payload.frequency not in VALID_FREQUENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"frequency must be one of: {', '.join(VALID_FREQUENCIES)}",
        )

    from_account = db.query(Account).filter(Account.id == payload.from_account_id).first()
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    if from_account.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    schedule = ScheduledTransfer(
        user_id=current_user["sub"],
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        frequency=payload.frequency,
        next_run_date=payload.next_run_date,
        description=payload.description,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("", response_model=List[ScheduledTransferResponse])
def list_scheduled_transfers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return (
        db.query(ScheduledTransfer)
        .filter(ScheduledTransfer.user_id == current_user["sub"])
        .order_by(ScheduledTransfer.next_run_date.asc())
        .all()
    )


@router.patch("/{schedule_id}/status", response_model=ScheduledTransferResponse)
def update_schedule_status(
    schedule_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    status = payload.get("status")
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of: {', '.join(VALID_STATUSES)}",
        )

    schedule = db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Scheduled transfer not found")
    if schedule.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    schedule.status = status
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
def delete_scheduled_transfer(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    schedule = db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Scheduled transfer not found")
    if schedule.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(schedule)
    db.commit()
