from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Beneficiary
from app.schemas import BeneficiaryCreate, BeneficiaryResponse

router = APIRouter()


@router.post("", response_model=BeneficiaryResponse, status_code=201)
def add_beneficiary(
    payload: BeneficiaryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    beneficiary = Beneficiary(
        user_id=current_user["sub"],
        name=payload.name,
        account_number=payload.account_number,
        routing_number=payload.routing_number,
        nickname=payload.nickname,
        bank_name=payload.bank_name,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


@router.get("", response_model=List[BeneficiaryResponse])
def list_beneficiaries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return (
        db.query(Beneficiary)
        .filter(Beneficiary.user_id == current_user["sub"])
        .order_by(Beneficiary.created_at.desc())
        .all()
    )


@router.delete("/{beneficiary_id}", status_code=204)
def delete_beneficiary(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    b = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    if b.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(b)
    db.commit()
