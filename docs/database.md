# Database Architecture & ERD

We deploy **PostgreSQL 15** utilizing highly normalized schemas tracked securely and reversibly via **Alembic**.

## Entity Relationship Diagram
```mermaid
erDiagram
    USERS ||--o{ TRANSACTIONS : creates
    USERS {
        UUID id PK
        string email
        string hashed_password
        boolean is_verified
        string role
        timestamps created_at
    }
    TRANSACTIONS {
        string transaction_id PK
        float amount
        int transaction_hour
        float fraud_probability
        boolean fraud_flag
        jsonb reason_codes
        string status
        UUID user_id FK
    }
```

## Table Specifications

### Users Table
- `id`: BTree indexed UUID4 constraints enabling massive horizontal hashing.
- `role`: Enum limiting privileges to `admin` / `user`. Default prevents arbitrary privilege escalation.

### Transactions Table
- `status`: Stored explicitly avoiding heavy joins. Possible states: `APPROVED`, `FLAGGED`, `REJECTED`, `VERIFICATION_SENT`.
- `reason_codes`: `JSONB` optimized index allowing fast array intersecting for specific model outputs.

## Migrations
All schema manipulations MUST run through Alembic.
1. Create a revision: `alembic revision --autogenerate -m "Add new column"`
2. Apply revision: `alembic upgrade head`
