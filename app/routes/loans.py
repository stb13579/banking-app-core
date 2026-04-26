from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Account, Loan, Transaction
from app.schemas import AmortizationEntry, LoanRepayRequest, LoanRequest, LoanResponse

router = APIRouter()


def _monthly_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    """M = P × r(1+r)^n / ((1+r)^n − 1)"""
    if annual_rate == 0:
        return (principal / term_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    r = annual_rate / Decimal("12")
    factor = (1 + r) ** term_months
    return (principal * r * factor / (factor - 1)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _amortization_schedule(
    principal: Decimal, annual_rate: Decimal, term_months: int, monthly_payment: Decimal
) -> List[AmortizationEntry]:
    schedule = []
    balance = principal
    r = annual_rate / Decimal("12")
    for month in range(1, term_months + 1):
        interest = (balance * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal_paid = (monthly_payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        balance = max(balance - principal_paid, Decimal("0.00"))
        schedule.append(AmortizationEntry(
            month=month,
            payment=monthly_payment,
            principal=principal_paid,
            interest=interest,
            balance=balance,
        ))
    return schedule


@router.post("", response_model=LoanResponse, status_code=201)
def apply_for_loan(
    payload: LoanRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    VULNERABILITY (IDOR + Business Logic): No ownership check on the target account.
    An attacker can disburse a loan into any account ID they supply.
    VULNERABILITY (No Credit/Risk Check): Loan amount is not validated against
    any limit, credit score, or account history.
    """
    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    monthly_pay = _monthly_payment(payload.principal, payload.interest_rate, payload.term_months)

    loan = Loan(
        account_id=payload.account_id,
        user_id=current_user["sub"],
        principal=payload.principal,
        interest_rate=payload.interest_rate,
        outstanding_balance=payload.principal,
        term_months=payload.term_months,
        monthly_payment=monthly_pay,
        next_payment_date=datetime.utcnow() + timedelta(days=30),
    )
    db.add(loan)

    account.balance = Decimal(str(account.balance)) + payload.principal

    ref = f"TXN-{datetime.utcnow().strftime('%Y%m%d')}-LOAN"
    txn = Transaction(
        from_account_id=None,
        to_account_id=payload.account_id,
        amount=payload.principal,
        type="loan_disbursement",
        status="completed",
        description=f"Loan disbursement — {payload.term_months} months at {float(payload.interest_rate)*100:.2f}%",
        reference_number=ref,
        category="loan_disbursement",
    )
    db.add(txn)
    db.commit()
    db.refresh(loan)
    return loan


@router.get("", response_model=List[LoanResponse])
def list_loans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(Loan).filter(Loan.user_id == current_user["sub"]).all()


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """VULNERABILITY (IDOR): No ownership check."""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.get("/{loan_id}/schedule", response_model=List[AmortizationEntry])
def get_loan_schedule(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Return the full amortization schedule for a loan.
    VULNERABILITY (IDOR): No ownership check — consistent with GET /loans/{id}.
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not loan.term_months or not loan.monthly_payment:
        raise HTTPException(status_code=400, detail="Loan has no repayment schedule")

    return _amortization_schedule(
        loan.outstanding_balance,
        loan.interest_rate,
        loan.term_months,
        loan.monthly_payment,
    )


@router.post("/{loan_id}/repay", response_model=LoanResponse)
def repay_loan(
    loan_id: str,
    payload: LoanRepayRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Make a repayment against a loan.
    VULNERABILITY (IDOR): No ownership check on the loan — any authenticated
    user can repay any loan (and debit any account they own toward it).
    Source account ownership IS enforced (the only check here).
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status == "paid_off":
        raise HTTPException(status_code=400, detail="Loan is already paid off")

    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if Decimal(str(account.balance)) < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    account.balance = Decimal(str(account.balance)) - payload.amount
    loan.outstanding_balance = max(
        Decimal(str(loan.outstanding_balance)) - payload.amount,
        Decimal("0.00"),
    )
    if loan.next_payment_date:
        loan.next_payment_date = loan.next_payment_date + timedelta(days=30)
    if loan.outstanding_balance == Decimal("0.00"):
        loan.status = "paid_off"

    ref = f"TXN-{datetime.utcnow().strftime('%Y%m%d')}-REPAY"
    txn = Transaction(
        from_account_id=payload.account_id,
        to_account_id=None,
        amount=payload.amount,
        type="loan_repayment",
        status="completed",
        description=f"Loan repayment for loan {loan_id[:8]}",
        reference_number=ref,
        category="loan_repayment",
    )
    db.add(txn)
    db.commit()
    db.refresh(loan)
    return loan
