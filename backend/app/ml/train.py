"""
Model Training Script
=======================
Trains both Logistic Regression and XGBoost on the synthetic dataset,
evaluates both, saves the best model along with metadata.

Outputs:
  - app/ml/models/default_model.joblib       (trained model)
  - app/ml/models/model_metadata.json        (metrics, feature names, version)

Usage:
    python -m app.ml.train [--data data/training_data.csv] [--generate]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

from app.ml.dataset_generator import FEATURE_NAMES, generate_dataset

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "default_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


def _try_import_xgboost():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier
    except ImportError:
        return None


def train_logistic_regression(X_train, y_train, X_test, y_test):
    """Train Logistic Regression with L2 regularization."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = model.predict(X_test_scaled)

    metrics = _compute_metrics(y_test, y_pred, y_prob)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring="roc_auc")
    metrics["cv_auc_mean"] = float(np.mean(cv_scores))
    metrics["cv_auc_std"] = float(np.std(cv_scores))

    coefficients = dict(zip(FEATURE_NAMES, model.coef_[0].tolist()))

    return model, scaler, metrics, coefficients


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost gradient-boosted classifier."""
    XGBClassifier = _try_import_xgboost()
    if XGBClassifier is None:
        return None, None, None, None

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1.0,
        eval_metric="logloss",
        random_state=42,
        use_label_encoder=False,
    )
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    metrics = _compute_metrics(y_test, y_pred, y_prob)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    metrics["cv_auc_mean"] = float(np.mean(cv_scores))
    metrics["cv_auc_std"] = float(np.std(cv_scores))

    importances = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))

    return model, None, metrics, importances


def _compute_metrics(y_true, y_pred, y_prob) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc_roc": float(roc_auc_score(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob)),
    }


def train_and_save(data_path: str | None = None, generate: bool = False) -> dict:
    """Full training pipeline: load data → train models → save best."""
    if generate or data_path is None or not os.path.exists(data_path):
        print("Generating synthetic dataset...")
        df = generate_dataset(n=5000, seed=42)
        if data_path:
            os.makedirs(os.path.dirname(data_path) or ".", exist_ok=True)
            df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)

    X = df[FEATURE_NAMES].values
    y = df["defaulted"].values

    split_idx = int(len(df) * 0.8)
    indices = np.random.RandomState(42).permutation(len(df))
    train_idx, test_idx = indices[:split_idx], indices[split_idx:]
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    print(f"Dataset: {len(df)} samples, {y.mean():.1%} default rate")
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Train Logistic Regression
    print("\n--- Logistic Regression ---")
    lr_model, lr_scaler, lr_metrics, lr_coefs = train_logistic_regression(
        X_train, y_train, X_test, y_test
    )
    print(f"  AUC-ROC: {lr_metrics['auc_roc']:.4f}")
    print(f"  CV AUC:  {lr_metrics['cv_auc_mean']:.4f} ± {lr_metrics['cv_auc_std']:.4f}")
    print(f"  F1:      {lr_metrics['f1']:.4f}")

    # Train XGBoost
    xgb_model, xgb_scaler, xgb_metrics, xgb_importances = train_xgboost(
        X_train, y_train, X_test, y_test
    )

    best_name = "logistic_regression"
    best_model = lr_model
    best_scaler = lr_scaler
    best_metrics = lr_metrics
    best_feature_importance = lr_coefs

    if xgb_model is not None:
        print("\n--- XGBoost ---")
        print(f"  AUC-ROC: {xgb_metrics['auc_roc']:.4f}")
        print(f"  CV AUC:  {xgb_metrics['cv_auc_mean']:.4f} ± {xgb_metrics['cv_auc_std']:.4f}")
        print(f"  F1:      {xgb_metrics['f1']:.4f}")

        if xgb_metrics["auc_roc"] > lr_metrics["auc_roc"]:
            best_name = "xgboost"
            best_model = xgb_model
            best_scaler = xgb_scaler
            best_metrics = xgb_metrics
            best_feature_importance = xgb_importances

    print(f"\nBest model: {best_name} (AUC={best_metrics['auc_roc']:.4f})")

    # Save model
    import joblib
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    save_data = {
        "model": best_model,
        "scaler": best_scaler,
        "model_type": best_name,
        "feature_names": FEATURE_NAMES,
    }
    joblib.dump(save_data, MODEL_PATH)
    print(f"  Model saved: {MODEL_PATH}")

    # Save metadata
    metadata = {
        "model_type": best_name,
        "model_version": "v3-hybrid",
        "feature_names": FEATURE_NAMES,
        "feature_importance": best_feature_importance,
        "metrics": best_metrics,
        "training_samples": len(df),
        "default_rate": float(y.mean()),
    }
    if xgb_metrics:
        metadata["alternative_model"] = {
            "name": "xgboost" if best_name == "logistic_regression" else "logistic_regression",
            "metrics": xgb_metrics if best_name == "logistic_regression" else lr_metrics,
        }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved: {METADATA_PATH}")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train default prediction model")
    parser.add_argument("--data", type=str, default="data/training_data.csv")
    parser.add_argument("--generate", action="store_true", help="Generate fresh data")
    args = parser.parse_args()
    train_and_save(data_path=args.data, generate=args.generate)


if __name__ == "__main__":
    main()
