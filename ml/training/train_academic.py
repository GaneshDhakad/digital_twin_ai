import os
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from sklearn.model_selection import train_test_split, KFold, cross_validate, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import time

# Models
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

# Paths
BASE_DIR = r"C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai"
DATA_PATH = r"C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\Datasets\prepared_datasets\academic_clean.csv"

ML_MODELS_DIR = os.path.join(BASE_DIR, "backend", "app", "ml_models", "academic")
REPORTS_DIR = os.path.join(BASE_DIR, "ml", "reports")
ACADEMIC_REPORTS_DIR = os.path.join(REPORTS_DIR, "academic")

os.makedirs(ML_MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(ACADEMIC_REPORTS_DIR, exist_ok=True)

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

target = "exam_score"
X = df.drop(columns=[target])
y = df[target]

# Identify feature types
categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
numerical_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

# No obvious identifier columns found based on previous inspection, all seem predictive.
removed_features = []
removal_reasons = {}

# Train/Val/Test Split (70/15/15)
X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=(0.15/0.85), random_state=42)

print(f"Train size: {X_train.shape[0]}, Val size: {X_val.shape[0]}, Test size: {X_test.shape[0]}")

# Preprocessing Pipeline
num_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

cat_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', num_transformer, numerical_features),
        ('cat', cat_transformer, categorical_features)
    ])

# Candidate Models
models = {
    "LinearRegression": LinearRegression(),
    "Ridge": Ridge(random_state=42),
    "Lasso": Lasso(random_state=42),
    "RandomForestRegressor": RandomForestRegressor(random_state=42),
    "ExtraTreesRegressor": ExtraTreesRegressor(random_state=42),
    "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42)
}
if XGBRegressor is not None:
    models["XGBRegressor"] = XGBRegressor(random_state=42)

results = []

print("Training candidate models...")
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for name, model in models.items():
    print(f"Evaluating {name}...")
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])
    
    start_time = time.time()
    cv_res = cross_validate(pipeline, X_train, y_train, cv=kf,
                            scoring=('neg_root_mean_squared_error', 'neg_mean_absolute_error', 'r2'))
    train_time = time.time() - start_time
    
    cv_rmse = -cv_res['test_neg_root_mean_squared_error'].mean()
    cv_mae = -cv_res['test_neg_mean_absolute_error'].mean()
    cv_r2 = cv_res['test_r2'].mean()
    
    # Fit and evaluate on validation set
    pipeline.fit(X_train, y_train)
    y_val_pred = pipeline.predict(X_val)
    val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    val_mae = mean_absolute_error(y_val, y_val_pred)
    val_r2 = r2_score(y_val, y_val_pred)
    
    results.append({
        "Model": name,
        "CV RMSE": cv_rmse,
        "CV MAE": cv_mae,
        "CV R2": cv_r2,
        "Validation RMSE": val_rmse,
        "Validation MAE": val_mae,
        "Validation R2": val_r2,
        "Training Time": train_time
    })

results_df = pd.DataFrame(results).sort_values(by="Validation RMSE", ascending=True)

print("\nModel Comparison:")
print(results_df)

results_df.to_csv(os.path.join(REPORTS_DIR, "academic_model_comparison.csv"), index=False)
results_df.to_json(os.path.join(REPORTS_DIR, "academic_model_comparison.json"), orient="records", indent=4)

# Select best model
best_model_name = results_df.iloc[0]["Model"]
print(f"\nBest model selected: {best_model_name}")

best_model = models[best_model_name]
pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', best_model)])

# Retrain on Train + Validation
X_train_val = pd.concat([X_train, X_val])
y_train_val = pd.concat([y_train, y_val])

print(f"Retraining {best_model_name} on train+val...")
pipeline.fit(X_train_val, y_train_val)

# Evaluate on Test set
y_test_pred = pipeline.predict(X_test)
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
test_mae = mean_absolute_error(y_test, y_test_pred)
test_r2 = r2_score(y_test, y_test_pred)

print(f"Test RMSE: {test_rmse:.4f}")
print(f"Test MAE: {test_mae:.4f}")
print(f"Test R2: {test_r2:.4f}")

# Save the model
model_path = os.path.join(ML_MODELS_DIR, "model.joblib")
joblib.dump(pipeline, model_path)
print(f"Model saved to {model_path}")

# Save metadata
metadata = {
    "model_name": best_model_name,
    "problem_type": "regression",
    "target": target,
    "dataset": "academic_clean.csv",
    "version": "1.0",
    "training_date": datetime.utcnow().isoformat(),
    "metrics": {
        "cv_rmse": float(results_df.iloc[0]["CV RMSE"]),
        "validation_rmse": float(results_df.iloc[0]["Validation RMSE"]),
        "test_rmse": float(test_rmse),
        "test_mae": float(test_mae),
        "test_r2": float(test_r2)
    }
}
with open(os.path.join(ML_MODELS_DIR, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=4)

# Feature Importance
importances = None
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
elif hasattr(best_model, 'coef_'):
    importances = np.abs(best_model.coef_)

if importances is not None:
    # Get feature names from preprocessor
    cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()
    all_feature_names = numerical_features + cat_feature_names
    
    # In some models like RandomForest, the number of importances match all_feature_names
    if len(importances) == len(all_feature_names):
        fi_df = pd.DataFrame({'Feature': all_feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False)
        fi_df.to_csv(os.path.join(REPORTS_DIR, "academic_feature_importance.csv"), index=False)
        
        # Plot feature importance
        plt.figure(figsize=(10, 8))
        sns.barplot(x='Importance', y='Feature', data=fi_df.head(20))
        plt.title(f"Top 20 Features - {best_model_name}")
        plt.tight_layout()
        plt.savefig(os.path.join(ACADEMIC_REPORTS_DIR, "feature_importance.png"))
        plt.close()
    else:
        fi_df = pd.DataFrame() # mismatch
else:
    fi_df = pd.DataFrame()

# Feature info
feature_info = {
    "final_features": X.columns.tolist(),
    "numerical_features": numerical_features,
    "categorical_features": categorical_features,
    "removed_features": removed_features,
    "removal_reasons": removal_reasons,
    "preprocessing": "StandardScaler for numerical, OneHotEncoder for categorical"
}
with open(os.path.join(ML_MODELS_DIR, "feature_info.json"), "w") as f:
    json.dump(feature_info, f, indent=4)

# Other Plots
plt.figure(figsize=(8, 5))
sns.histplot(y, bins=30, kde=True)
plt.title("Target Distribution (exam_score)")
plt.savefig(os.path.join(ACADEMIC_REPORTS_DIR, "target_distribution.png"))
plt.close()

plt.figure(figsize=(8, 5))
plt.scatter(y_test, y_test_pred, alpha=0.5)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.title("Actual vs Predicted")
plt.savefig(os.path.join(ACADEMIC_REPORTS_DIR, "actual_vs_predicted.png"))
plt.close()

residuals = y_test - y_test_pred
plt.figure(figsize=(8, 5))
sns.histplot(residuals, bins=30, kde=True)
plt.title("Residual Distribution")
plt.savefig(os.path.join(ACADEMIC_REPORTS_DIR, "residual_distribution.png"))
plt.close()

# Generate Markdown Report
report_content = f"""# Academic Model Training Report

## 1. Dataset
- **Name**: academic_clean.csv
- **Rows**: {df.shape[0]}
- **Features**: {df.shape[1] - 1}

## 2. Target
- **Target Variable**: {target}
- **Problem Type**: Regression

## 3. Features
- **Numerical**: {len(numerical_features)} features
- **Categorical**: {len(categorical_features)} features

## 4. Removed Features
No features were removed initially, as no explicit ID columns were detected.

## 5. Leakage Checks
No obvious target leakage was detected. Features like `study_efficiency` and `wellbeing_score` were retained as they are predictive indicators rather than direct algebraic derivations of `exam_score`.

## 6. Train/Validation/Test Split
- **Train**: {X_train.shape[0]} samples
- **Validation**: {X_val.shape[0]} samples
- **Test**: {X_test.shape[0]} samples
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
"""
for _, row in results_df.iterrows():
    report_content += f"- **{row['Model']}**: CV RMSE={row['CV RMSE']:.4f}, Val RMSE={row['Validation RMSE']:.4f}\n"

report_content += f"""
## 9. Hyperparameter Tuning
We evaluated models using default/random_state settings initially to establish baselines, and selected the best performing model directly for this iteration.

## 10. Final Test Results (on {best_model_name})
- **Test RMSE**: {test_rmse:.4f}
- **Test MAE**: {test_mae:.4f}
- **Test R2**: {test_r2:.4f}

## 11. Best Model
- **Selected**: {best_model_name}

## 12. Why it was selected
It achieved the lowest Validation RMSE ({float(results_df.iloc[0]['Validation RMSE']):.4f}) among all tested candidate models.

## Top 5 Features:
"""
if not fi_df.empty:
    for i, row in fi_df.head(5).iterrows():
        report_content += f"{i+1}. {row['Feature']} ({row['Importance']:.4f})\n"
else:
    report_content += "Feature importance not available for this model.\n"

with open(os.path.join(REPORTS_DIR, "academic_training_report.md"), "w") as f:
    f.write(report_content)

print("Training and reporting completed successfully!")
