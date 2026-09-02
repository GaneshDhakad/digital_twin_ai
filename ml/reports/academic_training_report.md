# Academic Model Training Report

## 1. Dataset
- **Name**: academic_clean.csv
- **Rows**: 80000
- **Features**: 32

## 2. Target
- **Target Variable**: exam_score
- **Problem Type**: Regression

## 3. Features
- **Numerical**: 20 features
- **Categorical**: 12 features

## 4. Removed Features
No features were removed initially, as no explicit ID columns were detected.

## 5. Leakage Checks
No obvious target leakage was detected. Features like `study_efficiency` and `wellbeing_score` were retained as they are predictive indicators rather than direct algebraic derivations of `exam_score`.

## 6. Train/Validation/Test Split
- **Train**: 56000 samples
- **Validation**: 12000 samples
- **Test**: 12000 samples
- **Method**: Random split (random_state=42)

## 7. Candidate Models
- LinearRegression
- Ridge
- Lasso
- RandomForestRegressor
- ExtraTreesRegressor
- GradientBoostingRegressor
- XGBRegressor (if available)

## 8. Cross-Validation & Validation Results
- **GradientBoostingRegressor**: CV RMSE=4.1533, Val RMSE=4.1105
- **Ridge**: CV RMSE=4.1858, Val RMSE=4.1396
- **LinearRegression**: CV RMSE=4.1861, Val RMSE=4.1406
- **RandomForestRegressor**: CV RMSE=4.2269, Val RMSE=4.1620
- **ExtraTreesRegressor**: CV RMSE=4.2454, Val RMSE=4.1745
- **Lasso**: CV RMSE=4.3015, Val RMSE=4.2378
- **XGBRegressor**: CV RMSE=4.2816, Val RMSE=4.2382

## 9. Hyperparameter Tuning
We evaluated models using default/random_state settings initially to establish baselines, and selected the best performing model directly for this iteration.

## 10. Final Test Results (on GradientBoostingRegressor)
- **Test RMSE**: 4.1317
- **Test MAE**: 3.2088
- **Test R2**: 0.8756

## 11. Best Model
- **Selected**: GradientBoostingRegressor

## 12. Why it was selected
It achieved the lowest Validation RMSE (4.1105) among all tested candidate models.

## Top 5 Features:
9. previous_gpa (0.9990)
20. wellbeing_score (0.0001)
5. attendance_percentage (0.0001)
19. digital_distraction_hours (0.0001)
11. stress_level (0.0001)
