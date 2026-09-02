r"""
train_remaining_models.py
FIXED PATH VERSION

Can be run from either:
    C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai
or:
    C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai\ml\training

It automatically discovers the actual digital_twin_ai project root.
"""

from __future__ import annotations

import json
import time
import datetime
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import (
    train_test_split,
    KFold,
    StratifiedKFold,
    TimeSeriesSplit,
    cross_validate,
)
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    LogisticRegression,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
)

warnings.filterwarnings("ignore")


# ============================================================
# PROJECT ROOT DISCOVERY
# ============================================================

def find_project_root() -> Path:
    """
    Locate the digital_twin_ai directory robustly.

    Works whether this script is placed in:
        digital_twin_ai/
    or:
        digital_twin_ai/ml/training/
    """
    current = Path(__file__).resolve()

    candidates = [current.parent] + list(current.parents)

    for folder in candidates:
        if (
            folder.name.lower() == "digital_twin_ai"
            and (folder / "backend").exists()
            and (folder / "ml").exists()
        ):
            return folder

    # Fallback: current working directory.
    cwd = Path.cwd().resolve()

    if (
        cwd.name.lower() == "digital_twin_ai"
        and (cwd / "backend").exists()
    ):
        return cwd

    raise FileNotFoundError(
        "Could not locate digital_twin_ai project root.\n"
        f"Script location: {Path(__file__).resolve()}\n"
        f"Current directory: {cwd}"
    )


PROJECT_ROOT = find_project_root()

# Your actual structure is:
#
# INFO_PROJECT/
# ├── Datasets/
# │   └── prepared_datasets/
# └── digital_twin_ai/
#     ├── backend/
#     └── ml/
#
# So Datasets is a sibling of digital_twin_ai.
DATA_DIR = (
    PROJECT_ROOT.parent
    / "Datasets"
    / "prepared_datasets"
)

MODELS_DIR = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "ml_models"
)

REPORTS_DIR = (
    PROJECT_ROOT
    / "ml"
    / "reports"
)

MODELS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

for domain in [
    "fitness",
    "lifestyle",
    "financial",
    "forecasting",
]:
    (MODELS_DIR / domain).mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# OPTIONAL XGBOOST
# ============================================================

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBRegressor = None
    XGBOOST_AVAILABLE = False


# ============================================================
# HELPERS
# ============================================================

def artifact_paths(domain: str) -> dict[str, Path]:
    folder = MODELS_DIR / domain

    return {
        "model": folder / "model.joblib",
        "metadata": folder / "metadata.json",
        "feature_info": folder / "feature_info.json",
    }


def artifacts_exist(domain: str) -> bool:
    return all(
        path.exists()
        for path in artifact_paths(domain).values()
    )


def print_skip(domain: str):
    paths = artifact_paths(domain)

    print("\n" + "=" * 60)
    print(f"SKIPPING {domain.upper()} MODEL")
    print("=" * 60)
    print("Existing artifacts found:")
    print(f"  model       : {paths['model']}")
    print(f"  metadata    : {paths['metadata']}")
    print(f"  feature_info: {paths['feature_info']}")
    print("No retraining will be performed.")


def make_onehot():
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


def get_preprocessor(
    numerical_cols,
    categorical_cols,
):
    transformers = []

    if numerical_cols:
        num_pipe = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                ),
                (
                    "scaler",
                    StandardScaler(),
                ),
            ]
        )

        transformers.append(
            ("num", num_pipe, numerical_cols)
        )

    if categorical_cols:
        cat_pipe = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    ),
                ),
                (
                    "onehot",
                    make_onehot(),
                ),
            ]
        )

        transformers.append(
            ("cat", cat_pipe, categorical_cols)
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


def build_pipeline(
    model,
    numerical_cols,
    categorical_cols,
):
    return Pipeline(
        steps=[
            (
                "preprocessor",
                get_preprocessor(
                    numerical_cols,
                    categorical_cols,
                ),
            ),
            ("model", model),
        ]
    )


def get_regressors():
    models = {
        "LinearRegression":
            LinearRegression(),

        "Ridge":
            Ridge(alpha=1.0),

        "RandomForestRegressor":
            RandomForestRegressor(
                n_estimators=50,
                n_jobs=-1,
                random_state=42,
            ),

        "ExtraTreesRegressor":
            ExtraTreesRegressor(
                n_estimators=50,
                n_jobs=-1,
                random_state=42,
            ),

        "GradientBoostingRegressor":
            GradientBoostingRegressor(
                n_estimators=50,
                learning_rate=0.05,
                max_depth=3,
                random_state=42,
            ),
    }

    if XGBOOST_AVAILABLE:
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


def get_classifiers():
    return {
        "LogisticRegression":
            LogisticRegression(
                max_iter=1000,
                random_state=42,
            ),
        "DecisionTreeClassifier":
            DecisionTreeClassifier(
                random_state=42
            ),
        "RandomForestClassifier":
            RandomForestClassifier(
                n_estimators=50,
                n_jobs=-1,
                random_state=42,
            ),
        "ExtraTreesClassifier":
            ExtraTreesClassifier(
                n_estimators=50,
                n_jobs=-1,
                random_state=42,
            ),
        "GradientBoostingClassifier":
            GradientBoostingClassifier(
                n_estimators=50,
                random_state=42,
            ),
    }


def get_feature_importances(pipeline):
    try:
        model = pipeline.named_steps["model"]
        preprocessor = pipeline.named_steps["preprocessor"]

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            coef = model.coef_
            if getattr(coef, "ndim", 1) > 1:
                importances = np.mean(
                    np.abs(coef),
                    axis=0,
                )
            else:
                importances = np.abs(coef)
        else:
            return None

        names = []

        for transformer_name, transformer, columns in (
            preprocessor.transformers_
        ):
            if (
                transformer_name == "num"
                and transformer != "drop"
            ):
                names.extend(list(columns))

            elif (
                transformer_name == "cat"
                and transformer != "drop"
            ):
                encoder = (
                    transformer.named_steps["onehot"]
                )

                names.extend(
                    encoder.get_feature_names_out(
                        columns
                    ).tolist()
                )

        if len(names) != len(importances):
            return None

        return (
            pd.DataFrame(
                {
                    "feature": names,
                    "importance": importances,
                }
            )
            .sort_values(
                "importance",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    except Exception as exc:
        print(
            f"[WARN] Feature importance failed: {exc}"
        )
        return None


# ============================================================
# GENERAL TRAINING
# ============================================================

def train_and_evaluate(
    df,
    target,
    problem_type,
    domain,
    num_cols,
    cat_cols,
    remove_cols,
    removal_reasons,
):
    print("\n" + "=" * 60)
    print(f"TRAINING {domain.upper()} MODEL")
    print("=" * 60)

    df_clean = (
        df.drop(
            columns=remove_cols,
            errors="ignore",
        )
        .dropna(subset=[target])
        .copy()
    )

    X = df_clean.drop(columns=[target])
    y = df_clean[target]

    if problem_type == "regression":
        models = get_regressors()

        scoring = {
            "rmse":
                "neg_root_mean_squared_error",
            "mae":
                "neg_mean_absolute_error",
            "r2":
                "r2",
        }

        cv3 = KFold(
            n_splits=3,
            shuffle=True,
            random_state=42,
        )

        cv5 = KFold(
            n_splits=5,
            shuffle=True,
            random_state=42,
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
        )

        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train,
            y_train,
            test_size=0.20,
            random_state=42,
        )

    else:
        models = get_classifiers()

        scoring = {
            "accuracy":
                "accuracy",
            "precision":
                "precision_macro",
            "recall":
                "recall_macro",
            "f1":
                "f1_macro",
        }

        cv3 = StratifiedKFold(
            n_splits=3,
            shuffle=True,
            random_state=42,
        )

        cv5 = StratifiedKFold(
            n_splits=5,
            shuffle=True,
            random_state=42,
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=42,
        )

        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train,
            y_train,
            test_size=0.20,
            stratify=y_train,
            random_state=42,
        )

    print(
        f"Train={len(X_train):,} | "
        f"Val={len(X_val):,} | "
        f"Test={len(X_test):,}"
    )

    results = []

    # --------------------------------------------------------
    # 3-fold screening
    # --------------------------------------------------------
    print("\nStep A: 3-fold candidate screening")

    for i, (name, model) in enumerate(
        models.items(),
        start=1,
    ):
        print(
            f"[{i}/{len(models)}] {name}..."
        )

        pipeline = build_pipeline(
            model,
            num_cols,
            cat_cols,
        )

        start = time.time()

        try:
            cv = cross_validate(
                pipeline,
                X_train,
                y_train,
                cv=cv3,
                scoring=scoring,
                n_jobs=-1,
                return_train_score=False,
            )

            elapsed = time.time() - start

            result = {
                "Model": name,
                "Training Time": elapsed,
            }

            if problem_type == "regression":
                result["3-Fold CV RMSE"] = -cv[
                    "test_rmse"
                ].mean()
                result["3-Fold CV MAE"] = -cv[
                    "test_mae"
                ].mean()
                result["3-Fold CV R2"] = cv[
                    "test_r2"
                ].mean()

                metric = result[
                    "3-Fold CV RMSE"
                ]
                print(
                    f"    RMSE={metric:.4f} "
                    f"| {elapsed:.1f}s"
                )
            else:
                result["CV Accuracy"] = cv[
                    "test_accuracy"
                ].mean()
                result["CV Precision"] = cv[
                    "test_precision"
                ].mean()
                result["CV Recall"] = cv[
                    "test_recall"
                ].mean()
                result["CV F1"] = cv[
                    "test_f1"
                ].mean()

                metric = result["CV F1"]
                print(
                    f"    F1={metric:.4f} "
                    f"| {elapsed:.1f}s"
                )

            results.append(result)

        except Exception as exc:
            print(
                f"    FAILED: {exc}"
            )

    if not results:
        raise RuntimeError(
            f"No successful candidates for {domain}."
        )

    res_df = pd.DataFrame(results)

    # Top three
    if problem_type == "regression":
        top3 = (
            res_df
            .nsmallest(
                min(3, len(res_df)),
                "3-Fold CV RMSE",
            )["Model"]
            .tolist()
        )
    else:
        top3 = (
            res_df
            .nlargest(
                min(3, len(res_df)),
                "CV F1",
            )["Model"]
            .tolist()
        )

    print(
        f"\nStep B: TOP 3 -> {top3}"
    )

    best_model_name = None
    best_val_score = (
        np.inf
        if problem_type == "regression"
        else -np.inf
    )

    # --------------------------------------------------------
    # 5-fold finalists
    # --------------------------------------------------------
    print(
        "\nStep C/D: 5-fold finalists + validation"
    )

    for name in top3:

        print(
            f"Finalist: {name}"
        )

        pipeline = build_pipeline(
            models[name],
            num_cols,
            cat_cols,
        )

        start = time.time()

        cv5_res = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv5,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        pipeline.fit(
            X_train_split,
            y_train_split,
        )

        pred = pipeline.predict(
            X_val
        )

        idx = res_df.index[
            res_df["Model"] == name
        ].tolist()[0]

        elapsed = time.time() - start

        if problem_type == "regression":
            cv_rmse = -cv5_res[
                "test_rmse"
            ].mean()

            cv_mae = -cv5_res[
                "test_mae"
            ].mean()

            cv_r2 = cv5_res[
                "test_r2"
            ].mean()

            val_rmse = np.sqrt(
                mean_squared_error(
                    y_val,
                    pred,
                )
            )

            val_mae = (
                mean_absolute_error(
                    y_val,
                    pred,
                )
            )

            val_r2 = r2_score(
                y_val,
                pred,
            )

            res_df.at[
                idx, "5-Fold CV RMSE"
            ] = cv_rmse

            res_df.at[
                idx, "5-Fold CV MAE"
            ] = cv_mae

            res_df.at[
                idx, "5-Fold CV R2"
            ] = cv_r2

            res_df.at[
                idx, "Validation RMSE"
            ] = val_rmse

            res_df.at[
                idx, "Validation MAE"
            ] = val_mae

            res_df.at[
                idx, "Validation R2"
            ] = val_r2

            print(
                f"    CV RMSE={cv_rmse:.4f} "
                f"| Val RMSE={val_rmse:.4f} "
                f"| {elapsed:.1f}s"
            )

            if val_rmse < best_val_score:
                best_val_score = val_rmse
                best_model_name = name

        else:
            cv_f1 = cv5_res[
                "test_f1"
            ].mean()

            val_f1 = f1_score(
                y_val,
                pred,
                average="macro",
                zero_division=0,
            )

            val_acc = accuracy_score(
                y_val,
                pred,
            )

            val_prec = precision_score(
                y_val,
                pred,
                average="macro",
                zero_division=0,
            )

            val_rec = recall_score(
                y_val,
                pred,
                average="macro",
                zero_division=0,
            )

            res_df.at[
                idx, "5-Fold CV F1"
            ] = cv_f1

            res_df.at[
                idx, "Validation F1"
            ] = val_f1

            res_df.at[
                idx, "Validation Accuracy"
            ] = val_acc

            res_df.at[
                idx, "Validation Precision"
            ] = val_prec

            res_df.at[
                idx, "Validation Recall"
            ] = val_rec

            print(
                f"    CV F1={cv_f1:.4f} "
                f"| Val F1={val_f1:.4f} "
                f"| {elapsed:.1f}s"
            )

            if val_f1 > best_val_score:
                best_val_score = val_f1
                best_model_name = name

    print(
        f"\nStep E: BEST MODEL -> "
        f"{best_model_name}"
    )

    # --------------------------------------------------------
    # Retrain on TRAIN + VALIDATION
    # --------------------------------------------------------
    best_pipeline = build_pipeline(
        models[best_model_name],
        num_cols,
        cat_cols,
    )

    X_train_val = pd.concat(
        [X_train_split, X_val],
        axis=0,
    )

    y_train_val = pd.concat(
        [y_train_split, y_val],
        axis=0,
    )

    print(
        "\nStep F: Retraining best model "
        "on train + validation..."
    )

    best_pipeline.fit(
        X_train_val,
        y_train_val,
    )

    # --------------------------------------------------------
    # Final untouched test
    # --------------------------------------------------------
    print(
        "\nStep G: Final untouched test..."
    )

    test_pred = best_pipeline.predict(
        X_test
    )

    if problem_type == "regression":
        test_rmse = np.sqrt(
            mean_squared_error(
                y_test,
                test_pred,
            )
        )
        test_mae = mean_absolute_error(
            y_test,
            test_pred,
        )
        test_r2 = r2_score(
            y_test,
            test_pred,
        )

        test_primary = test_rmse

        print(
            f"Final Test RMSE={test_rmse:.4f}"
        )
        print(
            f"Final Test MAE={test_mae:.4f}"
        )
        print(
            f"Final Test R2={test_r2:.4f}"
        )

    else:
        test_acc = accuracy_score(
            y_test,
            test_pred,
        )
        test_prec = precision_score(
            y_test,
            test_pred,
            average="macro",
            zero_division=0,
        )
        test_rec = recall_score(
            y_test,
            test_pred,
            average="macro",
            zero_division=0,
        )
        test_f1 = f1_score(
            y_test,
            test_pred,
            average="macro",
            zero_division=0,
        )

        test_primary = test_f1

        print(
            f"Final Test Accuracy={test_acc:.4f}"
        )
        print(
            f"Final Test Precision={test_prec:.4f}"
        )
        print(
            f"Final Test Recall={test_rec:.4f}"
        )
        print(
            f"Final Test F1={test_f1:.4f}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------
    paths = artifact_paths(domain)

    joblib.dump(
        best_pipeline,
        paths["model"],
    )

    best_idx = res_df.index[
        res_df["Model"] == best_model_name
    ].tolist()[0]

    if problem_type == "regression":
        cv_primary = float(
            res_df.at[
                best_idx,
                "5-Fold CV RMSE",
            ]
        )

        metrics = {
            "cv_rmse": cv_primary,
            "validation_rmse":
                float(best_val_score),
            "test_rmse":
                float(test_rmse),
            "test_mae":
                float(test_mae),
            "test_r2":
                float(test_r2),
        }

    else:
        cv_primary = float(
            res_df.at[
                best_idx,
                "5-Fold CV F1",
            ]
        )

        metrics = {
            "cv_f1":
                cv_primary,
            "validation_f1":
                float(best_val_score),
            "test_f1":
                float(test_f1),
            "test_accuracy":
                float(test_acc),
            "test_precision":
                float(test_prec),
            "test_recall":
                float(test_rec),
        }

    metadata = {
        "model_name":
            best_model_name,
        "problem_type":
            problem_type,
        "target":
            target,
        "dataset":
            f"{domain}_clean.csv",
        "version":
            "1.0",
        "training_date":
            datetime.datetime.now().isoformat(),
        "rows":
            int(len(df_clean)),
        "metrics":
            metrics,
    }

    with open(
        paths["metadata"],
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            indent=4,
        )

    feature_info = {
        "final_features":
            X.columns.tolist(),
        "numerical_features":
            num_cols,
        "categorical_features":
            cat_cols,
        "removed_features":
            remove_cols,
        "removal_reasons":
            removal_reasons,
    }

    with open(
        paths["feature_info"],
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            feature_info,
            f,
            indent=4,
        )

    # Reports
    res_df.to_csv(
        REPORTS_DIR
        / f"{domain}_model_comparison.csv",
        index=False,
    )

    importance_df = get_feature_importances(
        best_pipeline
    )

    if importance_df is not None:

        importance_df.to_csv(
            REPORTS_DIR
            / f"{domain}_feature_importance.csv",
            index=False,
        )

    report = f"""# {domain.capitalize()} Model Training Report

Dataset:
{metadata['dataset']}

Target:
{target}

Problem Type:
{problem_type}

Best Model:
{best_model_name}

CV Primary:
{cv_primary:.4f}

Validation Primary:
{best_val_score:.4f}

Test Primary:
{test_primary:.4f}

Saved Model:
{paths['model']}
"""

    with open(
        REPORTS_DIR
        / f"{domain}_training_report.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(report)

    # Update registry while preserving existing models.
    registry_path = (
        MODELS_DIR
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

    registry[domain] = {
        "model_path":
            str(paths["model"]),
        "model_name":
            best_model_name,
        "target":
            target,
        "problem_type":
            problem_type,
        "version":
            "1.0",
        "primary_metric":
            "RMSE"
            if problem_type == "regression"
            else "F1",
        "primary_metric_value":
            float(test_primary),
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

    return {
        "Domain":
            domain.capitalize(),
        "Dataset":
            metadata["dataset"],
        "Target":
            target,
        "Problem Type":
            problem_type,
        "Best Model":
            best_model_name,
        "CV":
            f"{('RMSE' if problem_type == 'regression' else 'F1')}="
            f"{cv_primary:.4f}",
        "Validation":
            f"{('RMSE' if problem_type == 'regression' else 'F1')}="
            f"{best_val_score:.4f}",
        "Test":
            f"{('RMSE' if problem_type == 'regression' else 'F1')}="
            f"{test_primary:.4f}",
        "Saved Model":
            str(paths["model"]),
    }


# ============================================================
# FORECASTING
# ============================================================

def train_forecasting(
    df,
    target,
    num_cols,
    cat_cols,
    remove_cols,
    removal_reasons,
):
    print(
        "\n" + "=" * 60
    )
    print(
        "TRAINING FORECASTING MODEL"
    )
    print(
        "=" * 60
    )

    df_clean = (
        df.drop(
            columns=remove_cols,
            errors="ignore",
        )
        .dropna(
            subset=[target]
        )
        .copy()
    )

    # Sort using ORIGINAL month_date before dropping it.
    if "month_date" in df.columns:

        sort_date = pd.to_datetime(
            df.loc[
                df_clean.index,
                "month_date",
            ],
            errors="coerce",
        )

        df_clean["_sort_date"] = (
            sort_date
        )

        df_clean = (
            df_clean
            .sort_values(
                "_sort_date"
            )
            .drop(
                columns=["_sort_date"]
            )
        )

    elif "month" in df_clean.columns:

        df_clean = (
            df_clean
            .sort_values("month")
        )

    X = df_clean.drop(
        columns=[target]
    )

    y = df_clean[target]

    n = len(df_clean)

    train_end = int(
        n * 0.80
    )

    val_end = int(
        n * 0.90
    )

    X_train = X.iloc[
        :train_end
    ]

    y_train = y.iloc[
        :train_end
    ]

    X_val = X.iloc[
        train_end:val_end
    ]

    y_val = y.iloc[
        train_end:val_end
    ]

    X_test = X.iloc[
        val_end:
    ]

    y_test = y.iloc[
        val_end:
    ]

    X_train_val = X.iloc[
        :val_end
    ]

    y_train_val = y.iloc[
        :val_end
    ]

    print(
        f"Train={len(X_train):,} | "
        f"Val={len(X_val):,} | "
        f"Test={len(X_test):,}"
    )

    # IMPORTANT:
    # Do not use RF / ExtraTrees here because your previous run
    # showed RF taking ~1181 seconds with almost no improvement
    # over Ridge.
    models = {
        "LinearRegression":
            LinearRegression(),

        "Ridge":
            Ridge(alpha=1.0),

        "GradientBoostingRegressor":
            GradientBoostingRegressor(
                n_estimators=80,
                learning_rate=0.05,
                max_depth=3,
                random_state=42,
            ),
    }

    if XGBOOST_AVAILABLE:
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

    scoring = {
        "rmse":
            "neg_root_mean_squared_error",
        "mae":
            "neg_mean_absolute_error",
        "r2":
            "r2",
    }

    cv3 = TimeSeriesSplit(
        n_splits=3
    )

    cv5 = TimeSeriesSplit(
        n_splits=5
    )

    # --------------------------------------------------------
    # Screening
    # --------------------------------------------------------
    print(
        "\nStep A: 3-fold TimeSeries CV"
    )

    results = []

    for i, (name, model) in enumerate(
        models.items(),
        start=1,
    ):

        print(
            f"[{i}/{len(models)}] "
            f"{name}..."
        )

        pipeline = build_pipeline(
            model,
            num_cols,
            cat_cols,
        )

        start = time.time()

        try:
            cv = cross_validate(
                pipeline,
                X_train,
                y_train,
                cv=cv3,
                scoring=scoring,
                n_jobs=-1,
                return_train_score=False,
            )

            elapsed = (
                time.time()
                - start
            )

            row = {
                "Model": name,
                "3-Fold CV RMSE": -cv[
                    "test_rmse"
                ].mean(),
                "3-Fold CV MAE": -cv[
                    "test_mae"
                ].mean(),
                "3-Fold CV R2": cv[
                    "test_r2"
                ].mean(),
                "Training Time": elapsed,
            }

            results.append(row)

            print(
                f"    RMSE="
                f"{row['3-Fold CV RMSE']:.4f} "
                f"| {elapsed:.1f}s"
            )

        except Exception as exc:
            print(
                f"    FAILED: {exc}"
            )

    if not results:
        raise RuntimeError(
            "No forecasting candidate succeeded."
        )

    res_df = pd.DataFrame(
        results
    )

    top3 = (
        res_df
        .nsmallest(
            min(3, len(res_df)),
            "3-Fold CV RMSE",
        )["Model"]
        .tolist()
    )

    print(
        f"\nStep B: TOP {len(top3)} -> {top3}"
    )

    # --------------------------------------------------------
    # Finalists
    # --------------------------------------------------------
    print(
        "\nStep C/D: 5-fold TimeSeries CV + validation"
    )

    best_name = None
    best_val = np.inf

    for name in top3:

        print(
            f"Finalist: {name}"
        )

        pipeline = build_pipeline(
            models[name],
            num_cols,
            cat_cols,
        )

        start = time.time()

        cv5res = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv5,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        pipeline.fit(
            X_train,
            y_train,
        )

        val_pred = pipeline.predict(
            X_val
        )

        cv_rmse = -cv5res[
            "test_rmse"
        ].mean()

        cv_mae = -cv5res[
            "test_mae"
        ].mean()

        cv_r2 = cv5res[
            "test_r2"
        ].mean()

        val_rmse = np.sqrt(
            mean_squared_error(
                y_val,
                val_pred,
            )
        )

        val_mae = mean_absolute_error(
            y_val,
            val_pred,
        )

        val_r2 = r2_score(
            y_val,
            val_pred,
        )

        idx = res_df.index[
            res_df["Model"] == name
        ].tolist()[0]

        res_df.at[
            idx,
            "5-Fold CV RMSE"
        ] = cv_rmse

        res_df.at[
            idx,
            "5-Fold CV MAE"
        ] = cv_mae

        res_df.at[
            idx,
            "5-Fold CV R2"
        ] = cv_r2

        res_df.at[
            idx,
            "Validation RMSE"
        ] = val_rmse

        res_df.at[
            idx,
            "Validation MAE"
        ] = val_mae

        res_df.at[
            idx,
            "Validation R2"
        ] = val_r2

        elapsed = (
            time.time()
            - start
        )

        print(
            f"    CV RMSE={cv_rmse:.4f} "
            f"| Val RMSE={val_rmse:.4f} "
            f"| {elapsed:.1f}s"
        )

        if val_rmse < best_val:
            best_val = val_rmse
            best_name = name

    print(
        f"\nStep E: BEST FORECASTING MODEL -> "
        f"{best_name}"
    )

    # --------------------------------------------------------
    # Final train + validation
    # --------------------------------------------------------
    best_pipeline = build_pipeline(
        models[best_name],
        num_cols,
        cat_cols,
    )

    print(
        "\nStep F: Retrain on TRAIN + VALIDATION"
    )

    best_pipeline.fit(
        X_train_val,
        y_train_val,
    )

    # --------------------------------------------------------
    # Test
    # --------------------------------------------------------
    print(
        "\nStep G: Untouched TEST"
    )

    test_pred = best_pipeline.predict(
        X_test
    )

    test_rmse = np.sqrt(
        mean_squared_error(
            y_test,
            test_pred,
        )
    )

    test_mae = mean_absolute_error(
        y_test,
        test_pred,
    )

    test_r2 = r2_score(
        y_test,
        test_pred,
    )

    print(
        f"Final Test RMSE={test_rmse:.4f}"
    )

    print(
        f"Final Test MAE={test_mae:.4f}"
    )

    print(
        f"Final Test R2={test_r2:.4f}"
    )

    paths = artifact_paths(
        "forecasting"
    )

    joblib.dump(
        best_pipeline,
        paths["model"],
    )

    best_idx = res_df.index[
        res_df["Model"] == best_name
    ].tolist()[0]

    metadata = {
        "model_name":
            best_name,
        "problem_type":
            "regression",
        "target":
            target,
        "dataset":
            "transaction_forecasting_clean.csv",
        "version":
            "1.0",
        "training_date":
            datetime.datetime.now().isoformat(),
        "metrics": {
            "cv_rmse":
                float(
                    res_df.at[
                        best_idx,
                        "5-Fold CV RMSE",
                    ]
                ),
            "validation_rmse":
                float(best_val),
            "test_rmse":
                float(test_rmse),
            "test_mae":
                float(test_mae),
            "test_r2":
                float(test_r2),
        },
    }

    with open(
        paths["metadata"],
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            indent=4,
        )

    feature_info = {
        "final_features":
            X.columns.tolist(),
        "numerical_features":
            num_cols,
        "categorical_features":
            cat_cols,
        "removed_features":
            remove_cols,
        "removal_reasons":
            removal_reasons,
        "split_strategy":
            "Chronological 80/10/10",
    }

    with open(
        paths["feature_info"],
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            feature_info,
            f,
            indent=4,
        )

    res_df.to_csv(
        REPORTS_DIR
        / "forecasting_model_comparison.csv",
        index=False,
    )

    importance_df = get_feature_importances(
        best_pipeline
    )

    if importance_df is not None:

        importance_df.to_csv(
            REPORTS_DIR
            / "forecasting_feature_importance.csv",
            index=False,
        )

    with open(
        REPORTS_DIR
        / "forecasting_training_report.md",
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            f"# Forecasting Model Training Report\n\n"
            f"- Dataset: transaction_forecasting_clean.csv\n"
            f"- Target: {target}\n"
            f"- Best model: {best_name}\n"
            f"- 5-fold TimeSeries CV RMSE: "
            f"{metadata['metrics']['cv_rmse']:.4f}\n"
            f"- Validation RMSE: "
            f"{best_val:.4f}\n"
            f"- Test RMSE: "
            f"{test_rmse:.4f}\n"
            f"- Test MAE: "
            f"{test_mae:.4f}\n"
            f"- Test R2: "
            f"{test_r2:.4f}\n\n"
            f"RandomForestRegressor and ExtraTreesRegressor were "
            f"excluded because the previous run showed "
            f"Random Forest taking about 1181 seconds for "
            f"3-fold TimeSeries CV while Ridge had nearly the same RMSE.\n"
        )

    # Preserve existing registry.
    registry_path = (
        MODELS_DIR
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

    registry["forecasting"] = {
        "model_path":
            str(paths["model"]),
        "model_name":
            best_name,
        "target":
            target,
        "problem_type":
            "regression",
        "version":
            "1.0",
        "primary_metric":
            "RMSE",
        "primary_metric_value":
            float(test_rmse),
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

    return {
        "Domain":
            "Forecasting",
        "Target":
            target,
        "Best Model":
            best_name,
        "CV":
            metadata["metrics"]["cv_rmse"],
        "Validation":
            best_val,
        "Test":
            test_rmse,
        "Saved Model":
            str(paths["model"]),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "DIGITAL TWIN AI - REMAINING MODEL TRAINING"
    )
    print("=" * 70)

    print(
        "\nProject root:"
    )
    print(
        f"  {PROJECT_ROOT}"
    )

    print(
        "\nDataset directory:"
    )
    print(
        f"  {DATA_DIR}"
    )

    print(
        "\nModel directory:"
    )
    print(
        f"  {MODELS_DIR}"
    )

    # Fail early if the dataset folder is wrong.
    if not DATA_DIR.exists():

        raise FileNotFoundError(
            "\nPrepared dataset directory was not found:\n"
            f"{DATA_DIR}\n\n"
            "Expected structure:\n"
            "INFO_PROJECT/\n"
            "├── Datasets/\n"
            "│   └── prepared_datasets/\n"
            "└── digital_twin_ai/\n"
            "    └── backend/\n"
        )

    summaries = []

    # ========================================================
    # ACADEMIC — ALWAYS SKIP
    # ========================================================

    print(
        "\nAcademic model is already complete."
    )
    print(
        "Academic will NOT be trained."
    )

    # ========================================================
    # FITNESS
    # ========================================================

    if artifacts_exist("fitness"):

        print_skip("fitness")

    else:

        path = (
            DATA_DIR
            / "fitness_clean.csv"
        )

        if not path.exists():

            print(
                f"[SKIP] Missing dataset: {path}"
            )

        else:

            df = pd.read_csv(
                path,
                low_memory=False,
            )

            summaries.append(
                train_and_evaluate(
                    df=df,
                    target="calories_burned",
                    problem_type="regression",
                    domain="fitness",
                    num_cols=[
                        "age",
                        "height_cm",
                        "weight_kg",
                        "steps",
                        "sleep_hours",
                        "water_intake_liters",
                        "active_minutes",
                        "heart_rate",
                        "stress_level",
                        "bmi",
                        "steps_per_active_minute",
                    ],
                    cat_cols=[
                        "gender",
                        "workout_type",
                        "mood",
                        "day_of_week",
                        "month",
                        "activity_level",
                    ],
                    remove_cols=[
                        "id",
                        "fitness_user_id",
                        "full_name",
                    ],
                    removal_reasons={
                        "id": "Identifier",
                        "fitness_user_id": "Identifier",
                        "full_name": "Identifier",
                    },
                )
            )

    # ========================================================
    # LIFESTYLE
    # ========================================================

    if artifacts_exist("lifestyle"):

        print_skip("lifestyle")

    else:

        path = (
            DATA_DIR
            / "lifestyle_clean.csv"
        )

        if not path.exists():

            print(
                f"[SKIP] Missing dataset: {path}"
            )

        else:

            df = pd.read_csv(
                path,
                low_memory=False,
            )

            summaries.append(
                train_and_evaluate(
                    df=df,
                    target="sleep_disorder",
                    problem_type="classification",
                    domain="lifestyle",
                    num_cols=[
                        "age",
                        "sleep_hours",
                        "sleep_quality",
                        "physical_activity_level",
                        "stress_level",
                        "heart_rate",
                        "daily_steps",
                        "activity_sleep_balance",
                        "lifestyle_risk_score",
                    ],
                    cat_cols=[
                        "gender",
                        "occupation",
                        "bmi_category",
                        "blood_pressure",
                    ],
                    remove_cols=[
                        "id",
                        "client_id",
                    ],
                    removal_reasons={
                        "id": "Identifier",
                        "client_id": "Identifier",
                    },
                )
            )

    # ========================================================
    # FINANCIAL
    # ========================================================

    if artifacts_exist("financial"):

        print_skip("financial")

    else:

        path = (
            DATA_DIR
            / "financial_profile_clean.csv"
        )

        if not path.exists():

            print(
                f"[SKIP] Missing dataset: {path}"
            )

        else:

            df = pd.read_csv(
                path,
                low_memory=False,
            )

            summaries.append(
                train_and_evaluate(
                    df=df,
                    target="disposable_income",
                    problem_type="regression",
                    domain="financial",
                    num_cols=[
                        "income",
                        "age",
                        "dependents",
                        "desired_savings_percentage",
                        "desired_savings",
                    ],
                    cat_cols=[
                        "occupation",
                        "city_tier",
                    ],
                    remove_cols=[
                        "id",
                        "client_id",
                        "total_expenses",
                        "calculated_savings",
                        "expense_ratio",
                        "saving_rate",
                        "financial_stability_score",
                        "potential_savings_groceries",
                        "potential_savings_transport",
                        "potential_savings_eating_out",
                        "potential_savings_entertainment",
                        "potential_savings_utilities",
                        "potential_savings_healthcare",
                        "potential_savings_education",
                        "potential_savings_miscellaneous",
                        "groceries",
                        "transport",
                        "eating_out",
                        "entertainment",
                        "utilities",
                        "healthcare",
                        "education",
                        "miscellaneous",
                        "rent",
                        "loan_repayment",
                        "insurance",
                    ],
                    removal_reasons={
                        "id": "Identifier",
                        "client_id": "Identifier",
                        "total_expenses": "Derived/leaky",
                        "calculated_savings": "Derived/leaky",
                        "expense_ratio": "Derived financial ratio",
                        "saving_rate": "Derived financial ratio",
                        "financial_stability_score": "Engineered score derived from inputs",
                    },
                )
            )

    # ========================================================
    # FORECASTING
    # ========================================================

    if artifacts_exist("forecasting"):

        print_skip("forecasting")

    else:

        path = (
            DATA_DIR
            / "transaction_forecasting_clean.csv"
        )

        if not path.exists():

            print(
                f"[SKIP] Missing dataset: {path}"
            )

        else:

            df = pd.read_csv(
                path,
                low_memory=False,
            )

            summaries.append(
                train_forecasting(
                    df=df,
                    target="next_month_spending",
                    num_cols=[
                        "total_signed_amount",
                        "total_absolute_amount",
                        "positive_amount",
                        "negative_amount",
                        "transaction_count",
                        "positive_transaction_count",
                        "negative_transaction_count",
                        "average_transaction_amount",
                        "unique_merchants",
                        "unique_cards",
                        "error_count",
                        "total_absolute_amount_lag_1",
                        "total_absolute_amount_rolling_3m",
                        "positive_amount_lag_1",
                        "positive_amount_rolling_3m",
                        "negative_amount_lag_1",
                        "negative_amount_rolling_3m",
                        "transaction_count_lag_1",
                        "transaction_count_rolling_3m",
                    ],
                    cat_cols=[
                        "month",
                    ],
                    remove_cols=[
                        "client_id",
                        "next_month_transaction_count",
                        "month_date",
                    ],
                    removal_reasons={
                        "client_id":
                            "Identifier",
                        "next_month_transaction_count":
                            "Future target information",
                        "month_date":
                            "Used for chronological sorting",
                    },
                )
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n" + "=" * 70
    )
    print(
        "FINAL SUMMARY"
    )
    print(
        "=" * 70
    )

    if summaries:

        summary_df = pd.DataFrame(
            summaries
        )

        print(
            summary_df.to_string(
                index=False
            )
        )

    else:

        print(
            "No new model was trained."
        )

        print(
            "Either all models already exist "
            "or required datasets are missing."
        )

    print(
        "\nAcademic model remains untouched."
    )

    print(
        "\nNo FastAPI, frontend, database, "
        "or authentication code was modified."
    )


if __name__ == "__main__":
    main()
