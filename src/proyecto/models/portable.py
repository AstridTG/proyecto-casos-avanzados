"""Versión portable del clasificador XGBoost para el archivo `models/model.joblib`.

XGBoost guarda su modelo interno en un formato binario que, dentro de un pickle/joblib, a veces no se puede
leer en otro sistema operativo ("XGBoostError: input stream corrupted", p. ej. al pasar de Linux a Windows).
Aquí el modelo se guarda como TEXTO JSON (el formato portable oficial de XGBoost) y se reconstruye al cargar.
Las predicciones son idénticas a las del modelo original (lo comprueba `tests/test_model_real.py`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.pipeline import Pipeline


class PortableXGBClassifier(BaseEstimator, ClassifierMixin):
    """Clasificador binario que guarda el booster de XGBoost como JSON."""

    def __init__(self, booster_json: str = "", classes=(0, 1)):
        self.booster_json = booster_json
        self.classes = classes

    @classmethod
    def from_xgb(cls, model) -> "PortableXGBClassifier":
        raw = model.get_booster().save_raw(raw_format="json")
        portable = cls(booster_json=bytes(raw).decode("utf-8"), classes=tuple(int(c) for c in model.classes_))
        portable.classes_ = np.array(portable.classes)
        return portable

    def _booster(self):
        if getattr(self, "_cached", None) is None:
            import xgboost as xgb
            booster = xgb.Booster()
            booster.load_model(bytearray(self.booster_json.encode("utf-8")))
            self._cached = booster
        return self._cached

    def __getstate__(self):  # el booster ya cargado no se guarda: solo el texto JSON
        state = self.__dict__.copy()
        state.pop("_cached", None)
        return state

    def fit(self, X, y):
        raise NotImplementedError("Modelo exportado solo para predecir; se entrena con XGBClassifier.")

    def predict_proba(self, X):
        import xgboost as xgb
        p = self._booster().predict(xgb.DMatrix(np.asarray(X, dtype=float)))
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return self.classes_[(self.predict_proba(X)[:, 1] >= 0.5).astype(int)]


def make_portable(pipeline: Pipeline) -> Pipeline:
    """Copia del pipeline con el paso final de XGBoost reemplazado por su versión portable (si lo es)."""
    from xgboost import XGBClassifier
    final = pipeline.steps[-1][1]
    if not isinstance(final, XGBClassifier):
        return pipeline
    steps = list(pipeline.steps[:-1]) + [(pipeline.steps[-1][0], PortableXGBClassifier.from_xgb(final))]
    return Pipeline(steps)


def same_predictions(a, b, X: pd.DataFrame, tol: float = 1e-6) -> bool:
    return bool(np.abs(a.predict_proba(X)[:, 1] - b.predict_proba(X)[:, 1]).max() < tol)
