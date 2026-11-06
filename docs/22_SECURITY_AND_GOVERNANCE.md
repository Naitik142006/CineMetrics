# CineMetrics — Security, Data Governance & Compliance Framework

**Document ID:** 22  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [API Specification](19_API_SPECIFICATION.md) | [Testing & Validation](23_TESTING_AND_VALIDATION.md) | [Final Technical Decisions](28_FINAL_TECHNICAL_DECISIONS.md)

---

## Table of Contents

1. [Security Architecture Principles](#1-security-architecture-principles)
2. [Secrets Management & Credential Hygiene](#2-secrets-management--credential-hygiene)
3. [Defensive Input Validation & Injection Prevention](#3-defensive-input-validation--injection-prevention)
4. [Authentication & Role-Based Access Control (RBAC)](#4-authentication--role-based-access-control-rbac)
5. [API Rate Limiting & Denial-of-Service Mitigation](#5-api-rate-limiting--denial-of-service-mitigation)
6. [Data Provenance, Licensing & External Source Attribution](#6-data-provenance-licensing--external-source-attribution)
7. [Legal & Ethical Boundaries of Data Acquisition](#7-legal--ethical-boundaries-of-data-acquisition)
8. [Privacy & Personally Identifiable Information (PII)](#8-privacy--personally-identifiable-information-pii)
9. [Structured Audit Logging & Data Retention Policies](#9-structured-audit-logging--data-retention-policies)
10. [Model Governance & Financial Disclaimer Safeguards](#10-model-governance--financial-disclaimer-safeguards)

---

## 1. Security Architecture Principles

CineMetrics treats security, licensing ethics, and algorithmic governance as first-class architectural concerns:
1. **Defense-in-Depth**: Multiple defensive barriers prevent data corruption, secret leakage, and SQL injection.
2. **Zero Commercial Infringement**: Strict adherence to free, non-commercial, and open-access licensing terms for all third-party data providers.
3. **Transparent Provenance**: Every predicted number and scraped data point retains full traceability back to its originating authority.
4. **Student Project Pragmatism**: Security controls are implemented cleanly using modern Python libraries (`pydantic`, `slowapi`, `passlib`) without requiring complex enterprise hardware security modules.

---

## 2. Secrets Management & Credential Hygiene

### 2.1 The Cardinal Rule of Secret Protection
**Under no circumstances are API keys, database credentials, or signing secrets committed to Git repositories.**

### 2.2 Environment Isolation
- Configuration is loaded into memory via `pydantic_settings.BaseSettings` from local `.env` files during development and OS environment variables in production.
- A public `.env.example` template provides dummy variable placeholders:
  ```env
  ENVIRONMENT=development
  DATABASE_URL=postgresql+asyncpg://cinemetrics_user:dev_password@localhost:5432/cinemetrics_db
  SECRET_KEY=replace_with_64_character_cryptographically_secure_random_hex
  TMDB_API_KEY=your_tmdb_v3_api_key_here
  YOUTUBE_DATA_API_KEY=your_google_cloud_youtube_api_key_here
  CORS_ORIGINS=["http://localhost:5173"]
  ```
- Git enforcement: The master `.gitignore` strictly ignores `.env`, `*.key`, `*.pem`, `kaggle.json`, and all secret directories.

---

## 3. Defensive Input Validation & Injection Prevention

1. **SQL Injection Elimination**:
   - CineMetrics enforces 100% parameterization via SQLAlchemy 2.0 ORM and `asyncpg`.
   - Raw string concatenation in SQL queries (`f"SELECT * FROM {table}"`) is strictly prohibited and flagged via automated `flake8-bandit` AST security scans in CI/CD.
2. **Cross-Site Scripting (XSS) Prevention**:
   - The React frontend inherently escapes untrusted text strings before rendering into the DOM.
   - Dynamic user-supplied HTML injection (`dangerouslySetInnerHTML`) is banned.
   - Standard security headers are returned on all HTTP responses:
     ```http
     X-Content-Type-Options: nosniff
     X-Frame-Options: DENY
     Content-Security-Policy: default-src 'self'; img-src 'self' https://image.tmdb.org;
     ```
3. **Path Traversal Protection**:
   - Local model loading strictly verifies that target file paths resolve within the pre-authorized `ml/models/production/` directory, preventing arbitrary filesystem read attacks.

---

## 4. Authentication & Role-Based Access Control (RBAC)

CineMetrics adopts a bifurcated access model:
- **Public Surface (Read-Only)**: Movie Explorer, Upcoming Releases Intelligence, Market Analytics, and What-If Simulations require **no user registration or API authentication**. This ensures maximum accessibility for portfolio evaluators and film enthusiasts.
- **Administrative Surface (Write & Ingestion)**: Administrative endpoints (`/api/v1/admin/*`) require a signed cryptographic JSON Web Token (JWT) transmitted via the `Authorization: Bearer <token>` header.

### RBAC Implementation Details:
- **Password Hashing**: Passwords stored using `bcrypt` (work factor 12) via `passlib`.
- **JWT Standard**: Signed using HMAC-SHA256 (`HS256`) with a 60-minute expiration window.
- **Admin Scope**: Only authenticated admin tokens can trigger manual ingestion jobs, modify canonical financial records, or trigger model rollback.

---

## 5. API Rate Limiting & Denial-of-Service Mitigation

To protect backend ASGI workers and prevent compute resource exhaustion:
- Implemented via `slowapi` utilizing an in-memory or Redis-backed sliding window token bucket:
  - **Public Search & Catalog**: 60 requests per minute per IP address.
  - **What-If Simulation Engine**: 15 requests per minute per IP address (computationally heavier).
  - **Admin Actions**: 10 requests per minute per IP.
- When an IP exceeds the threshold, the API responds with `HTTP 429 Too Many Requests` accompanied by a `Retry-After: 60` header.

---

## 6. Data Provenance, Licensing & External Source Attribution

CineMetrics strictly complies with the terms of service of all upstream data providers:

| Data Provider | Upstream License / Terms | CineMetrics Compliance & Attribution Mandate |
|---|---|---|
| **The Movie Database (TMDB)** | Free for non-commercial use with attribution | Mandatory footer attribution: *"This product uses the TMDB API but is not endorsed or certified by TMDB."* + TMDB logo. |
| **IMDb Non-Commercial Datasets** | Free non-commercial personal use | Data used strictly for academic research and portfolio demonstration. No resale or raw redistribution. Mandatory notice: *"Information courtesy of IMDb (https://www.imdb.com)."* |
| **YouTube Data API v3** | Google APIs Terms of Service | Strict adherence to daily quota (10,000 units/day). Trailing view counts refreshed at compliant intervals without permanent asset caching. |
| **Google Trends (Pytrends)** | Public search interest signals | Anonymized relative scores (0–100) sampled with conservative request throttling to respect server policies. |
| **Kaggle Public Datasets** | Varies (CC0 1.0, CC BY 4.0, ODbL) | Retains original creator attributions in `planning/RESEARCH_REFERENCES.md`. |
| **Indian Trade Portals (Sacnilk, etc.)**| Public reporting / fair use | Utilized strictly for factual reference data; collections marked with provenance tags and reliability disclaimers. |

---

## 7. Legal & Ethical Boundaries of Data Acquisition

1. **Scraping Ethics**:
   - CineMetrics prioritizes official REST APIs and publicly released bulk data dumps.
   - For supplementary trade data where official APIs do not exist, the engine strictly obeys `robots.txt` disallow directives and applies polite request throttling ($\ge 3.0\text{s}$ delay between requests) during off-peak hours.
2. **Copyrighted Material**:
   - CineMetrics **does not host or redistribute full copyrighted media** (no movie video streams, full-length scripts, or high-resolution photo archives).
   - Posters and backdrops are rendered as hotlinks pointing directly to TMDB's public CDN (`image.tmdb.org`).

---

## 8. Privacy & Personally Identifiable Information (PII)

- **End-User Privacy**: The CineMetrics MVP collects **zero personal user data**. There are no user sign-ups, no tracking cookies, and no third-party behavioral analytics scripts.
- **Public Talent Data**: The `persons` table stores strictly public professional biographical metadata (canonical name, public credits, primary profession). No private personal contact details or sensitive personal data is ever harvested.
- **Social Commentary Anonymization**: Sentiment analysis scripts strip usernames, IP addresses, and user handles from YouTube and Reddit commentary before text embeddings are computed.

---

## 9. Structured Audit Logging & Data Retention Policies

1. **Application Logging**:
   - Powered by `structlog`. Outputs JSON-formatted log lines with UTC timestamps, log levels, endpoint paths, client IP hashes, and latency metrics.
   - Log lines never record secrets, passwords, or raw API keys.
2. **Data Retention**:
   - `ingestion_jobs` and `ingestion_logs`: Retained for 90 days, then pruned via automated maintenance scripts.
   - `feature_snapshots` and `predictions`: Retained permanently to serve as the immutable scientific audit log of prediction accuracy over time.
   - `movie_history`: Permanent audit log tracking all human manual overrides and automated field updates.

---

## 10. Model Governance & Financial Disclaimer Safeguards

Because CineMetrics forecasts financial box-office collections, it implements formal model governance guardrails to prevent misinterpretation:

### Mandatory Visual & API Disclaimer:
Every prediction response and UI view presents a standardized disclaimer:
> **Notice:** *CineMetrics revenue predictions and success categories are probabilistic machine learning estimates generated from historical patterns. They do not constitute financial, investment, or commercial advice. Actual theatrical revenues depend on unpredictable external factors including final word-of-mouth, competitive counter-programming, and macroeconomic conditions.*

### Model Traceability:
Every generated prediction stores:
- `model_version_id`: Exact git-tagged model artifact SHA.
- `training_cutoff_date`: Verifies temporal boundary of the training data.
- `conformal_coverage_level`: Statistical uncertainty guarantee (e.g., 80% conformal bound).
- `data_completeness_score`: Quality score signaling whether the forecast is preliminary or refined.
