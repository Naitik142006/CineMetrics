# CineMetrics — Master REST API Endpoint Implementation Tracker

**Document ID:** PLN-06  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [API Specification](../docs/19_API_SPECIFICATION.md) | [Testing & Validation](../docs/23_TESTING_AND_VALIDATION.md)

---

## 1. Production API Endpoints Directory

| # | HTTP Method | Path | Description | Primary Target Phase | Target Latency (p95) | Authentication Scope | Implementation Status |
|---|:---:|---|---|:---:|:---:|:---:|:---:|
| 1 | `GET` | `/api/v1/movies/search` | Full-text and trigram fuzzy movie search with filters. | Phase 13 | $<60\text{ms}$ | Public (Rate Limited) | Planned |
| 2 | `GET` | `/api/v1/movies/{id}` | Complete analytical movie dossier and credits. | Phase 13 | $<50\text{ms}$ | Public | Planned |
| 3 | `GET` | `/api/v1/movies/{id}/similar` | 5–10 structurally comparable historical films. | Phase 13 | $<100\text{ms}$ | Public | Planned |
| 4 | `GET` | `/api/v1/movies/{id}/prediction` | Active ML forecast, intervals, and category probabilities. | Phase 13 | $<250\text{ms}$ | Public | Planned |
| 5 | `GET` | `/api/v1/movies/{id}/prediction/history`| Historical audit trail of prediction revisions. | Phase 13 | $<80\text{ms}$ | Public | Planned |
| 6 | `GET` | `/api/v1/movies/{id}/explanation` | Additive TreeSHAP local feature attribution waterfall. | Phase 13 | $<150\text{ms}$ | Public | Planned |
| 7 | `GET` | `/api/v1/upcoming` | Filterable list of upcoming theatrical releases. | Phase 13 | $<60\text{ms}$ | Public | Planned |
| 8 | `GET` | `/api/v1/upcoming/dashboard` | Aggregated payload for all 14 upcoming dashboard sections. | Phase 13 | $<180\text{ms}$ | Public | Planned |
| 9 | `GET` | `/api/v1/upcoming/highest-predicted` | Top 10 upcoming releases sorted by expected gross. | Phase 13 | $<50\text{ms}$ | Public | Planned |
| 10 | `GET` | `/api/v1/upcoming/most-anticipated`| Top releases ranked by digital engagement velocity. | Phase 13 | $<50\text{ms}$ | Public | Planned |
| 11 | `GET` | `/api/v1/upcoming/potential-blockbusters`| Films with Blockbuster category probability $>50\%$. | Phase 13 | $<50\text{ms}$ | Public | Planned |
| 12 | `GET` | `/api/v1/upcoming/high-risk` | High-budget releases with low expected budget recovery. | Phase 13 | $<50\text{ms}$ | Public | Planned |
| 13 | `POST`| `/api/v1/simulate/what-if` | In-memory counterfactual feature perturbation simulation. | Phase 15 | $<80\text{ms}$ | Public (Throttled) | Planned |
| 14 | `GET` | `/api/v1/analytics/actor/{id}` | Actor box-office track record, hit rates, and star power.| Phase 15 | $<80\text{ms}$ | Public | Planned |
| 15 | `GET` | `/api/v1/analytics/director/{id}` | Director historical yield, budget tier experience. | Phase 15 | $<80\text{ms}$ | Public | Planned |
| 16 | `GET` | `/api/v1/analytics/market` | Market trends, macro admissions, and genre shares. | Phase 15 | $<120\text{ms}$ | Public | Planned |
| 17 | `GET` | `/api/v1/model/performance` | Official validation benchmarks (SMAPE, $R^2$, Kappa). | Phase 15 | $<30\text{ms}$ | Public | Planned |
| 18 | `GET` | `/api/v1/model/versions` | List of registered production and archived model SHA artifacts.| Phase 15 | $<30\text{ms}$ | Public | Planned |
| 19 | `GET` | `/api/v1/health` | Comprehensive application, DB, and ML model health check. | Phase 13 | $<15\text{ms}$ | Public | Planned |
| 20 | `POST`| `/api/v1/admin/ingestion/trigger/{job}`| Manually dispatches background discovery or sync jobs. | Phase 13 | $<100\text{ms}$ | Admin (JWT Bearer) | Planned |
| 21 | `GET` | `/api/v1/admin/ingestion/jobs` | Inspection endpoint for scheduled job logs and failures. | Phase 13 | $<50\text{ms}$ | Admin (JWT Bearer) | Planned |
| 22 | `PUT` | `/api/v1/admin/movies/{id}` | Manual administrative metadata curation and override. | Phase 13 | $<80\text{ms}$ | Admin (JWT Bearer) | Planned |
| 23 | `POST`| `/api/v1/admin/auth/token` | Administrative JWT login and token generation. | Phase 13 | $<150\text{ms}$ | Public | Planned |

---

## 2. API Implementation Progress Summary

- **Total Endpoints Planned**: 23
- **Endpoints Implemented**: 0 (Planning Stage - Strict Implementation Embargo)
- **Target Implementation Window**: Phase 13 & Phase 15
- **Test Suite Location**: `backend/tests/api/`
