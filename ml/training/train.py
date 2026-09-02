from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGB_OK = True
except ImportError:
    XGBClassifier = XGBRegressor = None
    XGB_OK = False


# ============================================================
# PATHS
# ============================================================

from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai"
)

DATA_PATH = Path(
    r"C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\Datasets\prepared_datasets\fitness_clean.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "ml_models"
    / "fitness"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "fitness"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PREPROCESSING
# ============================================================

def one_hot():
    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=True,
        )


def make_pipeline(model, numeric_cols, categorical_cols):
    transformers = []

    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            )
        )

    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(strategy="most_frequent"),
                        ),
                        ("onehot", one_hot()),
                    ]
                ),
                categorical_cols,
            )
        )

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


# ============================================================
# MODELS
# ============================================================

def regression_models():
    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=100,
            n_jobs=-1,
            random_state=42,
        ),
        "ExtraTreesRegressor": ExtraTreesRegressor(
            n_estimators=100,
            n_jobs=-1,
            random_state=42,
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }

    if XGB_OK:
        models["XGBRegressor"] = XGBRegressor(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1,
        )

    return models


def classification_models():
    models = {
        "LogisticRegression": LogisticRegression(
            max_iter=2000,
            random_state=42,
        ),
        "DecisionTreeClassifier": DecisionTreeClassifier(
            random_state=42,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=100,
            n_jobs=-1,
            random_state=42,
        ),
        "ExtraTreesClassifier": ExtraTreesClassifier(
            n_estimators=100,
            n_jobs=-1,
            random_state=42,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }

    if XGB_OK:
        models["XGBClassifier"] = XGBClassifier(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )

    return models


# ============================================================
# TARGET / LEAKAGE DIAGNOSTICS
# ============================================================

def inspect_activity_target(df):
    print("\nACTIVITY_LEVEL CHECK")

    if "activity_level" not in df.columns:
        print("activity_level not found.")
        return False

    counts = df["activity_level"].value_counts(dropna=False)
    print("\nClass distribution:")
    print(counts)

    if "steps" not in df.columns:
        print("steps not found; cannot perform step-range check.")
        return False

    ranges = (
        df.dropna(subset=["activity_level", "steps"])
        .groupby("activity_level")["steps"]
        .agg(["min", "max", "count"])
        .sort_values("min")
    )

    print("\nSteps by activity_level:")
    print(ranges)

    intervals = list(
        ranges[["min", "max"]].itertuples(index=False, name=None)
    )

    non_overlapping = True
    for i in range(len(intervals) - 1):
        if intervals[i][1] >= intervals[i + 1][0]:
            non_overlapping = False
            break

    if non_overlapping and len(intervals) > 1:
        print(
            "\nWARNING: step ranges are non-overlapping. "
            "activity_level is likely derived from steps."
        )
        return True

    print(
        "\nNo direct deterministic step-range pattern detected."
    )
    return False


# ============================================================
# REGRESSION
# ============================================================

def run_regression(df):
    target = "calories_burned"

    if target not in df.columns:
        return None

    data = df.dropna(subset=[target]).copy()

    remove = [
        c for c in [
            "id",
            "fitness_user_id",
            "full_name",
            "activity_level",
        ]
        if c in data.columns
    ]

    X = data.drop(columns=[target] + remove)
    y = data[target]

    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = X.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.20, random_state=42
    )

    models = regression_models()

    cv3 = KFold(n_splits=3, shuffle=True, random_state=42)

    scoring = {
        "rmse": "neg_root_mean_squared_error",
        "mae": "neg_mean_absolute_error",
        "r2": "r2",
    }

    results = []

    print("\nTASK A: calories_burned regression")
    print("=" * 60)

    for i, (name, model) in enumerate(models.items(), 1):
        print(f"[{i}/{len(models)}] {name}...", flush=True)

        pipe = make_pipeline(model, num_cols, cat_cols)
        start = time.time()

        try:
            cv = cross_validate(
                pipe,
                X_train,
                y_train,
                cv=cv3,
                scoring=scoring,
                n_jobs=-1,
                return_train_score=False,
            )

            pipe.fit(X_tr, y_tr)
            val_pred = pipe.predict(X_val)

            row = {
                "Model": name,
                "3Fold_RMSE": -cv["test_rmse"].mean(),
                "3Fold_MAE": -cv["test_mae"].mean(),
                "3Fold_R2": cv["test_r2"].mean(),
                "Validation_RMSE": np.sqrt(
                    mean_squared_error(y_val, val_pred)
                ),
                "Validation_MAE": mean_absolute_error(
                    y_val, val_pred
                ),
                "Validation_R2": r2_score(
                    y_val, val_pred
                ),
                "Time_Seconds": time.time() - start,
            }

            results.append(row)

            print(
                f"    CV RMSE={row['3Fold_RMSE']:.4f} | "
                f"Val RMSE={row['Validation_RMSE']:.4f} | "
                f"Time={row['Time_Seconds']:.1f}s",
                flush=True,
            )

        except Exception as exc:
            print(f"    FAILED: {exc}", flush=True)

    if not results:
        return None

    result_df = pd.DataFrame(results)
    top3 = (
        result_df
        .nsmallest(3, "3Fold_RMSE")["Model"]
        .tolist()
    )

    print(f"\nTop 3: {top3}")

    cv5 = KFold(n_splits=5, shuffle=True, random_state=42)

    best_name = None
    best_val = np.inf
    best_cv = None

    for name in top3:
        print(f"Finalist: {name}", flush=True)

        pipe = make_pipeline(
            models[name],
            num_cols,
            cat_cols,
        )

        cv = cross_validate(
            pipe,
            X_train,
            y_train,
            cv=cv5,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        pipe.fit(X_tr, y_tr)
        val_pred = pipe.predict(X_val)

        cv_rmse = -cv["test_rmse"].mean()
        val_rmse = np.sqrt(
            mean_squared_error(y_val, val_pred)
        )

        idx = result_df.index[
            result_df["Model"] == name
        ].tolist()[0]

        result_df.at[idx, "5Fold_RMSE"] = cv_rmse
        result_df.at[idx, "5Fold_MAE"] = -cv[
            "test_mae"
        ].mean()
        result_df.at[idx, "5Fold_R2"] = cv[
            "test_r2"
        ].mean()
        result_df.at[idx, "Validation_RMSE"] = val_rmse

        print(
            f"    5-fold RMSE={cv_rmse:.4f} | "
            f"Val RMSE={val_rmse:.4f}",
            flush=True,
        )

        if val_rmse < best_val:
            best_val = val_rmse
            best_name = name
            best_cv = cv_rmse

    # Final train on train + validation.
    final_pipe = make_pipeline(
        models[best_name],
        num_cols,
        cat_cols,
    )

    X_train_val = pd.concat([X_tr, X_val])
    y_train_val = pd.concat([y_tr, y_val])

    final_pipe.fit(
        X_train_val,
        y_train_val,
    )

    test_pred = final_pipe.predict(X_test)

    test_rmse = np.sqrt(
        mean_squared_error(y_test, test_pred)
    )
    test_mae = mean_absolute_error(
        y_test, test_pred
    )
    test_r2 = r2_score(
        y_test, test_pred
    )

    baseline_pred = np.full(
        len(y_test),
        y_train.mean(),
    )
    baseline_rmse = np.sqrt(
        mean_squared_error(
            y_test,
            baseline_pred,
        )
    )

    print("\nRegression final:")
    print(f"Best model: {best_name}")
    print(f"Test RMSE: {test_rmse:.4f}")
    print(f"Test MAE:  {test_mae:.4f}")
    print(f"Test R2:   {test_r2:.4f}")
    print(f"Baseline:  {baseline_rmse:.4f}")

    return {
        "task": "calories_burned_regression",
        "target": target,
        "problem_type": "regression",
        "best_model": best_name,
        "cv_primary": float(best_cv),
        "validation_primary": float(best_val),
        "test_primary": float(test_rmse),
        "test_rmse": float(test_rmse),
        "test_mae": float(test_mae),
        "test_r2": float(test_r2),
        "baseline_rmse": float(baseline_rmse),
        "beats_baseline": bool(test_rmse < baseline_rmse),
        "pipeline": final_pipe,
        "features": X.columns.tolist(),
        "numeric": num_cols,
        "categorical": cat_cols,
        "removed": remove,
        "comparison": result_df,
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def run_classification(df, step_derived):
    target = "activity_level"

    if target not in df.columns:
        return None

    data = df.dropna(subset=[target]).copy()

    remove = [
        c for c in [
            "id",
            "fitness_user_id",
            "full_name",
        ]
        if c in data.columns
    ]

    # If target appears to be generated from steps, remove the source
    # feature and its direct engineered derivative.
    if step_derived:
        for c in ["steps", "steps_per_active_minute"]:
            if c in data.columns:
                remove.append(c)

    X = data.drop(
        columns=[target] + remove,
        errors="ignore",
    )
    y = data[target]

    print(
        "\nTASK B: activity_level classification"
    )
    print("=" * 60)

    print("\nTarget distribution:")
    print(y.value_counts())

    num_cols = X.select_dtypes(
        include=np.number
    ).columns.tolist()

    cat_cols = X.select_dtypes(
        include=[
            "object",
            "category",
            "string",
            "bool",
        ]
    ).columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train,
        y_train,
        test_size=0.20,
        stratify=y_train,
        random_state=42,
    )

    models = classification_models()

    cv3 = StratifiedKFold(
        n_splits=3,
        shuffle=True,
        random_state=42,
    )

    scoring = {
        "accuracy": "accuracy",
        "precision": "precision_macro",
        "recall": "recall_macro",
        "f1": "f1_macro",
    }

    results = []

    for i, (name, model) in enumerate(
        models.items(),
        1,
    ):

        print(
            f"[{i}/{len(models)}] {name}...",
            flush=True,
        )

        pipe = make_pipeline(
            model,
            num_cols,
            cat_cols,
        )

        start = time.time()

        try:

            cv = cross_validate(
                pipe,
                X_train,
                y_train,
                cv=cv3,
                scoring=scoring,
                n_jobs=-1,
                return_train_score=False,
            )

            pipe.fit(
                X_tr,
                y_tr,
            )

            val_pred = pipe.predict(
                X_val
            )

            row = {
                "Model": name,
                "3Fold_F1": cv[
                    "test_f1"
                ].mean(),
                "3Fold_Accuracy": cv[
                    "test_accuracy"
                ].mean(),
                "3Fold_Precision": cv[
                    "test_precision"
                ].mean(),
                "3Fold_Recall": cv[
                    "test_recall"
                ].mean(),
                "Validation_F1": f1_score(
                    y_val,
                    val_pred,
                    average="macro",
                    zero_division=0,
                ),
                "Time_Seconds":
                    time.time() - start,
            }

            results.append(row)

            print(
                f"    CV F1={row['3Fold_F1']:.4f} | "
                f"Val F1={row['Validation_F1']:.4f} | "
                f"Time={row['Time_Seconds']:.1f}s",
                flush=True,
            )

        except Exception as exc:
            print(
                f"    FAILED: {exc}",
                flush=True,
            )

    if not results:
        return None

    result_df = pd.DataFrame(results)

    top3 = (
        result_df
        .nlargest(
            3,
            "3Fold_F1",
        )["Model"]
        .tolist()
    )

    print(
        f"\nTop 3: {top3}"
    )

    cv5 = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    best_name = None
    best_val = -np.inf
    best_cv = None

    for name in top3:

        print(
            f"Finalist: {name}",
            flush=True,
        )

        pipe = make_pipeline(
            models[name],
            num_cols,
            cat_cols,
        )

        cv = cross_validate(
            pipe,
            X_train,
            y_train,
            cv=cv5,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        pipe.fit(
            X_tr,
            y_tr,
        )

        val_pred = pipe.predict(
            X_val
        )

        cv_f1 = cv[
            "test_f1"
        ].mean()

        val_f1 = f1_score(
            y_val,
            val_pred,
            average="macro",
            zero_division=0,
        )

        idx = result_df.index[
            result_df["Model"] == name
        ].tolist()[0]

        result_df.at[
            idx,
            "5Fold_F1"
        ] = cv_f1

        result_df.at[
            idx,
            "5Fold_Accuracy"
        ] = cv[
            "test_accuracy"
        ].mean()

        result_df.at[
            idx,
            "Validation_F1"
        ] = val_f1

        print(
            f"    5-fold F1={cv_f1:.4f} | "
            f"Val F1={val_f1:.4f}",
            flush=True,
        )

        if val_f1 > best_val:

            best_val = val_f1
            best_name = name
            best_cv = cv_f1

    # Final model.
    final_pipe = make_pipeline(
        models[best_name],
        num_cols,
        cat_cols,
    )

    X_train_val = pd.concat(
        [X_tr, X_val]
    )

    y_train_val = pd.concat(
        [y_tr, y_val]
    )

    final_pipe.fit(
        X_train_val,
        y_train_val,
    )

    test_pred = final_pipe.predict(
        X_test
    )

    test_f1 = f1_score(
        y_test,
        test_pred,
        average="macro",
        zero_division=0,
    )

    test_acc = accuracy_score(
        y_test,
        test_pred,
    )

    test_precision = precision_score(
        y_test,
        test_pred,
        average="macro",
        zero_division=0,
    )

    test_recall = recall_score(
        y_test,
        test_pred,
        average="macro",
        zero_division=0,
    )

    print("\nClassification final:")
    print(
        f"Best model: {best_name}"
    )
    print(
        f"Test Accuracy: {test_acc:.4f}"
    )
    print(
        f"Test Precision: {test_precision:.4f}"
    )
    print(
        f"Test Recall: {test_recall:.4f}"
    )
    print(
        f"Test F1: {test_f1:.4f}"
    )

    return {
        "task":
            "activity_level_classification",
        "target":
            target,
        "problem_type":
            "classification",
        "best_model":
            best_name,
        "cv_primary":
            float(best_cv),
        "validation_primary":
            float(best_val),
        "test_primary":
            float(test_f1),
        "test_f1":
            float(test_f1),
        "test_accuracy":
            float(test_acc),
        "test_precision":
            float(test_precision),
        "test_recall":
            float(test_recall),
        "pipeline":
            final_pipe,
        "features":
            X.columns.tolist(),
        "numeric":
            num_cols,
        "categorical":
            cat_cols,
        "removed":
            remove,
        "comparison":
            result_df,
    }


# ============================================================
# SAVE
# ============================================================

def save_model(result):
    model_path = (
        MODEL_DIR / "model.joblib"
    )

    metadata_path = (
        MODEL_DIR / "metadata.json"
    )

    feature_path = (
        MODEL_DIR / "feature_info.json"
    )

    joblib.dump(
        result["pipeline"],
        model_path,
    )

    metadata = {
        "model_name":
            result["best_model"],
        "problem_type":
            result["problem_type"],
        "target":
            result["target"],
        "dataset":
            "fitness_clean.csv",
        "task":
            result["task"],
        "version":
            "1.0",
        "training_date":
            datetime.now().isoformat(),
        "metrics":
            {
                "cv_primary":
                    result["cv_primary"],
                "validation_primary":
                    result["validation_primary"],
                "test_primary":
                    result["test_primary"],
            },
    }

    if result["problem_type"] == "regression":

        metadata["metrics"].update(
            {
                "test_mae":
                    result["test_mae"],
                "test_r2":
                    result["test_r2"],
                "baseline_rmse":
                    result["baseline_rmse"],
                "beats_baseline":
                    result["beats_baseline"],
            }
        )

    else:

        metadata["metrics"].update(
            {
                "test_accuracy":
                    result["test_accuracy"],
                "test_precision":
                    result["test_precision"],
                "test_recall":
                    result["test_recall"],
            }
        )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
        )

    feature_info = {
        "target":
            result["target"],
        "task":
            result["task"],
        "final_features":
            result["features"],
        "numerical_features":
            result["numeric"],
        "categorical_features":
            result["categorical"],
        "removed_features":
            result["removed"],
    }

    with open(
        feature_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            feature_info,
            f,
            indent=4,
        )

    result[
        "comparison"
    ].to_csv(
        REPORT_DIR
        / "fitness_model_comparison.csv",
        index=False,
    )

    with open(
        REPORT_DIR
        / "fitness_training_report.md",
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "# Fitness Model Training Report\n\n"
            f"- Task: {result['task']}\n"
            f"- Target: {result['target']}\n"
            f"- Problem type: {result['problem_type']}\n"
            f"- Best model: {result['best_model']}\n"
            f"- CV primary: {result['cv_primary']:.4f}\n"
            f"- Validation primary: {result['validation_primary']:.4f}\n"
            f"- Test primary: {result['test_primary']:.4f}\n"
            f"- Model path: {model_path}\n"
        )

    # Preserve other domain entries.
    registry_path = (
        PROJECT_ROOT
        / "backend"
        / "app"
        / "ml_models"
        / "model_registry.json"
    )

    if registry_path.exists():

        try:

            with open(
                registry_path,
                "r",
                encoding="utf-8",
            ) as f:

                registry = json.load(f)

        except Exception:

            registry = {}

    else:

        registry = {}

    metric_name = (
        "RMSE"
        if result["problem_type"] == "regression"
        else "F1"
    )

    registry["fitness"] = {
        "model_path":
            str(model_path),
        "model_name":
            result["best_model"],
        "target":
            result["target"],
        "problem_type":
            result["problem_type"],
        "version":
            "1.0",
        "primary_metric":
            metric_name,
        "primary_metric_value":
            result["test_primary"],
    }

    with open(
        registry_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            registry,
            f,
            indent=4,
        )

    print(
        f"\nSaved model: {model_path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    total_start = time.time()

    print("=" * 70)
    print(
        "FITNESS MODEL — TARGET DIAGNOSIS + TRAINING"
    )
    print("=" * 70)

    print(
        f"\nProject root: {PROJECT_ROOT}"
    )

    print(
        f"Dataset: {DATA_PATH}"
    )

    if not DATA_PATH.exists():

        raise FileNotFoundError(
            f"Fitness dataset not found:\n{DATA_PATH}"
        )

    print(
        "\nLoading dataset..."
    )

    df = pd.read_csv(
        DATA_PATH,
        low_memory=False,
    )

    print(
        f"Shape: {df.shape}"
    )

    print(
        f"Missing cells: "
        f"{int(df.isna().sum().sum())}"
    )

    print(
        f"Duplicate rows: "
        f"{int(df.duplicated().sum())}"
    )

    # Diagnostics.
    step_derived = inspect_activity_target(
        df
    )

    # Run both tasks.
    regression = run_regression(
        df
    )

    classification = run_classification(
        df,
        step_derived,
    )

    print(
        "\n" + "=" * 70
    )
    print(
        "FITNESS TASK COMPARISON"
    )
    print(
        "=" * 70
    )

    if regression:

        print(
            "\nRegression:"
        )

        print(
            f"  Best model: "
            f"{regression['best_model']}"
        )

        print(
            f"  Test RMSE: "
            f"{regression['test_rmse']:.4f}"
        )

        print(
            f"  Test R2: "
            f"{regression['test_r2']:.4f}"
        )

        print(
            f"  Beats mean baseline: "
            f"{regression['beats_baseline']}"
        )

    if classification:

        print(
            "\nClassification:"
        )

        print(
            f"  Best model: "
            f"{classification['best_model']}"
        )

        print(
            f"  Test F1: "
            f"{classification['test_f1']:.4f}"
        )

        print(
            f"  Test Accuracy: "
            f"{classification['test_accuracy']:.4f}"
        )

    # Select a defensible task.
    candidates = []

    if regression and regression[
        "beats_baseline"
    ]:

        candidates.append(
            regression
        )

    if classification and classification[
        "test_f1"
    ] > 0:

        candidates.append(
            classification
        )

    if not candidates:

        print(
            "\nNo defensible Fitness model found."
        )

        print(
            "No production Fitness model was saved."
        )

        return

    # Prefer strong classification when regression is weak.
    cls = next(
        (
            x
            for x in candidates
            if x["problem_type"]
            == "classification"
        ),
        None,
    )

    reg = next(
        (
            x
            for x in candidates
            if x["problem_type"]
            == "regression"
        ),
        None,
    )

    if (
        cls
        and cls["test_f1"] >= 0.80
        and (
            reg is None
            or reg["test_r2"] < 0.20
        )
    ):

        selected = cls

    elif reg:

        selected = reg

    else:

        selected = cls

    print(
        "\n" + "=" * 70
    )

    print(
        "FINAL FITNESS MODEL"
    )

    print(
        "=" * 70
    )

    print(
        f"Selected task: "
        f"{selected['task']}"
    )

    print(
        f"Selected model: "
        f"{selected['best_model']}"
    )

    save_model(
        selected
    )

    print(
        f"\nTotal runtime: "
        f"{time.time() - total_start:.1f}s"
    )

    print(
        "\nFITNESS MODEL COMPLETE."
    )


if __name__ == "__main__":
    main()

    print(
        "\n" + "=" * 70
    )

    print(
        "FITNESS MODEL COMPLETE."
    )

    print(
        "=" * 70
    )