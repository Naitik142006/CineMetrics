# CineMetrics — Deployment, Infrastructure & Production Operations Guide

**Document ID:** 24  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [Security & Governance](22_SECURITY_AND_GOVERNANCE.md) | [Resource & Feasibility](25_RESOURCE_AND_FEASIBILITY_ANALYSIS.md)

---

## Table of Contents

1. [Deployment Strategy & Infrastructure Philosophy](#1-deployment-strategy--infrastructure-philosophy)
2. [Primary Target: Local Multi-Container Deployment (Docker Compose)](#2-primary-target-local-multi-container-deployment-docker-compose)
3. [Zero-Cost Cloud Deployment Blueprint](#3-zero-cost-cloud-deployment-blueprint)
   - 3.1 [Frontend on Vercel](#31-frontend-on-vercel)
   - 3.2 [Backend API on Fly.io / Render](#32-backend-api-on-flyio--render)
   - 3.3 [Managed Database on Supabase Free Tier](#33-managed-database-on-supabase-free-tier)
4. [Environment Configuration & Profile Management](#4-environment-configuration--profile-management)
5. [Database Migrations & Initial Cold-Start Seeding](#5-database-migrations--initial-cold-start-seeding)
6. [Production Readiness & Operational Checklist](#6-production-readiness--operational-checklist)
7. [Zero-Cost Observability & Health Monitoring](#7-zero-cost-observability--health-monitoring)

---

## 1. Deployment Strategy & Infrastructure Philosophy

CineMetrics is designed to maximize student feasibility without compromising production engineering standards:
- **Zero-Cloud-Cost Baseline**: The entire platform runs locally on any modern consumer laptop using Docker Compose.
- **Optional Free-Tier Cloud Deployment**: If the developer wishes to showcase the live platform on a public portfolio URL, the architecture deploys entirely within the generous, permanently free tiers of modern developer platforms (Vercel, Fly.io, and Supabase).
- **Immutable Artifacts**: Pre-trained machine learning models and conformed databases are treated as versioned deployable assets.

---

## 2. Primary Target: Local Multi-Container Deployment (Docker Compose)

For local development and portfolio demonstration, the system deploys via a multi-container **Docker Compose** topology:

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Primary Relational Database
  db:
    image: postgres:15-alpine
    container_name: cinemetrics_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-cinemetrics}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cinemetrics_secret}
      POSTGRES_DB: ${POSTGRES_DB:-cinemetrics_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cinemetrics -d cinemetrics_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - cinemetrics_net

  # FastAPI Backend & ML In-Process Inference
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cinemetrics_backend
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-cinemetrics}:${POSTGRES_PASSWORD:-cinemetrics_secret}@db:5432/${POSTGRES_DB:-cinemetrics_db}
      - TMDB_API_KEY=${TMDB_API_KEY}
      - YOUTUBE_DATA_API_KEY=${YOUTUBE_DATA_API_KEY}
      - MODEL_ARTIFACT_DIR=/app/ml_models
    ports:
      - "8000:8000"
    volumes:
      - ./ml/models/production:/app/ml_models:ro
    networks:
      - cinemetrics_net

  # React Single Page Application (Nginx Alpine)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cinemetrics_frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "80:80"
    networks:
      - cinemetrics_net

  # Local MLflow Experiment Tracking Server
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.11.0
    container_name: cinemetrics_mlflow
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlflow/mlruns
    command: mlflow server --backend-store-uri sqlite:////mlflow/mlruns/mlflow.db --default-artifact-root /mlflow/mlruns/artifacts --host 0.0.0.0 --port 5000
    networks:
      - cinemetrics_net

volumes:
  postgres_data:

networks:
  cinemetrics_net:
    driver: bridge
```

---

## 3. Zero-Cost Cloud Deployment Blueprint

For a public web deployment, the monolithic stack seamlessly decomposes into three complimentary free cloud services:

```
┌──────────────────────────────────────┐
│  FRONTEND: Vercel Free Tier          │
│  • Edge CDN Global Distribution      │◄─── Browser Users
│  • Automatic GitHub Branch Deploys   │
└──────────────────┬───────────────────┘
                   │ HTTPS API Calls (/api/v1/...)
                   ▼
┌──────────────────────────────────────┐
│  BACKEND: Fly.io / Render Free Tier  │
│  • FastAPI ASGI Worker Container     │
│  • In-Memory CatBoost Model (<250MB) │
│  • APScheduler Background Jobs       │
└──────────────────┬───────────────────┘
                   │ Secure Connection Pooling
                   ▼
┌──────────────────────────────────────┐
│  DATABASE: Supabase Free Tier        │
│  • Managed PostgreSQL 15 Instance    │
│  • 500MB Table Storage + Backups     │
└──────────────────────────────────────┘
```

### 3.1 Frontend on Vercel
- **Configuration**: `frontend/vercel.json` rewrites client-side routes to `index.html`.
- **Build Command**: `npm run build` targeting Vite's optimized static bundle in `dist/`.
- **Cost**: **$0.00 / month** (Includes custom domain support and automatic SSL).

### 3.2 Backend API on Fly.io / Render
- **Configuration**: Packaged into a lightweight Alpine-based Docker container.
- **Resource Allocation**: Single shared-CPU VM with 512MB RAM comfortably executes FastAPI, Pydantic, and CatBoost inference.
- **Cost**: **$0.00 / month** on Fly.io free resource tier or Render free web service.

### 3.3 Managed Database on Supabase Free Tier
- **Database Engine**: Official PostgreSQL 15 with native extensions (`uuid-ossp`, `pg_trgm`).
- **Connection Strategy**: Uses Supabase Transaction Connection Pooling via port 6543 to handle async FastAPI client connections without exhausting database socket limits.
- **Cost**: **$0.00 / month** (500MB free database storage comfortably accommodates >15,000 films and snapshots).

---

## 4. Environment Configuration & Profile Management

CineMetrics uses three strict environment profiles:

| Variable | Development (`.env.dev`) | Local Docker (`.env.docker`) | Production Cloud (`.env.prod`) |
|---|---|---|---|
| `ENVIRONMENT` | `development` | `production` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://localhost:5432/cinemetrics_dev` | `postgresql+asyncpg://db:5432/cinemetrics_db` | `postgresql+asyncpg://user:pass@db.supabase.co:6543/postgres` |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | `["http://localhost:80"]` | `["https://cinemetrics.vercel.app"]` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `ENABLE_BACKGROUND_JOBS` | `false` | `true` | `true` |

---

## 5. Database Migrations & Initial Cold-Start Seeding

1. **Alembic Schema Execution**:
   ```bash
   # Apply migrations up to current head
   alembic upgrade head
   ```
2. **Cold-Start Seed Script (`backend/scripts/seed_database.py`)**:
   - Ingests canonical genres and primary production company tiers.
   - Populates a curated core catalogue of 500 benchmark Indian and Hollywood releases with pre-computed feature snapshots and baseline predictions, ensuring the platform presents a rich, functional experience immediately upon deployment.

---

## 6. Production Readiness & Operational Checklist

Before presenting the deployed platform publicly:
- [ ] 1. **Secret Leak Audit**: Verified `.env` and API keys are completely excluded from Git via `git status` and git history scans.
- [ ] 2. **CORS Hardening**: Verified `CORS_ORIGINS` restricts access strictly to the production frontend domain.
- [ ] 3. **Model Artifact Integrity**: Verified production CatBoost binary (`.cbm`) matches the latest MLflow registered model SHA.
- [ ] 4. **Database Migration Sync**: Verified database schema is identical to `alembic current` state.
- [ ] 5. **SSL Certification**: HTTPS enforced across all frontend and API routes.
- [ ] 6. **Health Check Validation**: `GET /api/v1/health` returns `HTTP 200 OK` with database connected and model loaded.

---

## 7. Zero-Cost Observability & Health Monitoring

1. **Uptime Monitoring**:
   - Monitored via **UptimeRobot** (Free Plan).
   - Configured to ping `https://api.cinemetrics.ai/api/v1/health` every 5 minutes with automated email alerts if downtime occurs.
2. **Exception Tracking**:
   - Integrated with **Sentry** (Free Developer Plan: 5,000 free events/month).
   - Automatically captures uncaught Python backend exceptions and React frontend UI runtime errors with full stack traces.
3. **Rotating Log Output**:
   - Container logs stream to Docker stdout/stderr with automatic log rotation (`max-size: 50m`, `max-file: 3`) to prevent disk exhaustion.
