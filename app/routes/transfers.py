import logging
from datetime import datetime
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Account, Transaction
from app.schemas import TransactionResponse, TransferRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=TransactionResponse, status_code=200)
def transfer(
    payload: TransferRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Transfer funds between accounts. Ownership enforced on source account."""
    from_account = db.query(Account).filter(Account.id == payload.from_account_id).first()
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    if from_account.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if from_account.status != "active":
        raise HTTPException(status_code=400, detail="Source account is not active")
    if Decimal(str(from_account.balance)) < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    to_account = db.query(Account).filter(Account.id == payload.to_account_id).first()
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")

    from_account.balance = Decimal(str(from_account.balance)) - payload.amount
    to_account.balance   = Decimal(str(to_account.balance))   + payload.amount

    ref = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    txn = Transaction(
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        type="transfer",
        status="completed",
        description=payload.description,
        reference_number=ref,
        category="transfer",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    if payload.webhook_url:
        try:
            httpx.post(
                payload.webhook_url,
                json={"transaction_id": txn.id, "amount": str(payload.amount)},
                timeout=5.0,
            )
        except Exception:
            pass

    return txn
