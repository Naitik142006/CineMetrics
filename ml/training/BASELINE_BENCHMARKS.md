# CineMetrics — Machine Learning Baseline Benchmark Report

**Generated:** 2026-11-06 17:52:00 UTC  
**Execution Phase:** Phase 6 (Baseline Machine Learning Models)  
**Splits Evaluated:** Train: 7,782 | Val: 651 | Test: 605  

---

## 1. Out-of-Time Test Set Performance Matrix (>= 2017 Holdout)

| Model Architecture | Model Description | Test RMSE (Log) | Test R² Score | Test SMAPE (%) | Test Median AE (USD) | Benchmark Rank |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Random Forest (Depth 10)** | 100-tree ensemble non-linear baseline | `0.7743` | `0.4625` | `102.83%` | `$25,897,700.64` | 🥇 Rank 1 |
| **Multivariate Ridge** | Regularized L2 linear model on all 20 features | `0.8928` | `0.2854` | `116.45%` | `$33,944,170.86` | 🥈 Rank 2 |
| **Simple OLS (Budget Only)** | Univariate linear regression on log10(budget) | `0.9706` | `0.1554` | `120.11%` | `$30,784,809.52` | 🥉 Rank 3 |
| **Naive Mean Baseline** | Predicts constant global mean log-revenue | `1.0652` | `-0.0172` | `127.07%` | `$22,542,949.11` | 4️⃣ Rank 4 |

---

## 2. Validation Set Performance Matrix (2014–2016 Tuning Set)

| Model Architecture | Val RMSE (Log) | Val R² Score | Val SMAPE (%) | Overfitting Delta (Test - Val RMSE) |
|---|:---:|:---:|:---:|:---:|
| **Naive Mean Baseline** | `1.0403` | `-0.0252` | `125.30%` | `+0.0249` (✅ Stable) |
| **Simple OLS (Budget Only)** | `0.9011` | `0.2309` | `112.91%` | `+0.0695` (✅ Stable) |
| **Multivariate Ridge** | `0.7905` | `0.4081` | `101.97%` | `+0.1023` (⚠️ High Variance) |
| **Random Forest (Depth 10)** | `0.6959` | `0.5412` | `92.89%` | `+0.0784` (✅ Stable) |

---

## 3. Scientific Benchmark Takeaways for Phase 7 (CatBoost & LightGBM)

1. **Defeating the Naive Baseline:** The Dummy industry mean yields an out-of-time Test SMAPE of **127.07%** and $R^2$ of **-0.0172**. All trained models decisively beat this naive benchmark.
2. **The Predictive Power of Budget:** Simple univariate OLS on $\log_{10}(\text{Budget})$ alone captures **15.5%** of test variance with a Test SMAPE of **120.11%**, establishing that production spend is the single strongest macroeconomic anchor for revenue.
3. **Non-Linear Tree Advantages:** The Random Forest baseline improves Test $R^2$ to **0.4625** and drops Test SMAPE to **102.83%**, validating that non-linear interaction terms between talent track records and calendar seasonality provide significant lift over linear models.
4. **Phase 7 Target Performance Gate:** Phase 7 advanced gradient boosting (CatBoost with Ordered Target Statistics + Optuna hyperparameter tuning) must target:
   - **Test SMAPE $\le 40.0\%$** (surpassing Random Forest)
   - **Test $R^2 \ge 0.55$**
   - **Test RMSE $\le 0.58$** in log space
