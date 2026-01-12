# VANGUARD PROJECT - EXECUTION PLAN
## Phase 1: Foundation & Infrastructure

**Status:** IN PROGRESS
**Lead Engineer:** Antigravity
**Date:** 2026-01-10

### 1. Objective
Establish the rock-solid foundation for the Vanguard high-frequency sports arbitrage platform. This phase focuses on the "plumbing": databases, containerization, and the core application skeleton designed for scale and compliance.

### 2. Architecture Overview
- **Monorepo Structure:**
  - `/backend`: FastAPI (Python 3.12+), Async SQLAlchemy, Pydantic v2.
  - `/frontend`: Flutter (Mobile First strategy).
  - `/infra`: Docker Compose orchestration.
- **Data Layer:**
  - **PostgreSQL 16**: Core transactional data (Users, Wallets, Compliance Logs).
  - **TimescaleDB**: Time-series data for Odds History (Critical for backtesting).
  - **Redis 7**: Hot caching (Live Odds) and Pub/Sub for WebSocket events.

### 3. Step-by-Step Execution (Phase 1)

#### 3.1. Infrastructure (Docker)
- [ ] Create `docker-compose.yml` with robust health checks.
- [ ] Configure PostgreSQL with `America/Sao_Paulo` timezone.
- [ ] Configure Redis for persistent caching.

#### 3.2. Backend Core (FastAPI)
- [ ] Initialize Python environment with `uv` (or pip).
- [ ] Setup `app` structure:
  - `main.py`: Entrypoint with lifespan events.
  - `core/config.py`: Settings management (pydantic-settings).
  - `db/session.py`: Async engine configuration.
- [ ] Implement Compliance Middleware (Logging all requests for Lei 14.790).
- [ ] Create `/health` endpoint for Docker probes.

#### 3.3. Database Schema (Initial)
- [ ] Design Users table (KYC ready).
- [ ] Design Wallets table (Decimal precision ONLY).
- [ ] Run Alembic migrations.

#### 3.4. Frontend Foundation (Flutter)
*(Note: I will generate the Dart code structure. User must run `flutter pub get` locally)*
- [ ] Scaffold Flutter app with `go_router`.
- [ ] Implement `VanguardTheme` (Dark Mode optimized).
- [ ] create Login Screen skeleton.

### 4. Compliance Check (Lei 14.790)
- **Data Sovereignty:** Ensure DB timezones are explicit.
- **Audit Trails:** Prepare structure for immutable logs.

---
*Ready to execute. Moving to Infrastructure Setup.*
