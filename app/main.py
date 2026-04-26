from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes import accounts as accounts_router
from app.routes import admin as admin_router
from app.routes import auth as auth_router
from app.routes import beneficiaries as beneficiaries_router
from app.routes import loans as loans_router
from app.routes import scheduled_transfers as scheduled_transfers_router
from app.routes import transfers as transfers_router
from app.routes import users as users_router

app = FastAPI(
    title="Banking Core Service",
    description="Core banking — accounts, balances, transactions, transfers, loans, beneficiaries",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router,                prefix="/auth",                tags=["Auth"])
app.include_router(users_router.router,               prefix="/users",               tags=["Users"])
app.include_router(accounts_router.router,            prefix="/accounts",            tags=["Accounts"])
app.include_router(transfers_router.router,           prefix="/transfers",           tags=["Transfers"])
app.include_router(loans_router.router,               prefix="/loans",               tags=["Loans"])
app.include_router(beneficiaries_router.router,       prefix="/beneficiaries",       tags=["Beneficiaries"])
app.include_router(scheduled_transfers_router.router, prefix="/scheduled-transfers", tags=["Scheduled Transfers"])
app.include_router(admin_router.router,               prefix="/admin",               tags=["Admin"])


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "banking-app-core"}
