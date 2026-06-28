import pytest

from btb_pipeline.ml_challenger import (
    LogisticModel,
    choose_model,
    fit_logistic,
    predict_proba,
)


def test_fit_learns_a_separable_pattern():
    # Dem wins when feature x0 (pvi) > 0. Clean separation -> model predicts accordingly.
    X = [[-0.3], [-0.2], [-0.1], [0.1], [0.2], [0.3]]
    y = [0, 0, 0, 1, 1, 1]
    model = fit_logistic(X, y, epochs=3000)
    probs = predict_proba(model, X)
    assert probs[0] < 0.5 < probs[-1]  # leans R for negative pvi, D for positive
    # accuracy on training data is perfect for this clean split
    preds = [1 if p >= 0.5 else 0 for p in probs]
    assert preds == y


def test_fit_validates_input():
    with pytest.raises(ValueError):
        fit_logistic([], [])
    with pytest.raises(ValueError):
        fit_logistic([[1.0], [2.0]], [1])  # length mismatch


def test_choose_model_keeps_heuristic_when_ml_not_better():
    actual = [1, 0, 1, 0]
    heuristic = [0.9, 0.1, 0.8, 0.2]  # good
    ml = [0.5, 0.5, 0.5, 0.5]  # worse
    out = choose_model(heuristic, ml, actual)
    assert out["chosen"] == "heuristic"
    assert out["ml_brier"] > out["heuristic_brier"]


def test_choose_model_adopts_ml_when_better():
    actual = [1, 0, 1, 0]
    heuristic = [0.5, 0.5, 0.5, 0.5]  # poor
    ml = [0.95, 0.05, 0.9, 0.1]  # better
    out = choose_model(heuristic, ml, actual)
    assert out["chosen"] == "ml"


def test_choose_model_empty_raises():
    with pytest.raises(ValueError):
        choose_model([], [], [])


def test_model_is_serializable():
    m = fit_logistic([[0.1], [-0.1]], [1, 0])
    assert isinstance(m, LogisticModel)
    assert m.model_dump()["bias"] == m.bias
