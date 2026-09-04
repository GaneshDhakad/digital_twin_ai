"""
train_lifestyle.py
============================================================
Train and deploy the Lifestyle / Sleep Disorder 3-class model.

Target:
    sleep_disorder -> Normal | Insomnia | Sleep Apnea

Expected dataset:
    lifestyle_clean.csv

Expected dataset location:
    INFO_PROJECT/
    ├── Datasets/
    │   └── prepared_datasets/
    │       └── lifestyle_clean.csv
    └── digital_twin_ai/
        └── ml/
            └── training/
                └── train_lifestyle.py

The script:
1. Loads lifestyle_clean.csv.
2. Validates the required columns and 3 target classes.
3. Uses a leakage-safe sklearn preprocessing pipeline.
4. Compares several classifiers using stratified 5-fold CV.
5. Selects the model with the best macro F1.
6. Evaluates the selected model on a held-out test set.
7. Retrains the selected pipeline on the full dataset.
8. Backs up the existing Lifestyle model artifacts.
9. Replaces:
       backend/app/ml_models/lifestyle/model.joblib
       backend/app/ml_models/lifestyle/metadata.json
       backend/app/ml_models/lifestyle/feature_info.json
10. Updates the Lifestyle entry in:
       backend/app/ml_models/model_registry.json
11. Writes model comparison, feature importance and training report
    into ml/reports/.

Run from project root:
    python ml/training/train_lifestyle.py

Or explicitly provide the dataset:
    python ml/training/train_lifestyle.py --data "C:/path/to/lifestyle_clean.csv"
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


# ============================================================
# PROJECT PATHS
# ============================================================

def find_project_root() -> Path:
    """Find the digital_twin_ai project directory."""
    current = Path(__file__).resolve()

    for folder in [current.parent, *current.parents]:
        if (
            folder.name.lower() == "digital_twin_ai"
            and (folder / "backend").exists()
            and (folder / "ml").exists()
        ):
            return folder

    cwd = Path.cwd().resolve()

    if (
        cwd.name.lower() == "digital_twin_ai"
        and (cwd / "backend").exists()
    ):
        return cwd

    raise FileNotFoundError(
        "Could not locate the digital_twin_ai project root.\n"
        f"Script location: {Path(__file__).resolve()}\n"
        f"Current working directory: {cwd}"
    )


PROJECT_ROOT = find_project_root()

DATA_DIR = (
    PROJECT_ROOT.parent
    / "Datasets"
    / "prepared_datasets"
)

DEFAULT_DATA_PATH = DATA_DIR / "lifestyle_clean.csv"

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "ml_models"
    / "lifestyle"
)

MODELS_ROOT = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "ml_models"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "reports"
)

MODEL_PATH = MODEL_DIR / "model.joblib"
METADATA_PATH = MODEL_DIR / "metadata.json"
FEATURE_INFO_PATH = MODEL_DIR / "feature_info.json"
REGISTRY_PATH = MODELS_ROOT / "model_registry.json"


# ============================================================
# DATA CONTRACT
# ============================================================

TARGET = "sleep_disorder"

NUMERICAL_FEATURES = [
    "age",
    "sleep_hours",
    "sleep_quality",
    "physical_activity_level",
    "stress_level",
    "heart_rate",
    "daily_steps",
    "activity_sleep_balance",
    "lifestyle_risk_score",
]

CATEGORICAL_FEATURES = [
    "gender",
    "occupation",
    "bmi_category",
    "blood_pressure",
]

FINAL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

EXPECTED_CLASSES = [
    "Normal",
    "Insomnia",
    "Sleep Apnea",
]


# ============================================================
# HELPERS
# ============================================================

def make_one_hot_encoder() -> OneHotEncoder:
    """Support both newer and older sklearn versions."""
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


def make_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
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

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "onehot",
                make_one_hot_encoder(),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "num",
                numeric_pipeline,
                NUMERICAL_FEATURES,
            ),
            (
                "cat",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def get_models() -> dict:
    """
    Candidate models.

    Macro F1 is used for model selection because the three classes
    are imbalanced, especially the Insomnia class.
    """
    return {
        "LogisticRegression": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            random_state=42,
        ),
        "DecisionTreeClassifier": DecisionTreeClassifier(
            class_weight="balanced",
            random_state=42,
            min_samples_leaf=3,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42,
            min_samples_leaf=2,
        ),
        "ExtraTreesClassifier": ExtraTreesClassifier(
            n_estimators=300,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42,
            min_samples_leaf=2,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }


def build_pipeline(model) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocessor",
                make_preprocessor(),
            ),
            (
                "model",
                model,
            ),
        ]
    )


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove common markdown/escaped-name artifacts."""
    cleaned = df.copy()

    cleaned.columns = (
        cleaned.columns.astype(str)
        .str.replace(r"\*\*", "", regex=True)
        .str.replace(r"\\_", "_", regex=True)
        .str.strip()
    )

    for column in cleaned.select_dtypes(include="object").columns:
        cleaned[column] = (
            cleaned[column]
            .astype(str)
            .str.replace(r"\*\*", "", regex=True)
            .str.strip()
        )

    return cleaned


def validate_dataset(df: pd.DataFrame) -> None:
    required = FINAL_FEATURES + [TARGET]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(
            "Dataset is missing required columns:\n"
            + "\n".join(f"  - {column}" for column in missing)
        )

    if df.empty:
        raise ValueError("Dataset is empty.")

    if df[TARGET].isna().any():
        raise ValueError(
            f"Target column '{TARGET}' contains missing values."
        )

    # Normalize class spelling only where harmless.
    df[TARGET] = (
        df[TARGET]
        .astype(str)
        .str.strip()
        .replace(
            {
                "normal": "Normal",
                "NORMAL": "Normal",
                "insomnia": "Insomnia",
                "INSOMNIA": "Insomnia",
                "sleep apnea": "Sleep Apnea",
                "Sleep apnea": "Sleep Apnea",
                "SLEEP APNEA": "Sleep Apnea",
            }
        )
    )

    actual_classes = sorted(df[TARGET].unique().tolist())
    expected_classes = sorted(EXPECTED_CLASSES)

    if actual_classes != expected_classes:
        raise ValueError(
            "Target must contain exactly these 3 classes:\n"
            f"  {EXPECTED_CLASSES}\n"
            f"Found:\n"
            f"  {actual_classes}"
        )

    class_counts = df[TARGET].value_counts()

    if (class_counts < 5).any():
        raise ValueError(
            "Every class needs at least 5 samples for reliable "
            "stratified cross-validation.\n"
            f"Class counts:\n{class_counts.to_string()}"
        )


def get_feature_importances(pipeline: Pipeline) -> pd.DataFrame | None:
    """
    Extract model-level feature importance after preprocessing.

    For one-hot encoded categorical fields, importance is aggregated
    back to the original feature name so the report is easier to read.
    """
    try:
        preprocessor = pipeline.named_steps["preprocessor"]
        model = pipeline.named_steps["model"]

        if hasattr(model, "feature_importances_"):
            importances = np.asarray(model.feature_importances_)
        elif hasattr(model, "coef_"):
            coefficients = np.asarray(model.coef_)
            if coefficients.ndim > 1:
                importances = np.mean(
                    np.abs(coefficients),
                    axis=0,
                )
            else:
                importances = np.abs(coefficients)
        else:
            return None

        feature_names = []

        for transformer_name, transformer, columns in (
            preprocessor.transformers_
        ):
            if transformer_name == "num":
                feature_names.extend(list(columns))

            elif transformer_name == "cat":
                encoder = transformer.named_steps["onehot"]
                feature_names.extend(
                    encoder.get_feature_names_out(
                        columns
                    ).tolist()
                )

        if len(feature_names) != len(importances):
            return None

        raw = pd.DataFrame(
            {
                "encoded_feature": feature_names,
                "importance": importances,
            }
        )

        # Aggregate one-hot columns to the original input feature.
        def original_feature(name: str) -> str:
            for feature in CATEGORICAL_FEATURES:
                if name.startswith(feature + "_"):
                    return feature
            return name

        raw["feature"] = raw["encoded_feature"].apply(
            original_feature
        )

        result = (
            raw.groupby("feature", as_index=False)["importance"]
            .sum()
            .sort_values(
                "importance",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        total = result["importance"].sum()

        if total > 0:
            result["importance_percent"] = (
                result["importance"] / total * 100
            ).round(4)
        else:
            result["importance_percent"] = 0.0

        return result

    except Exception as exc:
        print(
            f"[WARN] Could not calculate feature importance: {exc}"
        )
        return None


def backup_existing_artifacts() -> Path | None:
    """
    Back up the currently deployed Lifestyle artifacts before replacing them.
    """
    existing = [
        MODEL_PATH,
        METADATA_PATH,
        FEATURE_INFO_PATH,
    ]

    existing = [path for path in existing if path.exists()]

    if not existing:
        print("No existing Lifestyle artifacts found. Nothing to back up.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir = (
        MODEL_DIR
        / "backup"
        / f"before_retrain_{timestamp}"
    )

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for path in existing:
        shutil.copy2(
            path,
            backup_dir / path.name,
        )

    print(f"Existing artifacts backed up to:\n  {backup_dir}")

    return backup_dir


def update_model_registry(
    model_name: str,
    test_f1: float,
) -> None:
    """
    Update only the Lifestyle entry while preserving other domains.
    """
    if REGISTRY_PATH.exists():
        try:
            with open(
                REGISTRY_PATH,
                "r",
                encoding="utf-8",
            ) as file:
                registry = json.load(file)
        except Exception:
            registry = {}
    else:
        registry = {}

    registry["lifestyle"] = {
        "model_path": str(MODEL_PATH),
        "model_name": model_name,
        "target": TARGET,
        "problem_type": "classification",
        "version": "2.0",
        "primary_metric": "macro_f1",
        "primary_metric_value": float(test_f1),
        "classes": EXPECTED_CLASSES,
    }

    REGISTRY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REGISTRY_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            registry,
            file,
            indent=4,
        )


# ============================================================
# MAIN TRAINING
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train and deploy the Lifestyle 3-class model."
    )

    parser.add_argument(
        "--data",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to lifestyle_clean.csv",
    )

    args = parser.parse_args()

    data_path = Path(args.data).expanduser().resolve()

    print("=" * 70)
    print("LIFESTYLE / SLEEP DISORDER MODEL TRAINING")
    print("=" * 70)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Dataset      : {data_path}")
    print(f"Model output : {MODEL_PATH}")

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{data_path}\n\n"
            "Put lifestyle_clean.csv in "
            "Datasets/prepared_datasets or use --data."
        )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------
    df = pd.read_csv(data_path)
    df = clean_columns(df)

    print("\nDataset shape:")
    print(f"  Rows    : {len(df):,}")
    print(f"  Columns : {len(df.columns)}")

    validate_dataset(df)

    # Work only with the intended contract.
    df = df[FINAL_FEATURES + [TARGET]].copy()

    X = df[FINAL_FEATURES].copy()
    y = df[TARGET].copy()

    print("\nTarget distribution:")
    print(y.value_counts().to_string())

    print("\nFeatures used:")
    for feature in FINAL_FEATURES:
        print(f"  - {feature}")

    # --------------------------------------------------------
    # Hold-out test set
    # --------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    print(
        f"\nSplit: train={len(X_train)} | "
        f"test={len(X_test)}"
    )

    # --------------------------------------------------------
    # Model comparison
    # --------------------------------------------------------
    models = get_models()

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    scoring = {
        "accuracy": "accuracy",
        "precision_macro": "precision_macro",
        "recall_macro": "recall_macro",
        "f1_macro": "f1_macro",
    }

    results = []

    print("\n" + "-" * 70)
    print("5-FOLD STRATIFIED CROSS-VALIDATION")
    print("-" * 70)

    for name, model in models.items():
        pipeline = build_pipeline(model)

        cv_result = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        result = {
            "Model": name,
            "CV Accuracy": float(
                np.mean(cv_result["test_accuracy"])
            ),
            "CV Precision Macro": float(
                np.mean(cv_result["test_precision_macro"])
            ),
            "CV Recall Macro": float(
                np.mean(cv_result["test_recall_macro"])
            ),
            "CV F1 Macro": float(
                np.mean(cv_result["test_f1_macro"])
            ),
        }

        results.append(result)

        print(
            f"{name:30s} "
            f"Accuracy={result['CV Accuracy']:.4f}  "
            f"Precision={result['CV Precision Macro']:.4f}  "
            f"Recall={result['CV Recall Macro']:.4f}  "
            f"F1={result['CV F1 Macro']:.4f}"
        )

    results_df = (
        pd.DataFrame(results)
        .sort_values(
            "CV F1 Macro",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    best_model_name = results_df.iloc[0]["Model"]

    print("\n" + "=" * 70)
    print(f"BEST MODEL: {best_model_name}")
    print(
        f"Best 5-fold Macro F1: "
        f"{results_df.iloc[0]['CV F1 Macro']:.4f}"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Test evaluation
    # --------------------------------------------------------
    best_pipeline = build_pipeline(
        models[best_model_name]
    )

    best_pipeline.fit(
        X_train,
        y_train,
    )

    y_pred = best_pipeline.predict(X_test)

    test_accuracy = accuracy_score(
        y_test,
        y_pred,
    )

    test_precision = precision_score(
        y_test,
        y_pred,
        average="macro",
        zero_division=0,
    )

    test_recall = recall_score(
        y_test,
        y_pred,
        average="macro",
        zero_division=0,
    )

    test_f1 = f1_score(
        y_test,
        y_pred,
        average="macro",
        zero_division=0,
    )

    print("\n" + "-" * 70)
    print("HELD-OUT TEST RESULTS")
    print("-" * 70)

    print(f"Accuracy       : {test_accuracy:.4f}")
    print(f"Macro Precision: {test_precision:.4f}")
    print(f"Macro Recall   : {test_recall:.4f}")
    print(f"Macro F1       : {test_f1:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=EXPECTED_CLASSES,
            zero_division=0,
        )
    )

    print("Confusion matrix:")
    print(
        pd.DataFrame(
            confusion_matrix(
                y_test,
                y_pred,
                labels=EXPECTED_CLASSES,
            ),
            index=EXPECTED_CLASSES,
            columns=EXPECTED_CLASSES,
        )
    )

    # --------------------------------------------------------
    # Retrain final pipeline on ALL data
    # --------------------------------------------------------
    print("\n" + "-" * 70)
    print("RETRAINING BEST MODEL ON FULL DATASET")
    print("-" * 70)

    final_pipeline = build_pipeline(
        models[best_model_name]
    )

    final_pipeline.fit(
        X,
        y,
    )

    # --------------------------------------------------------
    # Backup old artifacts BEFORE replacement
    # --------------------------------------------------------
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_dir = backup_existing_artifacts()

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------
    joblib.dump(
        final_pipeline,
        MODEL_PATH,
    )

    # Feature importance from final model.
    importance_df = get_feature_importances(
        final_pipeline
    )

    if importance_df is not None:
        importance_path = (
            REPORT_DIR
            / "lifestyle_feature_importance.csv"
        )
        importance_df.to_csv(
            importance_path,
            index=False,
        )
    else:
        importance_path = None

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------
    metadata = {
        "model_name": best_model_name,
        "problem_type": "classification",
        "target": TARGET,
        "classes": EXPECTED_CLASSES,
        "dataset": data_path.name,
        "version": "2.0",
        "training_date": datetime.now().isoformat(),
        "rows": int(len(df)),
        "features": FINAL_FEATURES,
        "metrics": {
            "cv_accuracy": float(
                results_df.iloc[0]["CV Accuracy"]
            ),
            "cv_precision_macro": float(
                results_df.iloc[0]["CV Precision Macro"]
            ),
            "cv_recall_macro": float(
                results_df.iloc[0]["CV Recall Macro"]
            ),
            "cv_f1_macro": float(
                results_df.iloc[0]["CV F1 Macro"]
            ),
            "test_accuracy": float(test_accuracy),
            "test_precision_macro": float(test_precision),
            "test_recall_macro": float(test_recall),
            "test_f1_macro": float(test_f1),
        },
        "labeling": {
            "type": "rule_based_reference_ranges",
            "note": (
                "sleep_disorder labels were generated from the supplied "
                "reference ranges for Normal, Insomnia and Sleep Apnea. "
                "They are project labels, not clinical diagnoses."
            ),
        },
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Feature info
    # --------------------------------------------------------
    feature_info = {
        "target": TARGET,
        "problem_type": "classification",
        "classes": EXPECTED_CLASSES,
        "final_features": FINAL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "removed_features": [],
        "split_strategy": "Stratified 80/20 hold-out test",
        "cross_validation": "5-fold StratifiedKFold",
        "primary_metric": "macro_f1",
        "model_selection": (
            "Best 5-fold CV macro F1 among candidate classifiers"
        ),
    }

    with open(
        FEATURE_INFO_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_info,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------
    comparison_path = (
        REPORT_DIR
        / "lifestyle_model_comparison.csv"
    )

    results_df.to_csv(
        comparison_path,
        index=False,
    )

    report_path = (
        REPORT_DIR
        / "lifestyle_training_report.md"
    )

    report = f"""# Lifestyle Model Training Report

## Model
- Best model: `{best_model_name}`
- Target: `{TARGET}`
- Classes: `Normal`, `Insomnia`, `Sleep Apnea`
- Dataset: `{data_path.name}`
- Rows: `{len(df)}`
- Version: `2.0`

## Validation
- Split: stratified 80/20 hold-out
- Cross-validation: 5-fold StratifiedKFold
- Primary model-selection metric: Macro F1

## Cross-validation
- Accuracy: {results_df.iloc[0]['CV Accuracy']:.4f}
- Precision Macro: {results_df.iloc[0]['CV Precision Macro']:.4f}
- Recall Macro: {results_df.iloc[0]['CV Recall Macro']:.4f}
- F1 Macro: {results_df.iloc[0]['CV F1 Macro']:.4f}

## Held-out Test
- Accuracy: {test_accuracy:.4f}
- Precision Macro: {test_precision:.4f}
- Recall Macro: {test_recall:.4f}
- F1 Macro: {test_f1:.4f}

## Classes
{y.value_counts().to_string()}

## Features
{chr(10).join('- ' + feature for feature in FINAL_FEATURES)}

## Deployment
- Model: `{MODEL_PATH}`
- Metadata: `{METADATA_PATH}`
- Feature info: `{FEATURE_INFO_PATH}`
- Registry: `{REGISTRY_PATH}`

## Important
The target labels were generated from the project's supplied reference
ranges for Normal, Insomnia and Sleep Apnea. They are not clinical diagnoses.
"""

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(report)

    # --------------------------------------------------------
    # Update model registry
    # --------------------------------------------------------
    update_model_registry(
        model_name=best_model_name,
        test_f1=test_f1,
    )

    # --------------------------------------------------------
    # Smoke test the saved model
    # --------------------------------------------------------
    print("\n" + "-" * 70)
    print("SAVED MODEL SMOKE TEST")
    print("-" * 70)

    loaded_model = joblib.load(MODEL_PATH)

    smoke_inputs = pd.DataFrame(
        [
            {
                "gender": "Female",
                "age": 30,
                "occupation": "Software Engineer",
                "sleep_hours": 7.5,
                "sleep_quality": 8,
                "physical_activity_level": 75,
                "stress_level": 4,
                "bmi_category": "Normal",
                "blood_pressure": "120/80",
                "heart_rate": 70,
                "daily_steps": 8000,
                "activity_sleep_balance": 85,
                "lifestyle_risk_score": 20,
            },
            {
                "gender": "Female",
                "age": 30,
                "occupation": "Software Engineer",
                "sleep_hours": 5.8,
                "sleep_quality": 4,
                "physical_activity_level": 40,
                "stress_level": 8,
                "bmi_category": "Normal",
                "blood_pressure": "122/80",
                "heart_rate": 74,
                "daily_steps": 4500,
                "activity_sleep_balance": 35,
                "lifestyle_risk_score": 70,
            },
            {
                "gender": "Male",
                "age": 48,
                "occupation": "Manager",
                "sleep_hours": 6.8,
                "sleep_quality": 5,
                "physical_activity_level": 45,
                "stress_level": 6,
                "bmi_category": "Overweight",
                "blood_pressure": "138/88",
                "heart_rate": 80,
                "daily_steps": 5000,
                "activity_sleep_balance": 45,
                "lifestyle_risk_score": 75,
            },
        ]
    )

    smoke_predictions = loaded_model.predict(
        smoke_inputs[FINAL_FEATURES]
    )

    for index, prediction in enumerate(
        smoke_predictions,
        start=1,
    ):
        print(
            f"Smoke test {index}: {prediction}"
        )

    if not set(smoke_predictions).issubset(
        set(EXPECTED_CLASSES)
    ):
        raise RuntimeError(
            "Smoke test produced an unexpected class."
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("LIFESTYLE MODEL DEPLOYMENT COMPLETE")
    print("=" * 70)

    print(f"Model       : {MODEL_PATH}")
    print(f"Metadata    : {METADATA_PATH}")
    print(f"Features    : {FEATURE_INFO_PATH}")
    print(f"Registry    : {REGISTRY_PATH}")
    print(f"Comparison  : {comparison_path}")
    print(f"Report      : {report_path}")

    if importance_path is not None:
        print(f"Importance  : {importance_path}")

    if backup_dir is not None:
        print(f"Backup      : {backup_dir}")

    print("\nTarget classes:")
    for class_name in EXPECTED_CLASSES:
        print(f"  - {class_name}")

    print(
        f"\nHeld-out Macro F1: {test_f1:.4f}"
    )

    print(
        "\nThe saved model is now a 3-class classifier and "
        "is ready for the existing Lifestyle ML API."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            "\n[ERROR] Lifestyle model training failed:"
        )
        print(exc)
        sys.exit(1)
