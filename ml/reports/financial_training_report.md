# Financial Model Training Report

- **Dataset**: financial_clean.csv
- **Target**: disposable_income
- **Problem Type**: regression
- **Split Strategy**: 80/20 train/test split. Stratified if classification.
- **Leakage Checks**: Removed identified leaky/id columns.
- **Candidate Models**: LinearRegression, Ridge, RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
- **Best Model**: RandomForestRegressor
- **Final Test Score (RMSE)**: 4679.9225
- **Saved Model Path**: backend/app/ml_models\financial\model.joblib
