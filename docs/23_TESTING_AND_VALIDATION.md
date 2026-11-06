# CineMetrics — Comprehensive Testing, Validation & Verification Strategy

**Document ID:** 23  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Data Engineering Pipeline](07_DATA_ENGINEERING_PIPELINE.md) | [Model Selection](11_MODEL_SELECTION_AND_EVALUATION.md) | [API Specification](19_API_SPECIFICATION.md) | [Acceptance Criteria](29_ACCEPTANCE_CRITERIA.md)

---

## Table of Contents

1. [Testing Philosophy: The Multi-Tiered Verification Pyramid](#1-testing-philosophy-the-multi-tiered-verification-pyramid)
2. [Data Quality & Pipeline Integrity Test Suite (Pandera / Pytest)](#2-data-quality--pipeline-integrity-test-suite-pandera--pytest)
3. [Machine Learning Scientific Validation & Leakage Audits](#3-machine-learning-scientific-validation--leakage-audits)
4. [Backend API & Integration Test Suite (FastAPI / Pytest)](#4-backend-api--integration-test-suite-fastapi--pytest)
5. [Frontend Component, State & Accessibility Tests (Vitest / RTL)](#5-frontend-component-state--accessibility-tests-vitest--rtl)
6. [End-to-End User Journey Tests (Playwright)](#6-end-to-end-user-journey-tests-playwright)
7. [Automated Continuous Integration (CI/CD) Pipeline](#7-automated-continuous-integration-cicd-pipeline)
8. [Final Fifty-Item Project Acceptance Checklist](#8-final-fifty-item-project-acceptance-checklist)

---

## 1. Testing Philosophy: The Multi-Tiered Verification Pyramid

Because CineMetrics combines complex data engineering, machine learning inference, and a rich user interface, testing is organized into a formal multi-tiered verification pyramid:

```
                  ┌──────────────────────┐
                  │   E2E Browser (5%)   │  Playwright (User Flows)
                  ├──────────────────────┤
                  │ Integration (20%)    │  FastAPI TestClient + PostgreSQL
                  ├──────────────────────┤
                  │  ML & Data (35%)     │  Leakage Tests, Conformal Checks, Pandera
                  ├──────────────────────┤
                  │   Unit Tests (40%)   │  Pytest (Services, Math) & Vitest (React)
                  └──────────────────────┘
```

- **Target Coverage**: $\ge 80\%$ statement coverage for backend services; $\ge 75\%$ coverage for frontend utility/state components; $100\%$ test coverage on temporal leakage prevention rules.

---

## 2. Data Quality & Pipeline Integrity Test Suite (Pandera / Pytest)

The automated data test suite (`tests/data/`) validates all data transformations across Bronze, Silver, and Gold layers:

```python
import pytest
import pandera as pa
from pandera.typing import Series

# Declarative Silver Layer Movie Schema
class MasterMovieSchema(pa.DataFrameModel):
    movie_id: Series[str] = pa.Field(unique=True, coerce=True)
    title: Series[str] = pa.Field(nullable=False)
    release_year: Series[int] = pa.Field(ge=1900, le=2030)
    runtime_minutes: Series[int] = pa.Field(ge=10, le=600, nullable=True)
    market_segment: Series[str] = pa.Field(isin=[
        "Bollywood", "Tollywood", "Kollywood", "Mollywood", "Sandalwood", "Hollywood", "Global"
    ])
    prediction_readiness_score: Series[int] = pa.Field(ge=0, le=100)

def test_silver_movie_schema_conformance(silver_movies_df):
    """Enforce strict schema validation on the unified movie dataset."""
    MasterMovieSchema.validate(silver_movies_df)

def test_financial_sanity_bounds(silver_financials_df):
    """Assert budgets and grosses obey physical real-world economic constraints."""
    # Worldwide gross must be >= domestic gross
    assert (silver_financials_df["worldwide_gross_real_usd"] >= 
            silver_financials_df["domestic_gross_nominal"].fillna(0)).all()
    # Budgets must be strictly positive
    assert (silver_financials_df["production_budget_real_usd"] > 0).all()

def test_currency_consistency(silver_financials_df):
    """Verify that normalized USD and INR conversions maintain realistic FX bounds."""
    # Historical USD to INR exchange rates between 2000 and 2024: 40.0 <= rate <= 86.0
    implied_rate = (silver_financials_df["india_gross_inr"] / 
                    silver_financials_df["worldwide_gross_real_usd"]).dropna()
    assert ((implied_rate >= 20.0) & (implied_rate <= 100.0)).all()

def test_zero_duplicate_entities(silver_movies_df):
    """Verify that deduplication removed all duplicate TMDB and IMDb keys."""
    assert silver_movies_df["tmdb_id"].dropna().is_unique
    assert silver_movies_df["imdb_id"].dropna().is_unique
```

---

## 3. Machine Learning Scientific Validation & Leakage Audits

The ML validation suite (`tests/ml/`) enforces statistical validity, temporal isolation, and calibration quality:

```python
def test_zero_lookahead_leakage(stage1_feature_matrix):
    """Verify that Stage 1 training features contain zero post-release or banned features."""
    banned_signals = [
        "imdb_rating", "vote_count", "lifetime_gross", 
        "first_week", "opening_day", "trailer_views", "sentiment"
    ]
    for col in stage1_feature_matrix.columns:
        for signal in banned_signals:
            assert signal not in col.lower(), f"Fatal Leakage: {col} present in Stage 1 matrix!"

def test_temporal_split_isolation(train_df, val_df, test_df):
    """Assert that train, validation, and holdout splits have strict zero date overlap."""
    max_train_date = train_df["release_date"].max()
    min_val_date = val_df["release_date"].min()
    max_val_date = val_df["release_date"].max()
    min_test_date = test_df["release_date"].min()
    
    assert max_train_date < min_val_date, "Train split leaks into Validation split!"
    assert max_val_date < min_test_date, "Validation split leaks into Test split!"

def test_regression_benchmark_gates(trained_catboost_model, holdout_test_set):
    """Verify that model beats baseline complexity gate on holdout data."""
    X_test, y_test = holdout_test_set
    preds = trained_catboost_model.predict(X_test)
    smape = calculate_smape(y_test, preds)
    
    # Must beat 40.0% SMAPE threshold on holdout test set
    assert smape <= 40.0, f"Model failed accuracy acceptance gate: SMAPE was {smape:.2f}%"

def test_conformal_coverage_empirical_guarantee(calibrated_conformal_model, holdout_test_set):
    """Assert that 80% conformal prediction intervals cover at least 78% of true test labels."""
    X_test, y_test = holdout_test_set
    intervals = calibrated_conformal_model.predict_interval(X_test, alpha=0.20)
    covered = (y_test >= intervals[:, 0]) & (y_test <= intervals[:, 1])
    empirical_coverage = covered.mean()
    
    assert empirical_coverage >= 0.78, f"Conformal coverage violation: {empirical_coverage:.2%}"

def test_shap_additivity_property(trained_model, sample_feature_vector):
    """Verify that TreeSHAP values sum exactly to the model's raw prediction."""
    explainer = shap.TreeExplainer(trained_model)
    shap_values = explainer(sample_feature_vector)
    
    expected_pred = trained_model.predict(sample_feature_vector)[0]
    reconstructed_pred = shap_values.base_values[0] + shap_values.values[0].sum()
    
    assert np.isclose(expected_pred, reconstructed_pred, atol=1e-4)
```

---

## 4. Backend API & Integration Test Suite (FastAPI / Pytest)

The integration test suite (`tests/api/`) uses FastAPI's `AsyncClient` backed by a clean test PostgreSQL database:

```python
@pytest.mark.asyncio
async def test_movie_search_endpoint(async_client):
    """Verify search returns matching titles with correct pagination envelope."""
    response = await async_client.get("/api/v1/movies/search?q=Kalki")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert any("Kalki" in m["title"] for m in data["data"])

@pytest.mark.asyncio
async def test_prediction_endpoint_structure(async_client, sample_movie_uuid):
    """Verify /prediction returns all required forecast, milestone, and interval fields."""
    response = await async_client.get(f"/api/v1/movies/{sample_movie_uuid}/prediction")
    assert response.status_code == 200
    payload = response.json()
    assert "forecast" in payload
    assert "success_classification" in payload
    assert "financial_risk" in payload
    assert payload["forecast"]["worldwide_gross"]["expected_inr_crores"] > 0

@pytest.mark.asyncio
async def test_what_if_simulation_latency(async_client, sample_movie_uuid):
    """Verify What-If simulation executes within the <250ms SLA budget."""
    payload = {
        "base_movie_id": sample_movie_uuid,
        "overrides": {"budget_nominal": 2000000000, "is_cultural_festival_release": True}
    }
    start_time = time.perf_counter()
    response = await async_client.post("/api/v1/simulate/what-if", json=payload)
    elapsed = time.perf_counter() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.250, f"Simulation exceeded SLA: Took {elapsed:.3f}s"

@pytest.mark.asyncio
async def test_rate_limiting_enforcement(async_client):
    """Assert that flooding public endpoints triggers HTTP 429 Too Many Requests."""
    for _ in range(65):
        res = await async_client.get("/api/v1/movies/search?q=test")
    assert res.status_code == 429
```

---

## 5. Frontend Component, State & Accessibility Tests (Vitest / RTL)

The frontend test suite (`frontend/src/__tests__/`) executes via **Vitest** and **React Testing Library**:

1. **`MovieCard.test.tsx`**:
   - Asserts poster art renders with correct `alt` text.
   - Verifies fallback thumbnail displays when `poster_path` is null.
   - Asserts predicted gross formats cleanly in INR Crores (`₹1,040 Cr`) or USD Millions (`$125M`).
2. **`PredictionIntervalBar.test.tsx`**:
   - Asserts pessimistic, expected, and optimistic interval ticks are positioned proportionally along the SVG gradient bar.
3. **`WhatIfSimulator.test.tsx`**:
   - Simulates user dragging budget slider; asserts debounced API call dispatches and counterfactual prediction updates.
4. **Accessibility Auditing (axe-core)**:
   - Automated `axe-core` tests verify WCAG 2.1 AA compliance: all text elements satisfy the $4.5:1$ contrast ratio against the dark `#0A0A0F` background; all interactive controls possess ARIA labels.

---

## 6. End-to-End User Journey Tests (Playwright)

Automated headless browser tests (`tests/e2e/`) verify critical end-to-end user journeys:

- **Journey 1: Deep Analytical Investigation (Mode 1)**:
  - User visits landing page $\rightarrow$ enters `"Pushpa 2"` in Omnibox $\rightarrow$ selects result from dropdown $\rightarrow$ verifies dossier renders $\rightarrow$ toggles SHAP waterfall tab $\rightarrow$ opens What-If drawer $\rightarrow$ verifies simulated revenue updates.
- **Journey 2: Upcoming Intelligence Radar (Mode 2)**:
  - User clicks `"Upcoming Releases"` navigation link $\rightarrow$ applies `"Tollywood"` regional filter $\rightarrow$ verifies only Telugu releases are shown $\rightarrow$ sorts by `"Highest Predicted Gross"` $\rightarrow$ verifies leaderboard order.

---

## 7. Automated Continuous Integration (CI/CD) Pipeline

A lightweight **GitHub Actions** workflow (`.github/workflows/ci.yml`) executes on every commit:
1. **Lint & Security Gate**: `black --check`, `isort --check`, `flake8`, `bandit -r backend/`.
2. **Data & ML Verification**: Executes `pytest tests/data/` and `pytest tests/ml/`.
3. **Backend API Suite**: Boots test PostgreSQL container, runs Alembic migrations, executes `pytest tests/api/`.
4. **Frontend Test Suite**: `npm run lint`, `npm run test:vitest`, `npm run build`.

---

## 8. Final Fifty-Item Project Acceptance Checklist

```markdown
### A. Data Engineering & Integrity (Items 1–10)
- [ ] 1. Raw API downloads checksum-verified and stored in partitioned Parquet.
- [ ] 2. Lineage metadata (_source_id, _retrieval_timestamp) present on 100% of rows.
- [ ] 3. Entity resolution links TMDB and IMDb IDs with >95% accuracy on benchmark set.
- [ ] 4. Exact zero duplicate records exist in the canonical movies table.
- [ ] 5. Currency engine standardizes all historical collections to 2024 constant USD.
- [ ] 6. Inflation engine applies valid monthly US and Indian CPI index deflation.
- [ ] 7. Missing budget imputation uses KNN tier classification without target leakage.
- [ ] 8. Target variables (worldwide gross, opening day) are never imputed.
- [ ] 9. Pydantic and Pandera schema validation gates execute with zero fatal errors.
- [ ] 10. Temporal feature snapshots are completely immutable and append-only.

### B. Machine Learning & Scientific Rigour (Items 11–20)
- [ ] 11. All training, validation, and holdout splits strictly chronological (zero random splits).
- [ ] 12. Complete absence of banned post-release signals in pre-release feature sets.
- [ ] 13. Candidate models (CatBoost, LightGBM, XGBoost) systematically benchmarked.
- [ ] 14. Primary CatBoost model achieves holdout test SMAPE <= 40.0%.
- [ ] 15. Complexity justification gate met: model beats 5-feature OLS baseline by >= 20%.
- [ ] 16. Quadratic weighted kappa (κ_w) >= 0.65 for success classification tiers.
- [ ] 17. 80% conformal prediction intervals achieve empirical coverage between 78% and 83%.
- [ ] 18. TreeSHAP feature attributions mathematically sum to raw model prediction.
- [ ] 19. Google MuRIL multilingual sentiment pipeline processes Romanized Indic text.
- [ ] 20. Production model serialized to native CatBoost .cbm format without pickle risk.

### C. Backend API & System Performance (Items 21–30)
- [ ] 21. FastAPI application boots cleanly with all models loaded into memory.
- [ ] 22. REST API endpoints strictly adhere to OpenAPI 3.1 specification contracts.
- [ ] 23. Catalog search responses resolve in < 60ms (p95).
- [ ] 24. Live prediction and SHAP waterfall responses resolve in < 250ms (p95).
- [ ] 25. What-If counterfactual simulation engine resolves in < 80ms.
- [ ] 26. Standardized RFC-7807 problem details envelopes returned for all errors.
- [ ] 27. Slowapi rate limiting actively enforces 60 req/min limits on public endpoints.
- [ ] 28. Ingestion workers scheduled via APScheduler run autonomously in background.
- [ ] 29. Structured JSON logging via structlog captures all request latencies.
- [ ] 30. Zero API keys, passwords, or secrets committed to repository.

### D. Frontend UI/UX & User Experience (Items 31–40)
- [ ] 31. Dark cinematic design system implemented matching the #0A0A0F aesthetic.
- [ ] 32. Movie Explorer renders comprehensive analytical dossier for any selected film.
- [ ] 33. Upcoming Releases dashboard displays all 14 curated analytical sections.
- [ ] 34. Dual-currency display seamlessly toggles between INR Crores and USD Millions.
- [ ] 35. Prediction interval bar clearly visualizes pessimistic, expected, and optimistic bands.
- [ ] 36. Local SHAP waterfall chart clearly explains positive and negative drivers.
- [ ] 37. Interactive What-If Simulator provides real-time slider controls and instant updates.
- [ ] 38. Prediction Readiness Score clearly communicates data maturity (Stages 1 to 5).
- [ ] 39. Responsive breakpoints verified across Mobile (375px), Tablet (768px), Desktop (1440px).
- [ ] 40. WCAG 2.1 AA accessibility standards verified with zero axe-core contrast violations.

### E. Governance, Ethics & Documentation (Items 41–50)
- [ ] 41. Mandatory financial prediction disclaimer visible across all prediction views.
- [ ] 42. Required TMDB and IMDb non-commercial attribution notices displayed in footer.
- [ ] 43. YouTube Data API daily usage monitored within compliant 10,000 unit quota.
- [ ] 44. Upstream robots.txt policies strictly obeyed during supplementary data collection.
- [ ] 45. Zero end-user PII collected or stored anywhere in the application.
- [ ] 46. Full 29-document technical specification suite complete in docs/ directory.
- [ ] 47. All 7 Mermaid architectural diagrams parse and render without syntax errors.
- [ ] 48. Private interview preparation guide verified stored outside Git repository.
- [ ] 49. End-to-end Playwright browser tests pass across all primary user journeys.
- [ ] 50. Project verified as 100% reproducible on standard consumer laptop hardware.
```
