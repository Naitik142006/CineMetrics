# CineMetrics — Master Machine Learning Model Comparison Matrix

**Document ID:** PLN-03  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Machine Learning Research](../docs/10_MACHINE_LEARNING_RESEARCH.md) | [Model Selection](../docs/11_MODEL_SELECTION_AND_EVALUATION.md)

---

## 1. Revenue Regression Benchmark Matrix (Target: Real Worldwide Gross USD)

| Model Candidate | Algorithm Family | Framework | Categorical Handling | Key Hyperparameters | Test SMAPE (Expected) | Test $R^2$ (Expected) | Overfitting Risk | CPU Train Time (10k Rows) | Memory Footprint | Interpretability | Architectural Role | Status |
|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|---|---|:---:|
| **Mean Baseline** | Heuristic | NumPy | Ignored | None | $92.4\%$ | $0.00$ | None | $<1\text{s}$ | $<1\text{MB}$ | Trivial | Baseline Lower Bound | Planned |
| **Market Median Baseline** | Heuristic | NumPy | Market Partition | None | $85.4\%$ | $0.00$ | None | $<1\text{s}$ | $<1\text{MB}$ | Trivial | Baseline Lower Bound | Planned |
| **Linear Budget Rule** | Heuristic | Python | Ignored | Multiplier = 2.2x | $68.2\%$ | $0.18$ | None | $<1\text{s}$ | $<1\text{MB}$ | Complete | Industry Rule of Thumb | Planned |
| **5-Feature OLS** | Linear Model | Scikit-Learn | One-Hot (Top 10) | None | $59.4\%$ | $0.31$ | Low | $<2\text{s}$ | $<5\text{MB}$ | High (Coefficients) | **Complexity Gate** | Planned |
| **Ridge Regression (L2)** | Regularized Linear | Scikit-Learn | One-Hot Encoding | `alpha=10.0` | $58.1\%$ | $0.33$ | Low | $<2\text{s}$ | $<5\text{MB}$ | High (Coefficients) | Benchmark | Planned |
| **Lasso Regression (L1)** | Regularized Linear | Scikit-Learn | One-Hot Encoding | `alpha=0.1` | $58.5\%$ | $0.32$ | Low | $<2\text{s}$ | $<5\text{MB}$ | High (Feature Pruning)| Benchmark | Planned |
| **Random Forest Regressor** | Bagging Ensemble | Scikit-Learn | Target / Ordinal | `n_estimators=300, max_depth=12` | $46.8\%$ | $0.46$ | Moderate | $45\text{s}$ | $\sim 180\text{MB}$ | Medium (MDI) | Non-Linear Baseline | Planned |
| **Extra Trees Regressor** | Randomized Trees | Scikit-Learn | Target / Ordinal | `n_estimators=300, max_depth=14` | $47.5\%$ | $0.45$ | High | $30\text{s}$ | $\sim 200\text{MB}$ | Medium (MDI) | Benchmark | Planned |
| **HistGradientBoosting** | Histogram GBDT | Scikit-Learn | Ordinal / Native NaN | `max_iter=300, max_depth=8` | $42.5\%$ | $0.51$ | Moderate | $12\text{s}$ | $\sim 35\text{MB}$ | Medium (Permutation) | Fast Scikit Baseline | Planned |
| **XGBoost (Hist)** | Extreme Gradient Boost | DMLC XGBoost | One-Hot / Partition | `n_estimators=1000, lr=0.03, depth=6`| $41.2\%$ | $0.52$ | Moderate | $18\text{s}$ | $\sim 45\text{MB}$ | High (TreeSHAP) | Benchmark Candidate | Planned |
| **LightGBM Regressor** | Leaf-Wise GBDT | Microsoft LightGBM| Integer Categoricals | `n_estimators=1200, num_leaves=63, lr=0.03`| $39.4\%$ | $0.55$ | Moderate | **$8\text{s}$** | $\sim 25\text{MB}$ | High (TreeSHAP) | **Secondary Candidate**| Planned |
| **CatBoost Regressor** | Ordered GBDT | Yandex CatBoost | **Native Ordered Stats** | `iterations=1500, depth=6, lr=0.04, l2=5.0` | **$36.8\%$** | **$0.59$** | **Low** | $35\text{s}$ | $\sim 30\text{MB}$ | **High (Native SHAP)** | **PRIMARY SELECTION** | Planned |
| **Support Vector Regressor** | Kernel Method | Scikit-Learn | Scaled One-Hot | `C=10.0, gamma='scale', epsilon=0.1` | $54.2\%$ | $0.38$ | Low | $4\text{min}$ | $\sim 80\text{MB}$ | Low (Kernel Space) | Rejected (Slow) | Planned |
| **TabNet Deep Learning** | Sparse Attention NN | PyTorch-TabNet | Learned Embeddings | `n_d=32, n_a=32, n_steps=5, gamma=1.5` | $44.5\%$ | $0.48$ | High | $12\text{min}$ | $\sim 250\text{MB}$ | Low (Attention Masks)| Rejected (Poor ROI) | Planned |

---

## 2. Commercial Success Classification Benchmark Matrix (7-Tier Categories)

| Classifier Candidate | Framework | Class Weighting Strategy | Expected Macro $F_1$ | Expected PR-AUC (Macro) | Expected Quadratic Kappa ($\kappa_w$) | Brier Calibration Score | Architectural Role | Status |
|---|---|---|:---:|:---:|:---:|:---:|---|:---:|
| **Stratified Dummy Classifier**| Scikit-Learn | Empirical Prior | $0.14$ | $0.14$ | $0.00$ | $0.38$ | Lower Bound Baseline | Planned |
| **Multinomial Logistic Reg** | Scikit-Learn | `class_weight='balanced'` | $0.48$ | $0.42$ | $0.45$ | $0.26$ | Linear Baseline | Planned |
| **Random Forest Classifier** | Scikit-Learn | `class_weight='balanced'` | $0.59$ | $0.54$ | $0.58$ | $0.22$ | Bagging Baseline | Planned |
| **XGBoost Classifier** | DMLC XGBoost | Sample Weights via Inv-Freq | $0.62$ | $0.58$ | $0.62$ | $0.19$ | Benchmark Candidate | Planned |
| **LightGBM Classifier** | Microsoft | `class_weight='balanced'` | $0.64$ | $0.61$ | $0.64$ | $0.18$ | Secondary Candidate | Planned |
| **CatBoost Classifier** | Yandex | **`auto_class_weights='Balanced'`** | **$0.68$** | **$0.66$** | **$0.69$** | **$0.16$** | **PRIMARY SELECTION** | Planned |

---

## 3. Actual Evaluation Log (To be Populated During Phase 6, 7 & 8)

*This section will record real empirical holdout evaluation numbers when training scripts execute in Phase 7.*

| Evaluation Timestamp | Model Version SHA | Dataset Version Hash | Train SMAPE | Val SMAPE | Holdout Test SMAPE | Holdout Test $R^2$ | Macro $F_1$ | Quadratic Kappa $\kappa_w$ | Sign-Off Status |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| *Pending Phase 7* | - | - | - | - | - | - | - | - | Awaiting Phase 7 |
