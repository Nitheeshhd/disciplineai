# DisciplineAI Enterprise SaaS

link:https://disciplineai.onrender.com

Production-grade Telegram Bot Analytics & Productivity SaaS platform built with async FastAPI, PostgreSQL, Redis, Celery, APScheduler, SQLAlchemy 2.0, Alembic, and enterprise observability/security patterns.

## Architecture Summary

### Clean Architecture Layout
```text
app/
  core/            # config, security, db, redis, celery, logging, openapi
  models/          # domain + persistence entities
  schemas/         # Pydantic v2 API contracts
  repositories/    # data access abstraction
  services/        # business workflows / application services
  api/routes/      # versioned HTTP endpoints
  workers/         # Celery tasks + APScheduler integration
  analytics/       # CQRS commands/queries + domain event handlers
  middleware/      # request-id, rate-limit, metrics, error logging
  utils/           # shared utility helpers
alembic/
  versions/        # migration history
tests/
  unit/
  integration/
```

### DDD + CQRS Decisions
- Write model:
  - transactional entities (`users`, `sessions`, `habit_logs`, `messages`, etc.).
  - commands handled in services (`HabitService.log_habit`).
- Read model:
  - denormalized projection table `daily_analytics_read_model` for fast dashboard analytics.
  - query repositories only read from projections for analytics endpoints.
- Domain event flow:
  1. Habit log command persists habit + outbox event.
  2. EventBus publishes `habit.logged`.
  3. Handler triggers Celery task `project_daily_analytics`.
  4. Projection repository updates read model row.

## Enterprise Features Implemented

1. Authentication + RBAC
- JWT access and refresh tokens
- bcrypt password hashing
- session persistence for refresh token JTI lifecycle
- role model (`admin`, `analyst`, `user`)
- role-guard dependency (`require_roles`)

2. Dashboard Summary
- `GET /api/v1/dashboard/summary`
- returns:
  - `sessions_today`
  - `total_users`
  - `messages_today`
  - `revenue_today`
- Redis-cached for 60 seconds

3. Analytics Endpoints
- `GET /api/v1/analytics/productivity-trend`
- `GET /api/v1/analytics/demographics`
- `GET /api/v1/analytics/conversion-rate`
- `GET /api/v1/analytics/revenue-trend`
- `GET /api/v1/analytics/productivity-metrics`

4. Productivity Engine
- streak detection
- moving average
- anomaly detection using statistical threshold
- behavioral scoring model (0-100)

5. Error Logging System
- middleware captures unhandled exceptions
- stores structured records in `error_logs`
- includes `trace_id` in error response

6. Background Jobs
- Weekly report generation
- Productivity projection recalculation
- Inactive user detection
- Runs via Celery tasks; APScheduler triggers dispatches

7. Caching
- Redis summary cache with TTL
- designed for extensible query caching strategy

8. Observability
- `GET /api/v1/health`
- `GET /api/v1/readiness` (DB + Redis probe)
- `GET /api/v1/metrics` (Prometheus-compatible)
- JSON structured logging
- request ID propagation via `X-Request-ID`

9. API Versioning
- all API endpoints under `/api/v1/`

10. Security Controls
- CORS policy from environment
- Redis-backed rate limit middleware
- JWT validation and session revocation checks
- strict env validation with `pydantic-settings`

## Database Design

### Normalized Tables
- `users`
- `roles`
- `user_roles`
- `sessions`
- `messages`
- `payments`
- `habit_logs`
- `conversions`
- `campaign_tracking`
- `error_logs`
- `domain_event_outbox`
- `daily_analytics_read_model` (CQRS read model)

### Standards
- FK constraints with delete strategy
- explicit indexes for query patterns
- audit fields: `created_at`, `updated_at`
- soft-delete fields: `is_deleted`, `deleted_at` on primary domain tables

## API Route Map

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

### Dashboard
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/data`

### Analytics
- `GET /api/v1/analytics/productivity-trend`
- `GET /api/v1/analytics/demographics`
- `GET /api/v1/analytics/conversion-rate`
- `GET /api/v1/analytics/revenue-trend`
- `GET /api/v1/analytics/productivity-metrics`

### Habits
- `POST /api/v1/habits/log`

### Observability
- `GET /api/v1/health`
- `GET /api/v1/readiness`
- `GET /api/v1/metrics`

### Telegram Ingestion
- `POST /telegram/webhook`

### UI
- `GET /`

## Local Development

1. Create env file:
```bash
cp .env.example .env
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start API:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Start worker:
```bash
celery -A app.workers.runner.celery_app worker --loglevel=info
```

## Docker Deployment
```bash
docker compose up --build
```

Services:
- `api` (FastAPI)
- `worker` (Celery)
- `postgres`
- `redis`

## Alembic

Generate migration:
```bash
alembic revision --autogenerate -m "change description"
```

Apply migration:
```bash
alembic upgrade head
```

## Testing

Run tests:
```bash
pytest -q
```

Current test layout:
- `tests/unit/test_productivity_service.py`
- `tests/unit/test_auth_service.py`

## Resume Bullet (Example)

Designed and delivered an enterprise-grade, event-driven SaaS analytics platform for Telegram bots using FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery, APScheduler, and CQRS read models; implemented secure JWT+RBAC auth, observability (Prometheus metrics, structured logging, trace IDs), anomaly-based productivity scoring, and production deployment with Docker and Alembic migrations.
