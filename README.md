# banking-app-core — Core Banking Service

Python 3.11 / FastAPI core banking service. Manages accounts, balances, transaction history, transfers, loans, beneficiaries, and scheduled transfers.

Part of the mock consumer banking application.

---

## Quick Start

### Standalone (with Docker)

```bash
docker compose up
```

Service starts on port **8002**. Swagger UI at http://localhost:8002/docs.

### Local development

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

---

## API

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Register a new user |
| `POST` | `/auth/login` | No | Login and receive JWT |
| `POST` | `/auth/reset-password/request` | No | Request password reset |
| `POST` | `/auth/reset-password/confirm` | No | Confirm password reset |

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users/me` | Bearer | Get own profile |
| `PUT` | `/users/me` | Bearer | Update profile |

### Accounts

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/accounts` | Bearer | List your accounts |
| `POST` | `/accounts` | Bearer | Open new account |
| `GET` | `/accounts/{id}` | Bearer | Get account by ID |
| `PUT` | `/accounts/{id}` | Bearer | Update account |
| `GET` | `/accounts/{id}/transactions` | Bearer | Transaction history |
| `GET` | `/accounts/{id}/statements/{year}/{month}` | Bearer | Monthly statement |

### Transfers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/transfers` | Bearer | Transfer funds |

### Loans

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/loans` | Bearer | Apply for a loan |
| `GET` | `/loans` | Bearer | List your loans |
| `GET` | `/loans/{id}` | Bearer | Get loan by ID |
| `POST` | `/loans/{id}/repay` | Bearer | Make a repayment |
| `GET` | `/loans/{id}/schedule` | Bearer | Amortization schedule |

### Beneficiaries

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/beneficiaries` | Bearer | Add beneficiary |
| `GET` | `/beneficiaries` | Bearer | List beneficiaries |
| `DELETE` | `/beneficiaries/{id}` | Bearer | Remove beneficiary |

### Scheduled Transfers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/scheduled-transfers` | Bearer | Create schedule |
| `GET` | `/scheduled-transfers` | Bearer | List schedules |
| `PATCH` | `/scheduled-transfers/{id}/status` | Bearer | Update status |
| `DELETE` | `/scheduled-transfers/{id}` | Bearer | Delete schedule |

### Admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/admin/users` | Bearer (admin) | List all users |
| `GET` | `/admin/accounts` | Bearer (admin) | List all accounts |
| `POST` | `/admin/accounts/adjust-balance` | Bearer (admin) | Set account balance |
| `DELETE` | `/admin/users/{id}` | Bearer (admin) | Delete user |

---

## curl Examples

### Register and login

```bash
curl -s -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"hunter2"}' | jq

TOKEN=$(curl -s -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"hunter2"}' | jq -r '.access_token')
```

### Open account and transfer

```bash
ACCOUNT=$(curl -s -X POST http://localhost:8002/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"checking"}' | jq -r '.id')

curl -s -X POST http://localhost:8002/transfers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"from_account_id\":\"$ACCOUNT\",\"to_account_id\":\"<DEST>\",\"amount\":50.00}" | jq
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://banking:banking@localhost:5432/banking` | PostgreSQL connection string |
| `JWT_SECRET` | `supersecret123` | JWT verification secret |
| `PORT` | `8002` | Service port |
