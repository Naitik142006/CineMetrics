# CineMetrics — RESTful API Specification (OpenAPI 3.1)

**Document ID:** 19  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [Database Specification](18_DATABASE_AND_ER_DIAGRAM.md) | [Testing & Validation](23_TESTING_AND_VALIDATION.md)

---

## Table of Contents

1. [API Design Principles & Standards](#1-api-design-principles--standards)
2. [Base URL, Protocol & Global Headers](#2-base-url-protocol--global-headers)
3. [Standard Error Handling & RFC-7807 Format](#3-standard-error-handling--rfc-7807-format)
4. [Pagination, Filtering & Sorting Standards](#4-pagination-filtering--sorting-standards)
5. [Complete Endpoint Specifications](#5-complete-endpoint-specifications)
   - 5.1 [Movie Catalog & Search Endpoints](#51-movie-catalog--search-endpoints)
   - 5.2 [Upcoming Releases & Dashboard Endpoints](#52-upcoming-releases--dashboard-endpoints)
   - 5.3 [Machine Learning Prediction & Explainability Endpoints](#53-machine-learning-prediction--explainability-endpoints)
   - 5.4 [Interactive What-If Simulation Endpoints](#54-interactive-what-if-simulation-endpoints)
   - 5.5 [Cinema Analytics & Talent Dossier Endpoints](#55-cinema-analytics--talent-dossier-endpoints)
   - 5.6 [Model Governance & System Health Endpoints](#56-model-governance--system-health-endpoints)
   - 5.7 [Admin & Data Ingestion Control Endpoints](#57-admin--data-ingestion-control-endpoints)
6. [Realistic Production JSON Payloads](#6-realistic-production-json-payloads)

---

## 1. API Design Principles & Standards

The CineMetrics API is built to industry RESTful standards using **FastAPI**:
- **Stateless & Deterministic**: Requests contain all information necessary for processing; model inference is deterministic for identical input vectors.
- **Strict Pydantic Validation**: Every request parameter and body payload is strictly typed and validated at the boundary before execution.
- **Fast Performance SLA**: 95th percentile response times $<60\text{ms}$ for catalog queries; $<250\text{ms}$ for on-the-fly ML predictions and SHAP waterfalls.
- **Automatic OpenAPI 3.1 Documentation**: Interactive Swagger documentation is automatically hosted at `/docs` and Redoc at `/redoc`.

---

## 2. Base URL, Protocol & Global Headers

- **Development Base URL**: `http://localhost:8000/api/v1`
- **Production Base URL**: `https://api.cinemetrics.ai/api/v1`
- **Protocol**: HTTPS / REST over HTTP/1.1 or HTTP/2
- **Standard Request Headers**:
  - `Accept: application/json`
  - `Content-Type: application/json`
- **Standard Response Headers**:
  - `Content-Type: application/json; charset=utf-8`
  - `X-Process-Time: 0.042s`

---

## 3. Standard Error Handling & RFC-7807 Format

All error responses return structured problem detail envelopes matching RFC-7807:

```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "The requested movie could not be located.",
    "status": 404,
    "details": {
      "movie_id": "c1a84f32-8419-4b16-831e-436f56d81234"
    },
    "timestamp": "2026-11-05T18:25:00Z"
  }
}
```

### Standard HTTP Status Codes Used:
- `200 OK`: Request succeeded; entity returned.
- `201 Created`: Entity successfully created (e.g., admin manual entry).
- `400 Bad Request`: Malformed parameters or schema validation failure.
- `404 Not Found`: Target entity ID does not exist.
- `422 Unprocessable Entity`: Semantic constraint failure (e.g. invalid date range).
- `429 Too Many Requests`: Rate limit exceeded.
- `503 Service Unavailable`: Model weights not loaded or external API outage.

---

## 4. Pagination, Filtering & Sorting Standards

All list endpoints support standard query parameters:
- `page`: 1-based page index (Default: `1`)
- `page_size`: Records per page (Default: `20`, Max: `100`)
- `sort_by`: Target column name (Default: `release_date`)
- `sort_order`: `asc` or `desc` (Default: `desc`)

### Standard Pagination Response Structure:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 1420,
    "total_pages": 71,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 5. Complete Endpoint Specifications

### 5.1 Movie Catalog & Search Endpoints

#### 1. Search Movies (Fuzzy & Multi-Attribute)
- **Method & Path**: `GET /movies/search`
- **Description**: Fast debounced full-text and trigram fuzzy search across titles, transliterations, and alternate titles.
- **Query Parameters**:
  - `q` (string, required): Search query string (e.g., `"Kalki"`, `"Jawan"`).
  - `market_segment` (string, optional): Filter by `Bollywood`, `Tollywood`, `Hollywood`, etc.
  - `release_year` (int, optional): Filter by release year.
  - `status` (string, optional): `upcoming`, `released`, or `all`.

#### 2. Get Movie Details (Analytical Dossier)
- **Method & Path**: `GET /movies/{movie_id}`
- **Description**: Retrieves full metadata, poster art, cast credits, verified financials, and latest prediction status.
- **Path Parameter**: `movie_id` (UUID, required).

#### 3. Get Similar Movies
- **Method & Path**: `GET /movies/{movie_id}/similar`
- **Description**: Returns 5–10 structurally comparable historical films based on genre embedding, budget tier, and talent star power.

---

### 5.2 Upcoming Releases & Dashboard Endpoints

#### 1. Get Upcoming Releases Feed
- **Method & Path**: `GET /upcoming`
- **Description**: Returns upcoming films filtered by temporal horizon and industry segment.
- **Query Parameters**:
  - `timeframe`: `week`, `month`, `year`, `all` (Default: `month`).
  - `market_segment`: `all`, `Bollywood`, `Tollywood`, `Kollywood`, `Hollywood`.
  - `min_readiness`: Minimum Prediction Readiness Score (0 to 100).

#### 2. Get Upcoming Releases Intelligence Dashboard
- **Method & Path**: `GET /upcoming/dashboard`
- **Description**: Aggregates all 14 curated dashboard sections (Top Earners, Blockbusters, High Risk, etc.) in a single high-speed payload.

---

### 5.3 Machine Learning Prediction & Explainability Endpoints

#### 1. Get Active Movie Prediction
- **Method & Path**: `GET /movies/{movie_id}/prediction`
- **Description**: Returns point revenue forecast, 80% & 95% conformal uncertainty intervals, success classification probability distribution, and lifecycle stage.

#### 2. Get SHAP Local Feature Explanation
- **Method & Path**: `GET /movies/{movie_id}/explanation`
- **Description**: Returns exact additive SHAP feature importance waterfall array (base value, feature names, individual revenue impacts in USD and INR).

#### 3. Get Historical Prediction Evolution
- **Method & Path**: `GET /movies/{movie_id}/prediction/history`
- **Description**: Retrieves audit trail of previous forecasts across lifecycle stages showing prediction drift over time.

---

### 5.4 Interactive What-If Simulation Endpoints

#### 1. Simulate Counterfactual Scenario
- **Method & Path**: `POST /simulate/what-if`
- **Description**: In-memory feature perturbation. Evaluates synthetic changes (modified budget, new director, shifted release date) and returns updated predictions in $<50\text{ms}$.
- **Request Body Schema**:
  ```json
  {
    "base_movie_id": "c1a84f32-8419-4b16-831e-436f56d81234",
    "overrides": {
      "budget_nominal": 2500000000,
      "lead_actor_id": "pers_789123",
      "release_date": "2024-11-01",
      "is_cultural_festival_release": true,
      "simulated_youtube_views_first_24h": 45000000
    }
  }
  ```

---

### 5.5 Cinema Analytics & Talent Dossier Endpoints

#### 1. Get Actor Historical Dossier
- **Method & Path**: `GET /analytics/actor/{person_id}`
- **Description**: Historical box-office track record, rolling star power index, genre hit rates, and career revenue curve.

#### 2. Get Director Historical Dossier
- **Method & Path**: `GET /analytics/director/{person_id}`
- **Description**: Career box-office averages, budget consistency score, and commercial hit ratio.

#### 3. Get Market Trend Analytics
- **Method & Path**: `GET /analytics/market`
- **Query Parameters**: `market_segment` (required), `start_year`, `end_year`.
- **Description**: Multi-year theatrical admissions, genre market shares, and inflation-adjusted macro yields.

---

### 5.6 Model Governance & System Health Endpoints

#### 1. Health Check
- **Method & Path**: `GET /health`
- **Response**: `{"status": "healthy", "database": "connected", "model_loaded": "catboost_v1.0.0"}`

#### 2. Model Performance Benchmarks
- **Method & Path**: `GET /model/performance`
- **Description**: Official validation metrics (Holdout SMAPE, $R^2$, Classification F1, Conformal Coverage).

---

### 5.7 Admin & Data Ingestion Control Endpoints

#### 1. Trigger Manual Data Ingestion Job
- **Method & Path**: `POST /admin/ingestion/trigger/{job_type}`
- **Description**: Manually dispatches `daily_discovery`, `buzz_update`, or `post_release_sync`.

#### 2. Manually Curate / Override Movie Record
- **Method & Path**: `PUT /admin/movies/{movie_id}`
- **Description**: Allows authenticated administrator to verify budgets or update disputed release dates.

---

## 6. Realistic Production JSON Payloads

### Sample Response: `GET /movies/{id}/prediction`
```json
{
  "movie_id": "c1a84f32-8419-4b16-831e-436f56d81234",
  "title": "Kalki 2898 AD",
  "prediction_stage": "stage_3_1m",
  "readiness_score": 92,
  "last_updated": "2026-11-05T12:00:00Z",
  "model_version": "catboost_global_v1.0.0",
  "currency_display": "INR",
  "forecast": {
    "worldwide_gross": {
      "expected_inr_crores": 1040.50,
      "expected_usd_millions": 125.36,
      "pessimistic_inr_crores": 880.20,
      "optimistic_inr_crores": 1260.80,
      "conformal_confidence": 0.80
    },
    "milestones": {
      "opening_day_inr_crores": 175.40,
      "opening_weekend_inr_crores": 450.00,
      "india_nett_lifetime_inr_crores": 620.00
    }
  },
  "success_classification": {
    "predicted_category": "Blockbuster",
    "probabilities": {
      "Blockbuster": 0.68,
      "Super Hit": 0.24,
      "Hit": 0.06,
      "Average": 0.02,
      "Below Average": 0.00,
      "Flop": 0.00,
      "Disaster": 0.00
    }
  },
  "financial_risk": {
    "estimated_budget_inr_crores": 600.00,
    "recovery_ratio_expected": 1.73,
    "break_even_status": "Highly Likely to Recover",
    "risk_level": "Moderate (High Absolute Budget Scale)"
  }
}
```

### Sample Response: `GET /movies/{id}/explanation`
```json
{
  "movie_id": "c1a84f32-8419-4b16-831e-436f56d81234",
  "base_value_inr_crores": 140.00,
  "final_prediction_inr_crores": 1040.50,
  "top_positive_factors": [
    {
      "feature_name": "lead_actor_avg_gross_last5",
      "feature_label": "Prabhas Star Power & Theatrical Track Record",
      "shap_impact_inr_crores": 380.20,
      "direction": "positive"
    },
    {
      "feature_name": "is_pan_india_release",
      "feature_label": "Simultaneous Multi-Language Pan-India Scale",
      "shap_impact_inr_crores": 210.50,
      "direction": "positive"
    },
    {
      "feature_name": "youtube_views_first_24h",
      "feature_label": "High Digital Trailer Engagement Velocity",
      "shap_impact_inr_crores": 85.00,
      "direction": "positive"
    }
  ],
  "top_negative_factors": [
    {
      "feature_name": "production_budget_real_usd",
      "feature_label": "Extremely High Production Cost Barrier (>₹600 Cr)",
      "shap_impact_inr_crores": -62.40,
      "direction": "negative"
    },
    {
      "feature_name": "competing_clash_star_power",
      "feature_label": "Clash Competition Density on Release Window",
      "shap_impact_inr_crores": -18.20,
      "direction": "negative"
    }
  ]
}
```
