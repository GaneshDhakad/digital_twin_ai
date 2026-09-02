"""
model_loader.py
Shared model loader for all ML models.

Resolves model artifacts from ML_MODELS_DIR (env var) with automatic
fallback to ml_models/trained/<domain>/ if not found at the primary path.

Models are cached in-memory after first load to avoid repeated disk I/O.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)

# ── Resolve project root (digital_twin_ai/) ──────────────────────────────────
# This file lives at: backend/app/services/ml/model_loader.py
# So parents[4] = digital_twin_ai/
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[4]  # digital_twin_ai/

# ── Primary model directory from env, defaults to ml_models/ ─────────────────
_ML_MODELS_DIR_ENV = os.getenv("ML_MODELS_DIR", "")
if _ML_MODELS_DIR_ENV:
    ML_MODELS_DIR = Path(_ML_MODELS_DIR_ENV).resolve()
else:
    ML_MODELS_DIR = _PROJECT_ROOT / "ml_models"

# Fallback locations searched in order
_SEARCH_PATHS: list[Path] = [
    ML_MODELS_DIR,                          # ml_models/<domain>/
    ML_MODELS_DIR / "trained",              # ml_models/trained/<domain>/
    _PROJECT_ROOT / "backend" / "app" / "ml_models",  # backend/app/ml_models/<domain>/
]

SUPPORTED_DOMAINS = {"academic", "lifestyle", "financial", "forecasting"}

# ── In-memory cache ───────────────────────────────────────────────────────────
_pipeline_cache: Dict[str, Any] = {}
_metadata_cache: Dict[str, Dict] = {}
_feature_info_cache: Dict[str, Dict] = {}


def _find_domain_folder(domain: str) -> Optional[Path]:
    """Search all candidate paths for a domain model folder."""
    for base in _SEARCH_PATHS:
        candidate = base / domain
        if (candidate / "model.joblib").exists():
            return candidate
    return None


def get_model_dir(domain: str) -> Path:
    """Return the resolved directory for a domain; raises if missing."""
    folder = _find_domain_folder(domain)
    if folder is None:
        searched = [str(p / domain) for p in _SEARCH_PATHS]
        raise FileNotFoundError(
            f"Model artifact for '{domain}' not found. Searched:\n"
            + "\n".join(f"  {p}" for p in searched)
        )
    return folder


def load_pipeline(domain: str) -> Any:
    """Load and cache the sklearn pipeline for a domain."""
    if domain in _pipeline_cache:
        return _pipeline_cache[domain]

    folder = get_model_dir(domain)
    model_path = folder / "model.joblib"

    logger.info("Loading %s model from %s", domain, model_path)
    try:
        pipeline = joblib.load(model_path)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load {domain} model from {model_path}: {exc}"
        ) from exc

    _pipeline_cache[domain] = pipeline
    logger.info("%s model loaded and cached.", domain)
    return pipeline


def load_metadata(domain: str) -> Dict:
    """Load and cache metadata.json for a domain."""
    if domain in _metadata_cache:
        return _metadata_cache[domain]

    folder = get_model_dir(domain)
    meta_path = folder / "metadata.json"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    _metadata_cache[domain] = meta
    return meta


def load_feature_info(domain: str) -> Dict:
    """Load and cache feature_info.json for a domain."""
    if domain in _feature_info_cache:
        return _feature_info_cache[domain]

    folder = get_model_dir(domain)
    fi_path = folder / "feature_info.json"

    with open(fi_path, "r", encoding="utf-8") as f:
        fi = json.load(f)

    _feature_info_cache[domain] = fi
    return fi


def is_model_available(domain: str) -> bool:
    """Return True if the model artifact exists and is loadable."""
    try:
        _find_domain_folder(domain)
        return _find_domain_folder(domain) is not None
    except Exception:
        return False


def get_model_status() -> Dict[str, Any]:
    """
    Return a health-check dict for all supported domains + fitness (excluded).
    Does NOT expose filesystem paths.
    """
    status: Dict[str, Any] = {}
    for domain in SUPPORTED_DOMAINS:
        try:
            meta = load_metadata(domain)
            status[domain] = {
                "available": True,
                "model": meta.get("model_name", "unknown"),
                "version": meta.get("version", "1.0"),
                "target": meta.get("target", "unknown"),
                "problem_type": meta.get("problem_type", "unknown"),
            }
        except Exception as exc:
            logger.warning("Model status check failed for %s: %s", domain, exc)
            status[domain] = {"available": False, "error": "Model not available"}

    # Fitness is explicitly excluded from this phase
    status["fitness"] = {"available": False, "note": "Not integrated in this phase"}
    return status
