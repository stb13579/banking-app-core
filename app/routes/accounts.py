import random
from calendar import monthrange
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Account, Transaction
from app.schemas import (
    AccountCreate, AccountResponse, AccountUpdate,
    StatementResponse, TransactionResponse,
)

router = APIRouter()

INTEREST_RATES = {
    "savings":      Decimal("0.0250"),
    "money_market": Decimal("0.0400"),
    "cd":           Decimal("0.0510"),
}


def _generate_account_number(db: Session) -> str:
    for _ in range(10):
        number = str(random.randint(1000000000, 9999999999))
        if not db.query(Account).filter(Account.account_number == number).first():
            return number
    raise RuntimeError("Could not generate unique account number")


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(Account).filter(Account.user_id == current_user["sub"]).all()


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    account = Account(
        user_id=current_user["sub"],
        account_number=_generate_account_number(db),
        routing_number="021000021",
        type=payload.type,
        currency=payload.currency,
        nickname=payload.nickname,
        interest_rate=INTEREST_RATES.get(payload.type, Decimal("0.0000")),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}/transactions", response_model=List[TransactionResponse])
def list_transactions(
    account_id: str,
    type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    limit = min(limit, 100)

    if type is not None:
        query = (
            f"SELECT id, from_account_id, to_account_id, amount, type, status, "
            f"description, reference_number, category, created_at "
            f"FROM transactions "
            f"WHERE (from_account_id = '{account_id}' OR to_account_id = '{account_id}') "
            f"AND type = '{type}' "
            f"ORDER BY created_at DESC "
            f"LIMIT {limit} OFFSET {offset}"
        )
        rows = db.execute(text(query)).fetchall()
        return [dict(r._mapping) for r in rows]

    q = db.query(Transaction).filter(
        (Transaction.from_account_id == account_id) |
        (Transaction.to_account_id == account_id)
    )
    if from_date:
        q = q.filter(Transaction.created_at >= from_date)
    if to_date:
        q = q.filter(Transaction.created_at <= to_date)

    return q.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{account_id}/statements/{year}/{month}", response_model=StatementResponse)
def get_statement(
    account_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    _, last_day = monthrange(year, month)
    start = datetime(year, month, 1)
    end   = datetime(year, month, last_day, 23, 59, 59)

    txns = (
        db.query(Transaction)
        .filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        )
        .filter(Transaction.created_at >= start, Transaction.created_at <= end)
        .order_by(Transaction.created_at.asc())
        .all()
    )

    total_credits = sum(t.amount for t in txns if t.to_account_id == account_id)
    total_debits  = sum(t.amount for t in txns if t.from_account_id == account_id)
    closing_balance  = Decimal(str(account.balance))
    opening_balance  = closing_balance - total_credits + total_debits

    return StatementResponse(
        account_id=account_id,
        year=year,
        month=month,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        total_credits=total_credits,
        total_debits=total_debits,
        transactions=txns,
    )
