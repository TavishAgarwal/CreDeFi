"""
Synthetic Dataset Generator
=============================
Generates realistic user profiles with the 10 trust score features
and a binary default/non-default label.

Default probability is driven by a ground-truth logistic function of the
features, with noise added to prevent the ML model from simply
memorizing the heuristic. The correlations encode domain knowledge:
  - Low loan_reliability → high default risk
  - Low income / unverified → higher default risk
  - Sybil-like profiles (low account_behavior) → higher default
  - High graph_reputation → protective factor

Usage:
    python -m app.ml.dataset_generator --n 5000 --output data/training_data.csv
"""

from __future__ import annotations

import argparse
import math
import os

import numpy as np
import pandas as pd

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

# Ground-truth coefficients: negative = increases default probability
GT_COEFFICIENTS = {
    "loan_reliability":      -3.5,
    "income":                -2.0,
    "income_stability":      -1.5,
    "graph_reputation":      -1.8,
    "currency_risk":         -0.8,
    "platform_quality":      -1.2,
    "wallet_age":            -1.0,
    "transaction_diversity": -0.6,
    "growth_trend":          -0.9,
    "account_behavior":      -1.4,
}
GT_INTERCEPT = 2.5  # baseline logit (positive = biased toward default)


def _generate_correlated_features(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate n user profiles with realistic inter-feature correlations.
    Users fall into archetypes: reliable, risky, new, sybil-like, established.
    """
    features = np.zeros((n, len(FEATURE_NAMES)))

    for i in range(n):
        archetype = rng.choice(
            ["reliable", "risky", "new", "sybil", "established"],
            p=[0.30, 0.20, 0.25, 0.10, 0.15],
        )

        if archetype == "reliable":
            base = rng.uniform(0.65, 0.95, size=len(FEATURE_NAMES))
            base[0] = rng.uniform(0.75, 1.0)   # high loan_reliability
            base[1] = rng.uniform(0.5, 0.9)    # decent income
            base[4] = rng.uniform(0.7, 1.0)    # stable currency
            base[9] = rng.uniform(0.6, 1.0)    # good account behavior

        elif archetype == "risky":
            base = rng.uniform(0.1, 0.5, size=len(FEATURE_NAMES))
            base[0] = rng.uniform(0.0, 0.35)   # low loan_reliability
            base[1] = rng.uniform(0.05, 0.35)  # low income
            base[2] = rng.uniform(0.1, 0.4)    # unstable income
            base[8] = rng.uniform(0.2, 0.5)    # negative growth

        elif archetype == "new":
            base = rng.uniform(0.3, 0.6, size=len(FEATURE_NAMES))
            base[0] = 0.5                       # neutral (no history)
            base[6] = rng.uniform(0.0, 0.2)    # young wallet
            base[7] = rng.uniform(0.0, 0.3)    # few transactions
            base[8] = 0.5                       # neutral growth

        elif archetype == "sybil":
            base = rng.uniform(0.3, 0.7, size=len(FEATURE_NAMES))
            base[3] = rng.uniform(0.0, 0.15)   # no graph reputation
            base[5] = rng.uniform(0.0, 0.2)    # low platform quality
            base[9] = rng.uniform(0.0, 0.2)    # bad account behavior
            base[7] = rng.uniform(0.0, 0.15)   # no tx diversity

        else:  # established
            base = rng.uniform(0.5, 0.85, size=len(FEATURE_NAMES))
            base[0] = rng.uniform(0.6, 0.9)    # decent reliability
            base[3] = rng.uniform(0.5, 0.9)    # good graph
            base[6] = rng.uniform(0.6, 1.0)    # old wallet
            base[9] = rng.uniform(0.5, 0.9)    # established accounts

        noise = rng.normal(0, 0.05, size=len(FEATURE_NAMES))
        features[i] = np.clip(base + noise, 0.0, 1.0)

    return features


def _compute_default_labels(
    features: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """
    Compute binary default labels using a logistic ground-truth model.
    P(default) = sigmoid(intercept + coefficients · features + noise)
    """
    coef_vec = np.array([GT_COEFFICIENTS[f] for f in FEATURE_NAMES])
    logits = GT_INTERCEPT + features @ coef_vec
    noise = rng.normal(0, 0.4, size=len(logits))
    logits += noise
    probs = 1.0 / (1.0 + np.exp(-logits))
    labels = (rng.random(len(probs)) < probs).astype(int)
    return labels


def generate_dataset(
    n: int = 5000, seed: int = 42
) -> pd.DataFrame:
    """Generate a complete training dataset with features and labels."""
    rng = np.random.default_rng(seed)
    features = _generate_correlated_features(n, rng)
    labels = _compute_default_labels(features, rng)

    df = pd.DataFrame(features, columns=FEATURE_NAMES)
    df["defaulted"] = labels
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument("--n", type=int, default=5000, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/training_data.csv")
    args = parser.parse_args()

    df = generate_dataset(n=args.n, seed=args.seed)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Generated {len(df)} samples -> {args.output}")
    print(f"Default rate: {df['defaulted'].mean():.1%}")
    print(f"Feature stats:\n{df[FEATURE_NAMES].describe().round(3)}")


if __name__ == "__main__":
    main()
