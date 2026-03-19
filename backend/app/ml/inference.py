"""
ML Inference Module
====================
Loads the trained model and provides prediction + explainability.

Key functions:
  - predict_default_probability(features) → (probability, confidence, contributions)
  - get_feature_importance() → dict of global feature importance
  - get_model_info() → model type, version, metrics

The module is designed for hot-loading: the model is loaded once at
import time and cached. Call reload_model() to pick up a newly trained model.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "default_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

FEATURE_NAMES = [
    "loan_reliability",
    "income",
    "income_stability",
    "graph_reputation",
    "currency_risk",
    "platform_quality",
    "wallet_age",
    "transaction_diversity",
    "growth_trend",
    "account_behavior",
]

_cached_model = None
_cached_metadata = None


@dataclass
class MLPrediction:
    default_probability: float
    confidence: float
    feature_contributions: dict[str, float] = field(default_factory=dict)
    model_type: str = "none"
    model_version: str = "v3-hybrid"


def _load_model():
    global _cached_model
    if not MODEL_PATH.exists():
        return None
    import joblib
    _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def _load_metadata() -> dict | None:
    global _cached_metadata
    if not METADATA_PATH.exists():
        return None
    with open(METADATA_PATH) as f:
        _cached_metadata = json.load(f)
    return _cached_metadata


def _get_model():
    global _cached_model
    if _cached_model is None:
        _load_model()
    return _cached_model


def _get_metadata():
    global _cached_metadata
    if _cached_metadata is None:
        _load_metadata()
    return _cached_metadata


def reload_model() -> bool:
    """Force-reload the model from disk. Returns True if successful."""
    global _cached_model, _cached_metadata
    _cached_model = None
    _cached_metadata = None
    return _load_model() is not None


def is_model_available() -> bool:
    return MODEL_PATH.exists()


def predict_default_probability(features: dict[str, float]) -> MLPrediction:
    """
    Predict the probability that a user will default.

    Args:
        features: dict with the 10 feature values (0-1 normalized)

    Returns:
        MLPrediction with probability, confidence, and per-feature contributions
    """
    model_data = _get_model()

    if model_data is None:
        return _heuristic_fallback(features)

    model = model_data["model"]
    scaler = model_data.get("scaler")
    model_type = model_data.get("model_type", "unknown")

    feature_vec = np.array([[features.get(f, 0.0) for f in FEATURE_NAMES]])

    if scaler is not None:
        feature_vec_scaled = scaler.transform(feature_vec)
    else:
        feature_vec_scaled = feature_vec

    prob = model.predict_proba(feature_vec_scaled)[0]
    default_prob = float(prob[1])
    confidence = float(abs(default_prob - 0.5) * 2)  # 0 at 50/50, 1 at extremes

    contributions = _compute_contributions(
        model, model_type, features, feature_vec, feature_vec_scaled
    )

    return MLPrediction(
        default_probability=round(default_prob, 4),
        confidence=round(confidence, 4),
        feature_contributions=contributions,
        model_type=model_type,
        model_version=_get_metadata().get("model_version", "v3-hybrid") if _get_metadata() else "v3-hybrid",
    )


def _compute_contributions(
    model, model_type: str, features: dict[str, float],
    feature_vec: np.ndarray, feature_vec_scaled: np.ndarray
) -> dict[str, float]:
    """
    Compute per-feature contributions to the default prediction.

    For Logistic Regression: coefficient × feature value (signed)
    For XGBoost: feature_importances_ × feature value (unsigned, then signed by coef direction)
    """
    contributions = {}

    if model_type == "logistic_regression":
        coefficients = model.coef_[0]
        for i, name in enumerate(FEATURE_NAMES):
            raw_contribution = float(coefficients[i] * feature_vec_scaled[0][i])
            contributions[name] = round(raw_contribution, 4)

    elif model_type == "xgboost":
        importances = model.feature_importances_
        for i, name in enumerate(FEATURE_NAMES):
            value = features.get(name, 0.0)
            signed = -importances[i] * value  # negative = reduces default risk
            contributions[name] = round(float(signed), 4)

    else:
        for name in FEATURE_NAMES:
            contributions[name] = 0.0

    return contributions


def _heuristic_fallback(features: dict[str, float]) -> MLPrediction:
    """
    When no ML model is available, estimate default probability from
    a simple heuristic based on the feature values.
    """
    weights = {
        "loan_reliability": -0.30,
        "income": -0.15,
        "income_stability": -0.10,
        "graph_reputation": -0.10,
        "currency_risk": -0.05,
        "platform_quality": -0.10,
        "wallet_age": -0.05,
        "transaction_diversity": -0.05,
        "growth_trend": -0.05,
        "account_behavior": -0.05,
    }
    logit = 1.5  # base default rate
    contributions = {}
    for name, w in weights.items():
        val = features.get(name, 0.5)
        contrib = w * val
        logit += contrib
        contributions[name] = round(contrib, 4)

    prob = 1.0 / (1.0 + np.exp(-logit))
    confidence = float(abs(prob - 0.5) * 2)

    return MLPrediction(
        default_probability=round(float(prob), 4),
        confidence=round(confidence, 4),
        feature_contributions=contributions,
        model_type="heuristic_fallback",
        model_version="v3-hybrid",
    )


def get_feature_importance() -> dict[str, float]:
    """Return global feature importance from the trained model metadata."""
    metadata = _get_metadata()
    if metadata and "feature_importance" in metadata:
        return metadata["feature_importance"]
    return {f: 0.0 for f in FEATURE_NAMES}


def get_model_info() -> dict:
    """Return model metadata (type, version, metrics, etc.)."""
    metadata = _get_metadata()
    if metadata:
        return {
            "model_type": metadata.get("model_type"),
            "model_version": metadata.get("model_version"),
            "metrics": metadata.get("metrics"),
            "training_samples": metadata.get("training_samples"),
            "default_rate": metadata.get("default_rate"),
            "is_loaded": _cached_model is not None,
        }
    return {
        "model_type": "none",
        "model_version": "v3-hybrid",
        "metrics": None,
        "is_loaded": False,
    }
