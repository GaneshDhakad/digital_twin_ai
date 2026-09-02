# Forecasting Model Training Report

- Dataset: transaction_forecasting_clean.csv
- Target: next_month_spending
- Best model: XGBRegressor
- 5-fold TimeSeries CV RMSE: 1237.2756
- Validation RMSE: 1197.7359
- Test RMSE: 1207.0355
- Test MAE: 898.4003
- Test R2: 0.8595

RandomForestRegressor and ExtraTreesRegressor were excluded because the previous run showed Random Forest taking about 1181 seconds for 3-fold TimeSeries CV while Ridge had nearly the same RMSE.
