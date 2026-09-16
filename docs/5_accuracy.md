# ML Model Accuracy & Performance
**Digital Twin AI (TWIN.OS)**
*September 2026 | Source of truth: `backend/app/ml_models/` metadata.json + training reports in `ml/reports/`*

> **Important:** All metrics below are from the actual trained model files deployed in this repository. No metrics are fabricated or estimated.

---

## 1. Model Registry Overview

All deployed models live in `backend/app/ml_models/<domain>/` and are loaded via `model_loader.py`. The loader caches models in memory after the first load.

| Domain | Model Class | Target | Problem Type | Status |
|---|---|---|---|---|
| academic | GradientBoostingRegressor | exam_score | Regression | ✅ Active |
| lifestyle | GradientBoostingClassifier | sleep_disorder | Classification | ✅ Active |
| financial | RandomForestRegressor | disposable_income | Regression | ✅ Active |
| forecasting | XGBRegressor | next_month_spending | Regression | ✅ Active |
| fitness | DecisionTreeClassifier | activity_level | Classification | ❌ Not Exposed (quality too low) |

---

## 2. Academic Model (GradientBoostingRegressor)

**Target:** `exam_score` (continuous numeric 0–100)

**Dataset:** `academic_clean.csv` — 80,000 student records, 32 features

**Candidate Models Compared:**
| Model | CV RMSE | Val RMSE |
|---|---|---|
| **GradientBoostingRegressor** | **4.1533** | **4.1105** ← Champion |
| Ridge | 4.1858 | 4.1396 |
| LinearRegression | 4.1861 | 4.1406 |
| RandomForestRegressor | 4.2269 | 4.1620 |
| ExtraTreesRegressor | 4.2454 | 4.1745 |
| Lasso | 4.3015 | 4.2378 |
| XGBRegressor | 4.2816 | 4.2382 |

**Final Test Metrics (Champion):**
- Test RMSE: `4.1317`
- Test MAE: `3.2088`
- Test R²: `0.8756`

**Top 5 Predictive Features:**
1. `previous_gpa` (dominant weight ≈ 0.999)
2. `wellbeing_score`
3. `attendance_percentage`
4. `digital_distraction_hours`
5. `stress_level`

**Model file:** `backend/app/ml_models/academic/model.joblib` (197 KB)
**Training date:** 2026-08-12

**Preprocessing:** StandardScaler for 20 numerical features, OneHotEncoder for 12 categorical features. Both are part of the stored sklearn Pipeline.

---

## 3. Lifestyle Model (GradientBoostingClassifier)

**Target:** `sleep_disorder` — classification into **3 classes**:
- `Normal` — no significant sleep-related pattern risk
- `Insomnia` — pattern consistent with insomnia profile
- `Sleep Apnea` — pattern consistent with sleep apnea profile

> ⚠️ **These are project classification labels, NOT clinical diagnoses.** Labels were generated from rule-based reference ranges on lifestyle data, not from clinical records.

**Dataset:** `lifestyle_clean.csv` — 374 records, 13 features

**Final Test Metrics (Champion):**
- Test Accuracy: `0.9733`
- Test Precision (macro): `0.9852`
- Test Recall (macro): `0.9710`
- Test F1 (macro): **`0.9773`**

**Features Used:**
- Numerical: `age`, `sleep_hours`, `sleep_quality`, `physical_activity_level`, `stress_level`, `heart_rate`, `daily_steps`, `activity_sleep_balance`, `lifestyle_risk_score`
- Categorical: `gender`, `occupation`, `bmi_category`, `blood_pressure`

**Model file:** `backend/app/ml_models/lifestyle/model.joblib` (7 KB, very small dataset)
**Training date:** 2026-09-04, version 2.0

---

## 4. Financial Model (RandomForestRegressor)

**Target:** `disposable_income` (monthly disposable income prediction)

**Key Metric:**
- RMSE: `4679.92`

**Model file:** `backend/app/ml_models/financial/model.joblib`

---

## 5. Forecasting Model (XGBRegressor)

**Target:** `next_month_spending` (total spending in the following month)

**Dataset:** `transaction_forecasting_clean.csv`

**Candidate Models Compared:**
- XGBRegressor → **Champion**
- RandomForestRegressor → excluded (took ~1181s for 3-fold CV, marginal improvement)
- Ridge → used as baseline

**Final Test Metrics:**
- 5-fold TimeSeriesCV RMSE: `1237.28`
- Validation RMSE: `1197.74`
- Test RMSE: `1207.04`
- Test MAE: `898.40`
- Test R²: `0.8595`

**Model file:** `backend/app/ml_models/forecasting/model.joblib`

---

## 6. Fitness Model (NOT Exposed)

**Target:** `activity_level` (classification)
**Model:** DecisionTreeClassifier
**F1 Score:** `0.2448` — Very low quality. Deliberately excluded from the API.
**File:** `backend/app/ml_models/fitness/model.joblib` (exists but not served)

---

## 7. Champion/Challenger Process

The system employs a Champion/Challenger strategy:

1. Multiple candidate algorithms are trained on identical data splits.
2. Each is evaluated on CV and validation metrics.
3. The best performer is saved as `model.joblib` in the domain folder.
4. `metadata.json` records the winning algorithm and all metrics.
5. `model_loader.py` loads from this folder at startup.

Re-training does not require code changes — only replacing the `.joblib` file and updating `metadata.json`.

---

## 8. Model Drift Monitoring

Model drift is tracked via `model_registry.json` at `backend/app/ml_models/model_registry.json` and by comparing:
- `metadata.json` metrics at training time vs. live API prediction quality
- `PredictionCache` entries can be audited by administrators via the model registry UI

Currently no automated drift detection is implemented — this is a future scope item.
