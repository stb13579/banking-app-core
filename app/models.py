import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username      = Column(String, unique=True, nullable=False, index=True)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="user")
    created_at    = Column(DateTime, default=datetime.utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id        = Column(String, nullable=False, index=True)
    account_number = Column(String(10), unique=True, nullable=False, index=True)
    routing_number = Column(String(9), default="021000021")
    type           = Column(String, nullable=False)
    balance        = Column(Numeric(15, 2), default=Decimal("0.00"))
    currency       = Column(String, default="USD")
    status         = Column(String, default="active")
    nickname       = Column(String, nullable=True)
    interest_rate  = Column(Numeric(5, 4), default=Decimal("0.0000"))
    created_at     = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account_id  = Column(String, nullable=True)
    to_account_id    = Column(String, nullable=True)
    amount           = Column(Numeric(15, 2), nullable=False)
    type             = Column(String, nullable=False)
    status           = Column(String, default="completed")
    description      = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)
    category         = Column(String, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)


class Loan(Base):
    __tablename__ = "loans"

    id                  = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id          = Column(String, nullable=False, index=True)
    user_id             = Column(String, nullable=False, index=True)
    principal           = Column(Numeric(15, 2), nullable=False)
    interest_rate       = Column(Numeric(5, 4), nullable=False)
    outstanding_balance = Column(Numeric(15, 2), nullable=False)
    term_months         = Column(Integer, nullable=True)
    monthly_payment     = Column(Numeric(15, 2), nullable=True)
    next_payment_date   = Column(DateTime, nullable=True)
    status              = Column(String, default="active")
    created_at          = Column(DateTime, default=datetime.utcnow)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id        = Column(String, nullable=False, index=True)
    name           = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    routing_number = Column(String, nullable=False)
    nickname       = Column(String, nullable=True)
    bank_name      = Column(String, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


class ScheduledTransfer(Base):
    __tablename__ = "scheduled_transfers"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id         = Column(String, nullable=False, index=True)
    from_account_id = Column(String, nullable=False)
    to_account_id   = Column(String, nullable=False)
    amount          = Column(Numeric(15, 2), nullable=False)
    frequency       = Column(String, nullable=False)
    next_run_date   = Column(DateTime, nullable=False)
    description     = Column(String, nullable=True)
    status          = Column(String, default="active")
    created_at      = Column(DateTime, default=datetime.utcnow)
