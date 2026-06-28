import math

import pytest

from btb_pipeline.backtest import (
    accuracy,
    brier_score,
    calibration_bins,
    calibration_error,
    is_calibrated,
    log_loss,
    run_backtest,
)


def _pred(prob, actual, race_id="r"):
    return {"race_id": race_id, "pred_prob": prob, "actual_dem_win": actual}


def test_brier_perfect_confident_is_zero():
    # p=1.0 on a Dem win and p=0.0 on a Dem loss -> (1-1)^2 + (0-0)^2 = 0 -> mean 0.0.
    preds = [_pred(1.0, 1), _pred(0.0, 0)]
    assert brier_score(preds) == 0.0


def test_brier_coinflip_is_quarter():
    # p=0.5 on every race: (0.5-1)^2 = 0.25 and (0.5-0)^2 = 0.25 -> mean (0.25+0.25)/2 = 0.25.
    preds = [_pred(0.5, 1), _pred(0.5, 0)]
    assert brier_score(preds) == 0.25


def test_log_loss_perfect_confident_near_zero():
    # p clipped to [eps, 1-eps]; a perfect confident forecast scores essentially 0.
    preds = [_pred(1.0, 1), _pred(0.0, 0)]
    assert log_loss(preds) == pytest.approx(0.0, abs=1e-4)


def test_log_loss_coinflip_is_ln2():
    # Every term is -log(0.5) regardless of outcome -> mean = -log(0.5) = log(2) ~= 0.6931.
    preds = [_pred(0.5, 1), _pred(0.5, 0)]
    assert log_loss(preds) == pytest.approx(-math.log(0.5), abs=1e-4)
    assert log_loss(preds) == pytest.approx(0.6931, abs=1e-4)


def test_perfectly_calibrated_set_has_small_ece():
    # Construct a perfectly calibrated set by hand. With default n_bins=10 (width 0.1):
    #   - 10 races at p=0.7 (bin index int(0.7/0.1)=7, bin [0.7,0.8)); make exactly 7 Dem wins.
    #     mean_pred=0.7, frac_actual=7/10=0.7 -> gap 0.
    #   - 10 races at p=0.3 (bin index int(0.3/0.1)=3, bin [0.3,0.4)); make exactly 3 Dem wins.
    #     mean_pred=0.3, frac_actual=3/10=0.3 -> gap 0.
    # Both bins have zero gap, so ECE = 0 exactly. (We assert < 0.05 to allow for rounding.)
    preds = []
    preds += [_pred(0.7, 1) for _ in range(7)] + [_pred(0.7, 0) for _ in range(3)]
    preds += [_pred(0.3, 1) for _ in range(3)] + [_pred(0.3, 0) for _ in range(7)]
    assert calibration_error(preds) == pytest.approx(0.0, abs=1e-9)
    assert calibration_error(preds) < 0.05


def test_badly_miscalibrated_set_has_large_ece_and_blocked():
    # All races predicted p=0.9 but only 10% (1 of 10) actually Dem wins.
    # Single nonempty bin [0.9,1.0): mean_pred=0.9, frac_actual=0.1, gap=0.8, weight 10/10=1.
    # ECE = 1.0 * |0.9 - 0.1| = 0.8 (> 0.5).
    preds = [_pred(0.9, 1)] + [_pred(0.9, 0) for _ in range(9)]
    assert calibration_error(preds) == pytest.approx(0.8, abs=1e-9)
    assert calibration_error(preds) > 0.5
    report = run_backtest(preds)
    # brier = mean((0.9-1)^2 + 9*(0.9-0)^2) = (0.01 + 9*0.81)/10 = 7.30/10 = 0.73.
    assert report["brier"] == pytest.approx(0.73, abs=1e-9)
    assert is_calibrated(report) is False  # blocked: both ece and brier fail


def test_is_calibrated_gate_true_and_false():
    good = {"ece": 0.05, "brier": 0.18}
    bad_ece = {"ece": 0.40, "brier": 0.18}
    bad_brier = {"ece": 0.05, "brier": 0.30}
    assert is_calibrated(good) is True
    assert is_calibrated(bad_ece) is False  # ece > max_ece (0.1)
    assert is_calibrated(bad_brier) is False  # brier > max_brier (0.25)


def test_accuracy_known_set():
    # threshold 0.5. Calls: 0.9->Dem(1) actual 1 hit; 0.6->Dem actual 0 miss;
    # 0.4->Rep(0) actual 0 hit; 0.2->Rep actual 1 miss. 2 of 4 correct -> 0.5.
    preds = [_pred(0.9, 1), _pred(0.6, 0), _pred(0.4, 0), _pred(0.2, 1)]
    assert accuracy(preds) == 0.5


def test_accuracy_all_correct():
    preds = [_pred(0.8, 1), _pred(0.1, 0), _pred(0.55, 1)]
    assert accuracy(preds) == 1.0


def test_calibration_bins_shape_and_top_bin():
    # p=1.0 must land in the top bin [0.9, 1.0]; empty bins report None.
    preds = [_pred(1.0, 1), _pred(0.05, 0)]
    bins = calibration_bins(preds, n_bins=10)
    assert len(bins) == 10
    assert bins[-1]["bin_lo"] == 0.9 and bins[-1]["bin_hi"] == 1.0
    assert bins[-1]["n"] == 1
    assert bins[-1]["mean_pred"] == 1.0 and bins[-1]["frac_actual"] == 1.0
    assert bins[0]["n"] == 1  # the 0.05 prediction
    assert bins[5]["n"] == 0 and bins[5]["mean_pred"] is None  # empty bin -> None


def test_run_backtest_assembles_report_and_calibration():
    preds = [_pred(1.0, 1), _pred(0.0, 0)]
    report = run_backtest(preds)
    assert report["n"] == 2
    assert report["brier"] == 0.0
    assert "calibration" in report
    assert len(report["calibration"]) == 10


def test_empty_preds_raise():
    with pytest.raises(ValueError):
        brier_score([])
    with pytest.raises(ValueError):
        run_backtest([])
    with pytest.raises(ValueError):
        calibration_error([])
