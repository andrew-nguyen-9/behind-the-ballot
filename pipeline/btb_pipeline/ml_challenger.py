"""ML challenger for the forecast [N8a]: a documented logistic-regression model on
fundamentals features, scored against the heuristic and ADOPTED ONLY IF IT BEATS IT.

ponytail: hand-rolled logistic regression (numpy gradient descent) — no sklearn dep for
one small model; it's ~30 lines and fully testable. Swap for sklearn/GBM only if model
complexity actually grows. The decision rule (`choose_model`) is the whole point: the ML
model must lower Brier vs the heuristic on the SAME holdout or we keep the heuristic.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict

from btb_pipeline.backtest import brier_score


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -50, 50)))


class LogisticModel(BaseModel):
    """Fitted weights for a logistic model on standardized features."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    weights: list[float]
    bias: float
    mean: list[float]
    std: list[float]


def fit_logistic(
    X: list[list[float]], y: list[int], lr: float = 0.1, epochs: int = 2000, seed: int = 0
) -> LogisticModel:
    """Fit logistic regression by gradient descent on standardized features [N8a]."""
    Xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    if Xa.ndim != 2 or Xa.shape[0] == 0:
        raise ValueError("X must be a non-empty 2D feature matrix")
    if Xa.shape[0] != ya.shape[0]:
        raise ValueError("X and y length mismatch")

    mean = Xa.mean(axis=0)
    std = Xa.std(axis=0)
    std[std == 0] = 1.0  # avoid div-by-zero on constant features
    Xs = (Xa - mean) / std

    rng = np.random.default_rng(seed)
    w = rng.normal(0, 0.01, Xs.shape[1])
    b = 0.0
    n = Xs.shape[0]
    for _ in range(epochs):
        p = _sigmoid(Xs @ w + b)
        err = p - ya
        w -= lr * (Xs.T @ err) / n
        b -= lr * err.mean()

    return LogisticModel(
        weights=w.tolist(), bias=float(b), mean=mean.tolist(), std=std.tolist()
    )


def predict_proba(model: LogisticModel, X: list[list[float]]) -> list[float]:
    """Dem win probabilities from a fitted model."""
    Xa = np.asarray(X, dtype=float)
    mean = np.asarray(model.mean)
    std = np.asarray(model.std)
    Xs = (Xa - mean) / std
    z = Xs @ np.asarray(model.weights) + model.bias
    return _sigmoid(z).tolist()


def choose_model(heuristic_probs: list[float], ml_probs: list[float], actual: list[int]) -> dict:
    """Compare both on the SAME holdout by Brier; keep ML only if it's strictly better
    [N8a]. Returns the decision + both scores (4dp)."""
    if not actual:
        raise ValueError("empty holdout")
    h = brier_score([{"pred_prob": p, "actual_dem_win": a} for p, a in zip(heuristic_probs, actual)])
    m = brier_score([{"pred_prob": p, "actual_dem_win": a} for p, a in zip(ml_probs, actual)])
    use_ml = m < h
    return {
        "heuristic_brier": round(h, 4),
        "ml_brier": round(m, 4),
        "chosen": "ml" if use_ml else "heuristic",
    }
