import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Account, User
from app.schemas import AccountResponse, UserResponse, BalanceAdjustRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    admin: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).all()


@router.get("/accounts", response_model=List[AccountResponse])
def list_all_accounts(
    admin: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return db.query(Account).all()


@router.post("/accounts/adjust-balance")
def adjust_balance(
    payload: BalanceAdjustRequest,
    admin: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    old_balance = account.balance
    account.balance = payload.new_balance
    db.commit()

    logger.info(
        f"Admin balance adjustment: account={payload.account_id} "
        f"old={old_balance} new={payload.new_balance} "
        f"by={admin.get('username')} reason={payload.reason}"
    )
    return {
        "account_id": payload.account_id,
        "old_balance": str(old_balance),
        "new_balance": str(payload.new_balance),
    }


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    admin: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
