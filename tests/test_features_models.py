"""Variables, métrica de negocio, pipeline y comparación con intervalos (con datos de juguete)."""
import numpy as np
import pandas as pd
import pytest

from proyecto.config import GROUP_COL, TARGET
from proyecto.data.split import group_cv
from proyecto.features.engineering import add_features, feature_set, raw_input_columns
from proyecto.models.train import (
    ShortTermRule, build_pipeline, candidates, evaluate_folds, metrics_at_threshold, recall_at_precision, split_xy,
    summarize, threshold_for_precision,
)
from proyecto.models.tuning import bootstrap_metric_ci, bootstrap_metric_difference, recall_at_fixed_threshold


@pytest.fixture(scope="module")
def loans() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    n = 1500
    term = rng.choice([6, 12, 24, 36, 60], n)
    df = pd.DataFrame({
        GROUP_COL: [f"c{i}" for i in rng.integers(0, 1000, n)],
        "term_months": term, "loan_amount": rng.uniform(1e6, 5e7, n), "monthly_installment": rng.uniform(5e4, 2e6, n),
        "interest_rate_ea": rng.uniform(12, 28, n), "due_day": rng.choice([5, 10, 15, 20], n),
        "has_guarantee": rng.integers(0, 2, n), "guarantee_value": rng.uniform(0, 1e7, n), "has_cosigner": rng.integers(0, 2, n),
        "product": rng.choice(["118", "120", "200"], n), "business_type": rng.choice(["1", "9"], n),
        "economic_destination": rng.choice(["12013", "70046"], n), "city": rng.choice(["CALI", "BELLO"], n),
        "employer_id": rng.choice([f"e{i}" for i in range(30)], n), "prior_credits": rng.integers(0, 3, n),
        "age": rng.integers(20, 70, n),
    })
    df[TARGET] = (rng.random(n) < np.where(term <= 12, 0.35, 0.10)).astype(int)   # plazo corto = más mora
    return df


def test_add_features_ratios():
    out = add_features(pd.DataFrame({"loan_amount": [1_000_000.0, 0.0], "monthly_installment": [100_000.0, 5.0],
                                     "guarantee_value": [2_000_000.0, np.nan]}))
    assert out["installment_ratio"].iloc[0] == pytest.approx(0.1)
    assert np.isnan(out["installment_ratio"].iloc[1])                       # monto 0: no se divide
    assert out["guarantee_coverage"].iloc[0] == pytest.approx(2.0)


def test_feature_set_adds_ideas_and_rejects_unknown():
    assert "prior_credits" in feature_set(["historial"])["numeric"]
    assert feature_set(["empresa"])["target_encoded"] == ["employer_id"]
    assert "employer_id" in raw_input_columns(feature_set(["empresa"]))
    with pytest.raises(ValueError, match="Ideas desconocidas"):
        feature_set(["inventada"])


def test_recall_at_precision_and_threshold():
    y = np.array([1, 1, 0, 0, 0, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.7, 0.2, 0.1, 0.3, 0.05, 0.6])
    assert recall_at_precision(y, p, 0.6) == pytest.approx(2 / 3)       # umbral 0,8: precisión 1, recall 2/3
    thr = threshold_for_precision(y, p, 0.6)
    assert metrics_at_threshold(y, p, thr)["precision"] >= 0.6
    assert recall_at_precision(y, np.full(8, 0.5), 0.9) == 0.0           # nunca alcanza la precisión exigida
    assert threshold_for_precision(y, np.full(8, 0.5), 0.9) is None


def test_short_term_rule_scores_short_loans_higher():
    proba = ShortTermRule().fit(None, None).predict_proba(pd.DataFrame({"term_months": [6, 60]}))
    assert proba[0, 1] > proba[1, 1] and np.allclose(proba.sum(axis=1), 1)


@pytest.mark.parametrize("name", ["regresión logística", "lightgbm", "línea base: tasa de mora (sin modelo)"])
def test_pipelines_fit_and_predict_probabilities(loans, name):
    model, scale = candidates()[name]
    X, y = split_xy(loans)
    pipe = build_pipeline(model, scale, ideas=["razones", "empresa", "historial"]).fit(X, y)
    proba = pipe.predict_proba(X.drop(columns=[GROUP_COL]))[:, 1]
    assert proba.shape == (len(X),) and ((proba >= 0) & (proba <= 1)).all()


def test_evaluate_folds_finds_the_planted_signal(loans):
    X, y = split_xy(loans)
    table = evaluate_folds(build_pipeline(*candidates()["lightgbm"]), X, y, group_cv(3))
    summary = summarize(table)
    assert len(table) == 3 and summary["roc_auc_mean"] > 0.6
    assert len(table.attrs["oof"]) == len(X)


def test_bootstrap_by_client_gives_an_interval_and_detects_no_difference():
    rng = np.random.default_rng(2)
    y, p, g = rng.integers(0, 2, 400), rng.random(400), np.repeat(np.arange(200), 2)
    value, low, high = bootstrap_metric_ci(y, p, g, recall_at_fixed_threshold(0.5), n_boot=200)
    assert low <= value <= high
    diff, low, high = bootstrap_metric_difference(y, p, p, g, recall_at_fixed_threshold(0.5), n_boot=50)
    assert diff == 0 and low == 0 and high == 0
