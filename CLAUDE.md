# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hospital Management System — Streamlit + SQLAlchemy + SQLite. PII encrypted at rest (Fernet), passwords hashed (bcrypt), role-based access control, full audit logging.

## Commands

```bash
uv sync                        # Install dependencies
uv run streamlit run main.py   # Run app (localhost:8501)
python generate_key.py         # Generate Fernet key for .env
```

## Structure

| File | Purpose |
|---|---|
| `main.py` | Streamlit UI — login, dashboard, patient CRUD, audit logs |
| `models.py` | ORM models: `User`, `Patient`, `AuditLog` |
| `database.py` | Engine, session factory, `init_db()`, seed data |
| `auth.py` | Login/logout, bcrypt, RBAC, audit logging |
| `utils.py` | `CryptoManager` (Fernet), masking, CSV export |

## RBAC

- **Admin**: Full access to decrypted data + audit logs.
- **Doctor**: Read-only, anonymized data (`ANON_{id}`, masked contacts).
- **Receptionist**: Add patients + edit diagnosis only, anonymized data.

## Key Details

- SQLite DB (`hospital.db`) auto-creates on first run. Delete it to reset.
- `.env` needs `DB_URL` and `ENCRYPTION_KEY` (generate with `generate_key.py`).
- Default users: `admin`/`admin123`, `dr_bob`/`doc123`, `alice_recep`/`rec123`.
- No tests, no linting config, no CI/CD.
