"""Pruebas del modelo exportado y de la regla de umbral (se saltan si aún no existe models/model.joblib)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proyecto.inference.predict import InputValidationError, load_model, predict_with_scores
from proyecto.inference.schema import load_schema

ROOT = Path(__file__).resolve().parents[1]
MODEL, SCHEMA = ROOT / "models" / "model.joblib", ROOT / "models" / "input_schema.json"
needs_model = pytest.mark.skipif(not (MODEL.exists() and SCHEMA.exists()), reason="sin modelo exportado (notebook 09)")


@pytest.fixture(scope="module")
def artifacts():
    return load_model(MODEL), load_schema(SCHEMA)


def example(schema, name="Crédito típico (36 meses)", **overrides) -> pd.DataFrame:
    row = dict(schema["examples"][name])
    row.update(overrides)
    return pd.DataFrame([row])[schema["numeric"] + schema["categorical"]]


@needs_model
def test_schema_has_the_business_threshold_and_no_sensitive_columns(artifacts):
    _, schema = artifacts
    assert 0 < schema["threshold"] < 1 and 0 < schema["base_rate"] < 1
    assert not {"age", "sex", "SEXO", "ESTADO CIVIL", "client_id"} & set(schema["numeric"] + schema["categorical"])


@needs_model
def test_typical_loan_gives_a_probability_and_a_decision(artifacts):
    model, schema = artifacts
    out = predict_with_scores(example(schema), model, schema)
    p = out[f"proba_{schema['class_names'][1]}"].iloc[0]
    assert 0 < p < 1 and out["decision"].iloc[0] in schema["class_names"]
    assert out["decision"].iloc[0] == (schema["class_names"][1] if p >= schema["threshold"] else schema["class_names"][0])


@needs_model
def test_short_term_loan_is_riskier_than_a_long_one(artifacts):
    model, schema = artifacts
    short = predict_with_scores(example(schema, "Plazo corto (6 meses)"), model, schema)
    long_ = predict_with_scores(example(schema, term_months=120), model, schema)
    col = f"proba_{schema['class_names'][1]}"
    assert short[col].iloc[0] > long_[col].iloc[0]


@needs_model
def test_impossible_term_is_refused(artifacts):
    model, schema = artifacts
    with pytest.raises(InputValidationError, match="term_months"):
        predict_with_scores(example(schema, term_months=-5), model, schema)


@needs_model
def test_unknown_values_still_predict(artifacts):
    model, schema = artifacts
    out = predict_with_scores(example(schema, interest_rate_ea=np.nan, city=np.nan), model, schema)
    assert len(out) == 1


@needs_model
def test_exported_model_matches_the_registered_test_metric(artifacts):
    """El modelo del repo es el que se evaluó en la etapa 7 (si la base procesada está disponible)."""
    test_path = ROOT / "data" / "processed" / "test.joblib"
    if not test_path.exists():
        pytest.skip("sin data/processed/test.joblib (se genera con el notebook 03)")
    import joblib
    model, schema = artifacts
    test = joblib.load(test_path)
    p = model.predict_proba(test[schema["numeric"] + schema["categorical"]])[:, 1]
    recall = (p[test["mora_30"] == 1] >= schema["threshold"]).mean()
    expected = json.loads((ROOT / "reports" / "07_metricas_test.json").read_text(encoding="utf-8"))
    assert recall == pytest.approx(expected["prueba"]["recall de mora (métrica principal)"]["modelo"][0], abs=1e-9)


def test_threshold_rule_in_predict_with_scores():
    class Fixed:
        classes_ = np.array([0, 1])

        def predict_proba(self, X):
            return np.column_stack([1 - X["p"].to_numpy(), X["p"].to_numpy()])

    schema = {"numeric": ["p"], "categorical": [], "class_names": ["al día", "mora"], "threshold": 0.2, "base_rate": 0.16,
              "review_margin": 0.01}
    out = predict_with_scores(pd.DataFrame({"p": [0.25, 0.15, 0.205]}), Fixed(), schema)
    assert out["decision"].tolist() == ["mora", "al día", "mora"]          # se decide con el umbral, no con 0,5
    assert out["needs_review"].tolist() == [False, False, True]           # 0,205 está a menos de 0,01 del umbral
    assert out["relative_risk"].iloc[0] == pytest.approx(0.25 / 0.16)


def test_portable_xgboost_gives_identical_probabilities_after_save_and_load(tmp_path):
    import joblib
    from sklearn.pipeline import Pipeline
    from xgboost import XGBClassifier
    from proyecto.models.portable import PortableXGBClassifier, make_portable
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(300, 4)), rng.integers(0, 2, 300)
    pipe = Pipeline([("model", XGBClassifier(n_estimators=20, max_depth=3))]).fit(X, y)
    joblib.dump(make_portable(pipe), tmp_path / "m.joblib", compress=0)
    loaded = joblib.load(tmp_path / "m.joblib")
    assert isinstance(loaded.steps[-1][1], PortableXGBClassifier)
    assert np.abs(loaded.predict_proba(X) - pipe.predict_proba(X)).max() < 1e-6
