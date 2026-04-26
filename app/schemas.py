from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


# ---------- Accounts ----------

class AccountCreate(BaseModel):
    type: str           # checking | savings | money_market | cd
    currency: str = "USD"
    nickname: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    user_id: str
    account_number: str
    routing_number: str
    type: str
    balance: Decimal
    currency: str
    status: str
    nickname: Optional[str]
    interest_rate: Decimal
    created_at: datetime

    class Config:
        orm_mode = True


class AccountUpdate(BaseModel):
    type: Optional[str] = None
    currency: Optional[str] = None
    nickname: Optional[str] = None
    status: Optional[str] = None
    balance: Optional[Decimal] = None   # should never be user-settable
    user_id: Optional[str] = None       # should never be user-settable


class TransactionResponse(BaseModel):
    id: str
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    amount: Decimal
    type: str
    status: str
    description: Optional[str]
    reference_number: Optional[str]
    category: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class StatementResponse(BaseModel):
    account_id: str
    year: int
    month: int
    opening_balance: Decimal
    closing_balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    transactions: List[TransactionResponse]


# ---------- Transfers ----------

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: Optional[str] = None
    # VULNERABILITY (SSRF): webhook_url is user-supplied and fetched server-side
    # without validation, allowing probing of internal services.
    webhook_url: Optional[str] = None


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# ---------- Users ----------

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None          # should never be user-settable


# ---------- Admin ----------

class BalanceAdjustRequest(BaseModel):
    account_id: str
    new_balance: Decimal
    reason: Optional[str] = None


# ---------- Loans ----------

class LoanRequest(BaseModel):
    account_id: str
    principal: Decimal
    interest_rate: Decimal = Decimal("0.05")
    term_months: int = 36


class LoanResponse(BaseModel):
    id: str
    account_id: str
    user_id: str
    principal: Decimal
    interest_rate: Decimal
    outstanding_balance: Decimal
    term_months: Optional[int]
    monthly_payment: Optional[Decimal]
    next_payment_date: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class LoanRepayRequest(BaseModel):
    account_id: str
    amount: Decimal


class AmortizationEntry(BaseModel):
    month: int
    payment: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal


# ---------- Beneficiaries ----------

class BeneficiaryCreate(BaseModel):
    name: str
    account_number: str
    routing_number: str
    nickname: Optional[str] = None
    bank_name: Optional[str] = None


class BeneficiaryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    account_number: str
    routing_number: str
    nickname: Optional[str]
    bank_name: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# ---------- Scheduled Transfers ----------

class ScheduledTransferCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: Decimal
    frequency: str          # weekly | biweekly | monthly
    next_run_date: datetime
    description: Optional[str] = None


class ScheduledTransferResponse(BaseModel):
    id: str
    user_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    frequency: str
    next_run_date: datetime
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
