import os
import json
import joblib
import time
import datetime
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, KFold, StratifiedKFold, TimeSeriesSplit, cross_validate
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

# Regressors
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor

# Classifiers
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

DATA_DIR = '../Datasets/prepared_datasets'
MODELS_DIR = 'backend/app/ml_models'
REPORTS_DIR = 'ml/reports'

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
for d in ['fitness', 'lifestyle', 'financial', 'forecasting']:
    os.makedirs(os.path.join(MODELS_DIR, d), exist_ok=True)

def get_preprocessor(numerical_cols, categorical_cols):
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ])
    return preprocessor

def get_regressors():
    return {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(),
        'RandomForestRegressor': RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42),
        'ExtraTreesRegressor': ExtraTreesRegressor(n_estimators=50, n_jobs=-1, random_state=42),
        'GradientBoostingRegressor': GradientBoostingRegressor(n_estimators=50, random_state=42)
    }

def get_classifiers():
    return {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'DecisionTreeClassifier': DecisionTreeClassifier(random_state=42),
        'RandomForestClassifier': RandomForestClassifier(n_estimators=50, n_jobs=-1, random_state=42),
        'ExtraTreesClassifier': ExtraTreesClassifier(n_estimators=50, n_jobs=-1, random_state=42),
        'GradientBoostingClassifier': GradientBoostingClassifier(n_estimators=50, random_state=42),
        'SVC': SVC(probability=True, random_state=42)
    }

def get_feature_importances(model, X_train_cols, cat_encoder):
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0]) if len(model.coef_.shape) > 1 else np.abs(model.coef_)
        else:
            return None
            
        feature_names = []
        # Try to get feature names out of ColumnTransformer
        try:
            transformers = model.named_steps['preprocessor'].transformers_
            for name, trans, cols in transformers:
                if name == 'num':
                    feature_names.extend(cols)
                elif name == 'cat':
                    cat_features = trans.named_steps['onehot'].get_feature_names_out(cols)
                    feature_names.extend(cat_features)
            if len(feature_names) == len(importances):
                return pd.DataFrame({'feature': feature_names, 'importance': importances}).sort_values('importance', ascending=False)
        except Exception:
            pass
            
    except Exception as e:
        print(f"Could not get feature importances: {e}")
    return None

def train_and_evaluate(df, target, problem_type, domain, num_cols, cat_cols, remove_cols, removal_reasons):
    print(f"\n{'='*50}\nTraining {domain} model\n{'='*50}")
    
    # Drop columns
    df_clean = df.drop(columns=remove_cols, errors='ignore')
    
    X = df_clean.drop(columns=[target])
    y = df_clean[target]
    
    if problem_type == 'regression':
        models = get_regressors()
        scoring = {'rmse': 'neg_root_mean_squared_error', 'mae': 'neg_mean_absolute_error', 'r2': 'r2'}
        primary_metric = 'rmse'
        cv_splitter = KFold(n_splits=3, shuffle=True, random_state=42)
        cv_splitter_5 = KFold(n_splits=5, shuffle=True, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
    else:
        models = get_classifiers()
        scoring = {'accuracy': 'accuracy', 'precision': 'precision_macro', 'recall': 'recall_macro', 'f1': 'f1_macro'}
        primary_metric = 'f1'
        cv_splitter = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        cv_splitter_5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(X_train, y_train, test_size=0.2, stratify=y_train, random_state=42)

    # 1. Fast candidate screening with 3-fold CV
    print("Step A: Fast candidate screening with 3-fold CV")
    results = []
    
    for name, model in models.items():
        start_time = time.time()
        pipeline = Pipeline(steps=[
            ('preprocessor', get_preprocessor(num_cols, cat_cols)),
            ('model', model)
        ])
        try:
            cv_res = cross_validate(pipeline, X_train, y_train, cv=cv_splitter, scoring=scoring, n_jobs=-1 if name != 'SVC' else 1)
            elapsed = time.time() - start_time
            
            res_dict = {'Model': name, 'Training Time': elapsed}
            if problem_type == 'regression':
                res_dict['3-Fold CV RMSE'] = -cv_res['test_rmse'].mean()
                res_dict['3-Fold CV MAE'] = -cv_res['test_mae'].mean()
                res_dict['3-Fold CV R2'] = cv_res['test_r2'].mean()
                metric_val = res_dict['3-Fold CV RMSE']
            else:
                res_dict['CV Accuracy'] = cv_res['test_accuracy'].mean()
                res_dict['CV Precision'] = cv_res['test_precision'].mean()
                res_dict['CV Recall'] = cv_res['test_recall'].mean()
                res_dict['CV F1'] = cv_res['test_f1'].mean()
                metric_val = res_dict['CV F1']
                
            results.append(res_dict)
            print(f"[{name}] 3-fold CV {primary_metric.upper()}: {metric_val:.4f} | Time: {elapsed:.1f}s")
        except Exception as e:
            print(f"[{name}] Failed during 3-fold CV: {e}")
            
    res_df = pd.DataFrame(results)
    
    # Select TOP 3
    print("\nStep B: Select TOP 3 candidates")
    if problem_type == 'regression':
        top_3 = res_df.nsmallest(3, '3-Fold CV RMSE')['Model'].tolist()
    else:
        top_3 = res_df.nlargest(3, 'CV F1')['Model'].tolist()
    print(f"Top 3 candidates: {top_3}")
    
    # 3. 5-fold CV ONLY on TOP 3
    print("\nStep C & D: Run 5-fold CV on TOP 3 and validation")
    top_results = []
    
    best_model_name = None
    best_pipeline = None
    best_val_score = float('inf') if problem_type == 'regression' else -float('inf')
    
    for name in top_3:
        start_time = time.time()
        pipeline = Pipeline(steps=[
            ('preprocessor', get_preprocessor(num_cols, cat_cols)),
            ('model', models[name])
        ])
        
        cv_res_5 = cross_validate(pipeline, X_train, y_train, cv=cv_splitter_5, scoring=scoring, n_jobs=-1 if name != 'SVC' else 1)
        
        # Train on split for validation
        pipeline.fit(X_train_split, y_train_split)
        y_val_pred = pipeline.predict(X_val_split)
        
        elapsed = time.time() - start_time
        
        # update res_df with 5-fold and validation
        idx = res_df.index[res_df['Model'] == name].tolist()[0]
        
        if problem_type == 'regression':
            val_rmse = np.sqrt(mean_squared_error(y_val_split, y_val_pred))
            val_mae = mean_absolute_error(y_val_split, y_val_pred)
            val_r2 = r2_score(y_val_split, y_val_pred)
            
            res_df.at[idx, '5-Fold CV RMSE'] = -cv_res_5['test_rmse'].mean()
            res_df.at[idx, '5-Fold CV MAE'] = -cv_res_5['test_mae'].mean()
            res_df.at[idx, '5-Fold CV R2'] = cv_res_5['test_r2'].mean()
            res_df.at[idx, 'Validation RMSE'] = val_rmse
            res_df.at[idx, 'Validation MAE'] = val_mae
            res_df.at[idx, 'Validation R2'] = val_r2
            
            print(f"[{name}] 5-fold RMSE: {res_df.at[idx, '5-Fold CV RMSE']:.4f} | Val RMSE: {val_rmse:.4f}")
            
            if val_rmse < best_val_score:
                best_val_score = val_rmse
                best_model_name = name
                best_pipeline = pipeline
                
        else:
            val_acc = accuracy_score(y_val_split, y_val_pred)
            val_prec = precision_score(y_val_split, y_val_pred, average='macro', zero_division=0)
            val_rec = recall_score(y_val_split, y_val_pred, average='macro', zero_division=0)
            val_f1 = f1_score(y_val_split, y_val_pred, average='macro', zero_division=0)
            
            res_df.at[idx, '5-Fold CV Accuracy'] = cv_res_5['test_accuracy'].mean()
            res_df.at[idx, '5-Fold CV Precision'] = cv_res_5['test_precision'].mean()
            res_df.at[idx, '5-Fold CV Recall'] = cv_res_5['test_recall'].mean()
            res_df.at[idx, '5-Fold CV F1'] = cv_res_5['test_f1'].mean()
            res_df.at[idx, 'Validation Accuracy'] = val_acc
            res_df.at[idx, 'Validation Precision'] = val_prec
            res_df.at[idx, 'Validation Recall'] = val_rec
            res_df.at[idx, 'Validation F1'] = val_f1
            
            print(f"[{name}] 5-fold F1: {res_df.at[idx, '5-Fold CV F1']:.4f} | Val F1: {val_f1:.4f}")
            
            if val_f1 > best_val_score:
                best_val_score = val_f1
                best_model_name = name
                best_pipeline = pipeline
                
    print(f"\nStep E: Select best model -> BEST MODEL: {best_model_name}")
    
    print("\nStep F: Retrain best model on train + validation")
    best_pipeline.fit(X_train, y_train)
    
    print("\nStep G: Evaluate once on untouched test")
    y_test_pred = best_pipeline.predict(X_test)
    
    test_metrics = {}
    if problem_type == 'regression':
        test_metrics['test_rmse'] = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_metrics['test_mae'] = mean_absolute_error(y_test, y_test_pred)
        test_metrics['test_r2'] = r2_score(y_test, y_test_pred)
        print(f"Final Test RMSE: {test_metrics['test_rmse']:.4f}")
        primary_val = test_metrics['test_rmse']
    else:
        test_metrics['test_accuracy'] = accuracy_score(y_test, y_test_pred)
        test_metrics['test_precision'] = precision_score(y_test, y_test_pred, average='macro', zero_division=0)
        test_metrics['test_recall'] = recall_score(y_test, y_test_pred, average='macro', zero_division=0)
        test_metrics['test_f1'] = f1_score(y_test, y_test_pred, average='macro', zero_division=0)
        print(f"Final Test F1: {test_metrics['test_f1']:.4f}")
        primary_val = test_metrics['test_f1']
        
    # Save model and metadata
    model_path = os.path.join(MODELS_DIR, domain, 'model.joblib')
    joblib.dump(best_pipeline, model_path)
    
    # Metadata
    metadata = {
        "model_name": best_model_name,
        "problem_type": problem_type,
        "target": target,
        "dataset": f"{domain}_clean.csv" if domain != 'forecasting' else "transaction_forecasting_clean.csv",
        "version": "1.0",
        "training_date": datetime.datetime.now().isoformat(),
        "rows": len(df),
        "final_features": X_train.columns.tolist(),
        "metrics": {
            "cv_primary": res_df.loc[res_df['Model'] == best_model_name, f"5-Fold CV {'RMSE' if problem_type == 'regression' else 'F1'}"].values[0],
            "validation_primary": best_val_score,
            "test_primary": primary_val,
            "test_secondary": test_metrics['test_mae'] if problem_type == 'regression' else test_metrics['test_accuracy']
        }
    }
    with open(os.path.join(MODELS_DIR, domain, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    # Feature info
    feature_info = {
        "final_features": X_train.columns.tolist(),
        "numerical_features": num_cols,
        "categorical_features": cat_cols,
        "removed_features": remove_cols,
        "removal_reasons": removal_reasons,
        "preprocessing": "SimpleImputer + StandardScaler for num, SimpleImputer + OneHotEncoder for cat"
    }
    with open(os.path.join(MODELS_DIR, domain, 'feature_info.json'), 'w') as f:
        json.dump(feature_info, f, indent=4)
        
    # Reports
    res_df.to_csv(os.path.join(REPORTS_DIR, f"{domain}_model_comparison.csv"), index=False)
    
    # Feature Importance
    importance_df = get_feature_importances(best_pipeline.named_steps['model'], X_train.columns, best_pipeline.named_steps['preprocessor'])
    if importance_df is not None:
        importance_df.to_csv(os.path.join(REPORTS_DIR, f"{domain}_feature_importance.csv"), index=False)
        
    # Training Report
    report_content = f"""# {domain.capitalize()} Model Training Report

- **Dataset**: {metadata['dataset']}
- **Target**: {target}
- **Problem Type**: {problem_type}
- **Split Strategy**: 80/20 train/test split. Stratified if classification.
- **Leakage Checks**: Removed identified leaky/id columns.
- **Candidate Models**: {', '.join(models.keys())}
- **Best Model**: {best_model_name}
- **Final Test Score ({primary_metric.upper()})**: {primary_val:.4f}
- **Saved Model Path**: {model_path}
"""
    with open(os.path.join(REPORTS_DIR, f"{domain}_training_report.md"), 'w') as f:
        f.write(report_content)
        
    # Update registry
    registry_path = os.path.join(MODELS_DIR, 'model_registry.json')
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry = json.load(f)
    else:
        registry = {}
        
    registry[domain] = {
        "model_path": model_path,
        "model_name": best_model_name,
        "target": target,
        "problem_type": problem_type,
        "version": "1.0",
        "primary_metric": primary_metric.upper(),
        "primary_metric_value": float(primary_val)
    }
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=4)
        
    return {
        'Domain': domain.capitalize(),
        'Dataset': metadata['dataset'],
        'Target': target,
        'Problem Type': problem_type,
        'Best Model': best_model_name,
        'CV Metric': f"{primary_metric.upper()}={metadata['metrics']['cv_primary']:.4f}",
        'Validation Metric': f"{primary_metric.upper()}={best_val_score:.4f}",
        'Test Metric': f"{primary_metric.upper()}={primary_val:.4f}",
        'Saved Model': model_path
    }

def train_forecasting(df, target, domain, num_cols, cat_cols, remove_cols, removal_reasons):
    print(f"\n{'='*50}\nTraining {domain} model (Time-Aware)\n{'='*50}")
    
    df_clean = df.drop(columns=remove_cols, errors='ignore')
    
    # Chronological sort
    if 'month_date' in df_clean.columns:
        df_clean = df_clean.sort_values('month_date')
    elif 'month' in df_clean.columns:
        df_clean = df_clean.sort_values('month')
        
    X = df_clean.drop(columns=[target])
    y = df_clean[target]
    
    # Train / Val / Test (80 / 10 / 10)
    n = len(df_clean)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    X_train_full = X.iloc[:val_end]
    y_train_full = y.iloc[:val_end]
    
    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]
    X_val = X.iloc[train_end:val_end]
    y_val = y.iloc[train_end:val_end]
    
    X_test = X.iloc[val_end:]
    y_test = y.iloc[val_end:]
    
    models = get_regressors()
    scoring = {'rmse': 'neg_root_mean_squared_error', 'mae': 'neg_mean_absolute_error', 'r2': 'r2'}
    cv_splitter = TimeSeriesSplit(n_splits=3)
    cv_splitter_5 = TimeSeriesSplit(n_splits=5)
    
    print("Step A: Fast candidate screening with 3-fold TimeSeries CV")
    results = []
    
    for name, model in models.items():
        start_time = time.time()
        pipeline = Pipeline(steps=[
            ('preprocessor', get_preprocessor(num_cols, cat_cols)),
            ('model', model)
        ])
        try:
            cv_res = cross_validate(pipeline, X_train_full, y_train_full, cv=cv_splitter, scoring=scoring, n_jobs=-1)
            elapsed = time.time() - start_time
            
            res_dict = {
                'Model': name, 
                'Training Time': elapsed,
                '3-Fold CV RMSE': -cv_res['test_rmse'].mean(),
                '3-Fold CV MAE': -cv_res['test_mae'].mean(),
                '3-Fold CV R2': cv_res['test_r2'].mean()
            }
            results.append(res_dict)
            print(f"[{name}] 3-fold CV RMSE: {res_dict['3-Fold CV RMSE']:.4f} | Time: {elapsed:.1f}s")
        except Exception as e:
            print(f"[{name}] Failed during CV: {e}")
            
    res_df = pd.DataFrame(results)
    
    print("\nStep B: Select TOP 3 candidates")
    top_3 = res_df.nsmallest(3, '3-Fold CV RMSE')['Model'].tolist()
    print(f"Top 3 candidates: {top_3}")
    
    print("\nStep C & D: Run 5-fold CV on TOP 3 and validation")
    best_model_name = None
    best_pipeline = None
    best_val_score = float('inf')
    
    for name in top_3:
        start_time = time.time()
        pipeline = Pipeline(steps=[
            ('preprocessor', get_preprocessor(num_cols, cat_cols)),
            ('model', models[name])
        ])
        
        cv_res_5 = cross_validate(pipeline, X_train_full, y_train_full, cv=cv_splitter_5, scoring=scoring, n_jobs=-1)
        
        # Validation
        pipeline.fit(X_train, y_train)
        y_val_pred = pipeline.predict(X_val)
        
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_r2 = r2_score(y_val, y_val_pred)
        
        idx = res_df.index[res_df['Model'] == name].tolist()[0]
        res_df.at[idx, '5-Fold CV RMSE'] = -cv_res_5['test_rmse'].mean()
        res_df.at[idx, '5-Fold CV MAE'] = -cv_res_5['test_mae'].mean()
        res_df.at[idx, '5-Fold CV R2'] = cv_res_5['test_r2'].mean()
        res_df.at[idx, 'Validation RMSE'] = val_rmse
        res_df.at[idx, 'Validation MAE'] = val_mae
        res_df.at[idx, 'Validation R2'] = val_r2
        
        print(f"[{name}] 5-fold RMSE: {res_df.at[idx, '5-Fold CV RMSE']:.4f} | Val RMSE: {val_rmse:.4f}")
        
        if val_rmse < best_val_score:
            best_val_score = val_rmse
            best_model_name = name
            best_pipeline = pipeline
            
    print(f"\nStep E: Select best model -> BEST MODEL: {best_model_name}")
    
    print("\nStep F: Retrain best model on train + validation")
    best_pipeline.fit(X_train_full, y_train_full)
    
    print("\nStep G: Evaluate once on untouched test")
    y_test_pred = best_pipeline.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    print(f"Final Test RMSE: {test_rmse:.4f}")
    
    model_path = os.path.join(MODELS_DIR, domain, 'model.joblib')
    joblib.dump(best_pipeline, model_path)
    
    metadata = {
        "model_name": best_model_name,
        "problem_type": "regression",
        "target": target,
        "dataset": "transaction_forecasting_clean.csv",
        "version": "1.0",
        "training_date": datetime.datetime.now().isoformat(),
        "rows": len(df),
        "final_features": X_train.columns.tolist(),
        "metrics": {
            "cv_primary": res_df.loc[res_df['Model'] == best_model_name, "5-Fold CV RMSE"].values[0],
            "validation_primary": best_val_score,
            "test_primary": test_rmse,
            "test_secondary": test_mae
        }
    }
    with open(os.path.join(MODELS_DIR, domain, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    feature_info = {
        "final_features": X_train.columns.tolist(),
        "numerical_features": num_cols,
        "categorical_features": cat_cols,
        "removed_features": remove_cols,
        "removal_reasons": removal_reasons,
        "preprocessing": "SimpleImputer + StandardScaler for num, SimpleImputer + OneHotEncoder for cat"
    }
    with open(os.path.join(MODELS_DIR, domain, 'feature_info.json'), 'w') as f:
        json.dump(feature_info, f, indent=4)
        
    res_df.to_csv(os.path.join(REPORTS_DIR, f"{domain}_model_comparison.csv"), index=False)
    
    importance_df = get_feature_importances(best_pipeline.named_steps['model'], X_train.columns, best_pipeline.named_steps['preprocessor'])
    if importance_df is not None:
        importance_df.to_csv(os.path.join(REPORTS_DIR, f"{domain}_feature_importance.csv"), index=False)
        
    report_content = f"""# {domain.capitalize()} Model Training Report

- **Dataset**: {metadata['dataset']}
- **Target**: {target}
- **Problem Type**: regression
- **Split Strategy**: Chronological split (80% train, 10% validation, 10% test).
- **Leakage Checks**: Removed next month counts and leaky IDs.
- **Candidate Models**: {', '.join(models.keys())}
- **Best Model**: {best_model_name}
- **Final Test Score (RMSE)**: {test_rmse:.4f}
- **Saved Model Path**: {model_path}
"""
    with open(os.path.join(REPORTS_DIR, f"{domain}_training_report.md"), 'w') as f:
        f.write(report_content)
        
    registry_path = os.path.join(MODELS_DIR, 'model_registry.json')
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry = json.load(f)
    else:
        registry = {}
        
    registry[domain] = {
        "model_path": model_path,
        "model_name": best_model_name,
        "target": target,
        "problem_type": "regression",
        "version": "1.0",
        "primary_metric": "RMSE",
        "primary_metric_value": float(test_rmse)
    }
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=4)
        
    return {
        'Domain': domain.capitalize(),
        'Dataset': metadata['dataset'],
        'Target': target,
        'Problem Type': 'regression',
        'Best Model': best_model_name,
        'CV Metric': f"RMSE={metadata['metrics']['cv_primary']:.4f}",
        'Validation Metric': f"RMSE={best_val_score:.4f}",
        'Test Metric': f"RMSE={test_rmse:.4f}",
        'Saved Model': model_path
    }

def main():
    final_summaries = []
    
    # ==========================
    # 1. FITNESS
    # ==========================
    # Target: calories_burned (Regression) for digital twin energy expenditure tracking
    df_fit = pd.read_csv(os.path.join(DATA_DIR, 'fitness_clean.csv'))
    fit_target = 'calories_burned'
    fit_remove = ['id', 'fitness_user_id', 'full_name']
    fit_reasons = {'id': 'Identifier', 'fitness_user_id': 'Identifier', 'full_name': 'Identifier'}
    fit_num = ['age', 'height_cm', 'weight_kg', 'steps', 'sleep_hours', 'water_intake_liters', 'active_minutes', 'heart_rate', 'stress_level', 'bmi', 'steps_per_active_minute']
    fit_cat = ['gender', 'workout_type', 'mood', 'day_of_week', 'month', 'activity_level']
    
    s1 = train_and_evaluate(df_fit, fit_target, 'regression', 'fitness', fit_num, fit_cat, fit_remove, fit_reasons)
    final_summaries.append(s1)
    
    # ==========================
    # 2. LIFESTYLE
    # ==========================
    # Target: sleep_disorder (Classification)
    df_life = pd.read_csv(os.path.join(DATA_DIR, 'lifestyle_clean.csv'))
    life_target = 'sleep_disorder'
    life_remove = ['id', 'client_id']
    life_reasons = {'id': 'Identifier', 'client_id': 'Identifier'}
    life_num = ['age', 'sleep_hours', 'sleep_quality', 'physical_activity_level', 'stress_level', 'heart_rate', 'daily_steps', 'activity_sleep_balance', 'lifestyle_risk_score']
    life_cat = ['gender', 'occupation', 'bmi_category', 'blood_pressure']
    
    s2 = train_and_evaluate(df_life, life_target, 'classification', 'lifestyle', life_num, life_cat, life_remove, life_reasons)
    final_summaries.append(s2)
    
    # ==========================
    # 3. FINANCIAL
    # ==========================
    # Target: disposable_income (Regression)
    # Remove derived expenses and savings that create leakage
    df_fin = pd.read_csv(os.path.join(DATA_DIR, 'financial_profile_clean.csv'))
    fin_target = 'disposable_income'
    fin_remove = [
        'id', 'client_id', 'total_expenses', 'calculated_savings', 'expense_ratio', 'saving_rate', 'financial_stability_score',
        'potential_savings_groceries', 'potential_savings_transport', 'potential_savings_eating_out', 
        'potential_savings_entertainment', 'potential_savings_utilities', 'potential_savings_healthcare', 
        'potential_savings_education', 'potential_savings_miscellaneous',
        'groceries', 'transport', 'eating_out', 'entertainment', 'utilities', 'healthcare', 'education', 'miscellaneous', 'rent', 'loan_repayment', 'insurance'
    ]
    fin_reasons = {'id': 'Identifier', 'client_id': 'Identifier', 'total_expenses': 'Target leakage (derived)', 'calculated_savings': 'Target leakage'}
    fin_num = ['income', 'age', 'dependents', 'desired_savings_percentage', 'desired_savings']
    fin_cat = ['occupation', 'city_tier']
    
    s3 = train_and_evaluate(df_fin, fin_target, 'regression', 'financial', fin_num, fin_cat, fin_remove, fin_reasons)
    final_summaries.append(s3)
    
    # ==========================
    # 4. FORECASTING
    # ==========================
    # Target: next_month_spending
    df_fore = pd.read_csv(os.path.join(DATA_DIR, 'transaction_forecasting_clean.csv'))
    fore_target = 'next_month_spending'
    fore_remove = ['client_id', 'next_month_transaction_count', 'month_date']
    fore_reasons = {'client_id': 'Identifier', 'next_month_transaction_count': 'Future leakage', 'month_date': 'Used for sorting only'}
    fore_num = ['total_signed_amount', 'total_absolute_amount', 'positive_amount', 'negative_amount', 
                'transaction_count', 'positive_transaction_count', 'negative_transaction_count', 
                'average_transaction_amount', 'unique_merchants', 'unique_cards', 'error_count', 
                'total_absolute_amount_lag_1', 'total_absolute_amount_rolling_3m', 'positive_amount_lag_1', 
                'positive_amount_rolling_3m', 'negative_amount_lag_1', 'negative_amount_rolling_3m', 
                'transaction_count_lag_1', 'transaction_count_rolling_3m']
    fore_cat = ['month'] # Can use month as categorical or drop it. We'll include it.
    
    s4 = train_forecasting(df_fore, fore_target, 'forecasting', fore_num, fore_cat, fore_remove, fore_reasons)
    final_summaries.append(s4)
    
    print("\n" + "="*50)
    print("FINAL SUMMARY")
    print("="*50)
    summ_df = pd.DataFrame(final_summaries)
    print(summ_df.to_markdown(index=False))

if __name__ == "__main__":
    main()
