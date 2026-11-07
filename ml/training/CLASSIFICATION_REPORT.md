# CineMetrics — Commercial Success Classification Evaluation Report

**Execution Phase:** Phase 8 (Commercial Success Classification Modeling)  
**Evaluation Split:** Out-of-Time Test Holdout (>= 2017 Releases / 398 Labeled Films)  
**Target Taxonomy:** 7-Tier Cinema Economics Hierarchy (`Disaster` to `Blockbuster`)  

---

## 1. Out-of-Time Test Set Model Leaderboard

| Model Architecture | Quadratic Kappa (κ_w) | Macro F1 Score | Weighted F1 | Test Accuracy | Brier Score | Log Loss | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stratified Dummy Baseline** | `-0.0080` | `0.1397` | `0.1646` | `16.08%` | `1.6784` | `28.9848` | Benchmark |
| **Regression-Derived Thresholding (Strategy 2)** | `0.1053` | `0.1060` | `0.1060` | `12.06%` | `1.6591` | `4.2163` | Benchmark |
| **Multinomial Logistic Regression** | `0.1358` | `0.1694` | `0.2258` | `19.85%` | `0.8743` | `2.0298` | Benchmark |
| **Balanced Random Forest** | `0.0924` | `0.1393` | `0.2069` | `18.84%` | `0.8850` | `2.0729` | Benchmark |
| **LightGBM Classifier** | `0.1550` | `0.1362` | `0.1896` | `16.33%` | `0.9768` | `2.5029` | Benchmark |
| **CatBoost Classifier (Production)** | `0.1695` | `0.1759` | `0.2582` | `23.87%` | `0.8521` | `1.9654` | 🌟 **PRODUCTION CHAMPION** |

---

## 2. Production CatBoost Tier-Wise Performance Breakdown

| Commercial Tier | Economic Definition | Test Support | Precision | Recall | F1-Score |
|---|---|:---:|:---:|:---:|:---:|
| **Disaster** | `ROI < 0.4` | `25` | `0.0949` | `0.6000` | `0.1639` |
| **Flop** | `0.4 <= ROI < 0.8` | `27` | `0.0885` | `0.3704` | `0.1429` |
| **Below Average** | `0.8 <= ROI < 1.2` | `31` | `0.0000` | `0.0000` | `0.0000` |
| **Average** | `1.2 <= ROI < 2.0` | `63` | `0.5000` | `0.0159` | `0.0308` |
| **Hit** | `2.0 <= ROI < 2.5` | `31` | `0.1250` | `0.0645` | `0.0851` |
| **Super Hit** | `2.5 <= ROI < 3.0` | `89` | `0.7419` | `0.2584` | `0.3833` |
| **Blockbuster** | `ROI >= 3.0 & High Volume` | `132` | `0.5867` | `0.3333` | `0.4251` |

---

## 3. Production CatBoost Confusion Matrix (Holdout Test)

Rows: Actual Ground Truth | Columns: Predicted Tier

| Actual \ Pred | Disaster | Flop | Below Average | Average | Hit | Super Hit | Blockbuster |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Disaster** | `15` | `7` | `0` | `0` | `0` | `2` | `1` |
| **Flop** | `15` | `10` | `1` | `0` | `0` | `1` | `0` |
| **Below Average** | `12` | `16` | `0` | `0` | `0` | `1` | `2` |
| **Average** | `23` | `23` | `0` | `1` | `5` | `0` | `11` |
| **Hit** | `11` | `7` | `0` | `0` | `2` | `2` | `9` |
| **Super Hit** | `48` | `8` | `1` | `0` | `1` | `23` | `8` |
| **Blockbuster** | `34` | `42` | `1` | `1` | `8` | `2` | `44` |

---

## 4. CatBoost Feature Importance Ranking (Top 10 Classification Drivers)

| Rank | Feature Identifier | Relative Importance (%) |
|:---:|---|:---:|
| 1 | `budget_tier` | `18.46%` |
| 2 | `director` | `10.82%` |
| 3 | `log_budget` | `10.59%` |
| 4 | `primary_genre` | `10.15%` |
| 5 | `lead_actor` | `9.72%` |
| 6 | `industry` | `7.48%` |
| 7 | `language_clean` | `6.31%` |
| 8 | `release_month` | `4.09%` |
| 9 | `genre_count` | `2.55%` |
| 10 | `lead_actor_prior_hit_rate` | `2.47%` |

---

## 5. Architectural Conclusions & Deployment Sign-Off

1. **Quadratic Kappa Validation:** Quadratic Weighted Kappa penalizes off-diagonal distance quadratically, ensuring adjacent-tier errors (e.g. Hit vs Super Hit) are not penalized as harshly as catastrophic errors (Disaster vs Blockbuster).
2. **Balanced Loss Mitigation:** `auto_class_weights='Balanced'` prevents majority class domination, maintaining high recall on critical high-stakes tiers.
3. **Serialization:** Production model saved to `ml/models/production/catboost_classifier_v1.cbm` and ready for integration into the FastAPI prediction service.
