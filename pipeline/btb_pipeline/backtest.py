"""Forecast backtest + calibration [N9a]: score predicted win probabilities vs outcomes.

The forecast unit's GATE depends on this module. The race model [race_model.py] emits a Dem
win_prob per race [N2a]; on a holdout of known outcomes (e.g. the 2018/2022 cycles) we score
those probabilities against what actually happened. Two kinds of question are answered [N9a]:

- SKILL: were the predictions accurate? brier_score and log_loss are strictly-proper scoring
  rules — lower is better, and they reward honest, sharp probabilities, not just the right call.
- CALIBRATION: when the model says 70%, do Democrats really win about 70% of those races?
  calibration_bins groups predictions into probability buckets (the data for a reliability
  diagram), and calibration_error (Expected Calibration Error) summarizes the gap as one number.

is_calibrated() is the gate helper: the forecast unit calls it to BLOCK shipping an
uncalibrated model [N9a]. Pure-math, keyless, no network, no accounts. The scalar summary is
validated into a pydantic model before reporting [R7a], and matches the published methodology
[N12a] (every metric here is explainable and standard, not a fitted black box).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict


def _as_prob_actual(preds: list[dict]) -> list[tuple[float, float]]:
    """Normalize preds into (pred_prob, actual) float pairs; raise ValueError on empty [R7a]."""
    if not preds:
        raise ValueError("preds must contain at least one prediction")
    out: list[tuple[float, float]] = []
    for p in preds:
        prob = float(p["pred_prob"])
        actual = float(p["actual_dem_win"])
        out.append((prob, actual))
    return out


def brier_score(preds: list[dict]) -> float:
    """Mean squared error of predicted probabilities: mean((pred_prob - actual)**2) [N9a].

    Lower is better; 0 is perfect (probability 1.0 on every race that happened). A constant
    0.5 forecast scores 0.25. Raises ValueError on empty preds.
    """
    pairs = _as_prob_actual(preds)
    total = sum((prob - actual) ** 2 for prob, actual in pairs)
    return round(total / len(pairs), 4)


def log_loss(preds: list[dict], eps: float = 1e-15) -> float:
    """Mean negative log-likelihood: -mean(a*log(p) + (1-a)*log(1-p)), p clipped to [eps,1-eps].

    Lower is better; a perfect confident forecast approaches 0. A constant 0.5 forecast scores
    -log(0.5) ~= 0.6931. Clipping keeps a confident-but-wrong prediction finite. Raises
    ValueError on empty preds.
    """
    pairs = _as_prob_actual(preds)
    total = 0.0
    for prob, actual in pairs:
        p = min(max(prob, eps), 1.0 - eps)
        total += actual * math.log(p) + (1.0 - actual) * math.log(1.0 - p)
    return round(-total / len(pairs), 4)


def calibration_bins(preds: list[dict], n_bins: int = 10) -> list[dict]:
    """Bin predictions into n_bins equal-width buckets over [0, 1] for a reliability diagram [N9a].

    Each bin dict has bin_lo, bin_hi, n (count), mean_pred (mean predicted prob in the bin, or
    None if empty), and frac_actual (observed Dem-win fraction in the bin, or None if empty). A
    pred_prob of exactly 1.0 falls in the top bin. Raises ValueError on empty preds or n_bins<1.
    """
    pairs = _as_prob_actual(preds)
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1")
    width = 1.0 / n_bins
    buckets: list[dict] = [{"sum_pred": 0.0, "sum_actual": 0.0, "n": 0} for _ in range(n_bins)]
    for prob, actual in pairs:
        idx = int(prob / width)
        if idx >= n_bins:  # pred_prob == 1.0 (or rounding) -> top bin
            idx = n_bins - 1
        if idx < 0:
            idx = 0
        b = buckets[idx]
        b["sum_pred"] += prob
        b["sum_actual"] += actual
        b["n"] += 1

    out: list[dict] = []
    for i, b in enumerate(buckets):
        n = b["n"]
        mean_pred = round(b["sum_pred"] / n, 4) if n else None
        frac_actual = round(b["sum_actual"] / n, 4) if n else None
        out.append(
            {
                "bin_lo": round(i * width, 4),
                "bin_hi": round((i + 1) * width, 4),
                "n": n,
                "mean_pred": mean_pred,
                "frac_actual": frac_actual,
            }
        )
    return out


def calibration_error(preds: list[dict], n_bins: int = 10) -> float:
    """Expected Calibration Error [N9a]: sum over nonempty bins of (n_bin/N)*|mean_pred-frac_actual|.

    A weighted average of the gap between predicted probability and observed frequency across
    bins. Lower is better; 0 means perfectly calibrated. Raises ValueError on empty preds.
    """
    pairs = _as_prob_actual(preds)
    n_total = len(pairs)
    ece = 0.0
    for b in calibration_bins(preds, n_bins):
        if b["n"]:
            ece += (b["n"] / n_total) * abs(b["mean_pred"] - b["frac_actual"])
    return round(ece, 4)


def accuracy(preds: list[dict], threshold: float = 0.5) -> float:
    """Fraction of races where (pred_prob >= threshold) matches actual_dem_win [N9a].

    The plain hit rate of the implied call. Less informative than brier/log_loss (it ignores
    confidence) but easy to read. Raises ValueError on empty preds.
    """
    pairs = _as_prob_actual(preds)
    hits = sum(1 for prob, actual in pairs if (prob >= threshold) == bool(actual))
    return round(hits / len(pairs), 4)


class BacktestReport(BaseModel):
    """Scalar backtest summary [N9a]: skill + calibration metrics. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    n: int
    brier: float
    log_loss: float
    ece: float
    accuracy: float


def run_backtest(preds: list[dict]) -> dict:
    """Assemble the full backtest result [N9a,R7a]: scalar report plus reliability-diagram bins.

    Returns BacktestReport.model_dump() (n, brier, log_loss, ece, accuracy — all 4dp) PLUS a
    "calibration" key holding calibration_bins(preds), the per-bin data a reliability diagram is
    drawn from. Raises ValueError on empty preds.
    """
    if not preds:
        raise ValueError("run_backtest requires at least one prediction")
    report = BacktestReport(
        n=len(preds),
        brier=brier_score(preds),
        log_loss=log_loss(preds),
        ece=calibration_error(preds),
        accuracy=accuracy(preds),
    ).model_dump()
    report["calibration"] = calibration_bins(preds)
    return report


def is_calibrated(report: dict, max_ece: float = 0.1, max_brier: float = 0.25) -> bool:
    """Gate helper [N9a]: True iff the forecast is well-calibrated AND has enough skill.

    The forecast unit's gate calls this to BLOCK shipping an uncalibrated model: a forecast
    passes only when ece <= max_ece (its stated probabilities match observed frequencies) AND
    brier <= max_brier (it is no worse than a naive 0.5-everywhere baseline). Takes a report
    dict as produced by run_backtest (or any dict with "ece" and "brier" keys).
    """
    return report["ece"] <= max_ece and report["brier"] <= max_brier
