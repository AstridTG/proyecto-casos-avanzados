"""Candidatos, métrica de negocio y evaluación con validación cruzada por cliente.

Métrica principal (ficha de caso): recall de la clase "en mora" exigiendo precisión ≥ MIN_PRECISION.
Se calcula como el mayor recall que se alcanza con algún umbral cuya precisión sea al menos MIN_PRECISION.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, brier_score_loss, f1_score, log_loss, precision_recall_curve,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from xgboost import XGBClassifier

from proyecto.config import GROUP_COL, MIN_PRECISION, RANDOM_STATE, TARGET
from proyecto.features.engineering import add_features, build_preprocessor, feature_set, raw_input_columns


# ---------------------------------------------------------------- métrica de negocio
def recall_at_precision(y_true, proba, min_precision: float = MIN_PRECISION) -> float:
    """Mayor recall de la clase 1 con algún umbral cuya precisión sea ≥ min_precision (0 si ninguno la alcanza)."""
    precision, recall, _ = precision_recall_curve(np.asarray(y_true), np.asarray(proba))
    ok = precision[:-1] >= min_precision  # el último punto (recall 0) no corresponde a ningún umbral
    return float(recall[:-1][ok].max()) if ok.any() else 0.0


def threshold_for_precision(y_true, proba, min_precision: float = MIN_PRECISION) -> float | None:
    """Umbral que da el mayor recall con precisión ≥ min_precision. None si ningún umbral la alcanza."""
    precision, recall, thresholds = precision_recall_curve(np.asarray(y_true), np.asarray(proba))
    ok = np.where(precision[:-1] >= min_precision)[0]
    if not len(ok):
        return None
    best = ok[np.argmax(recall[:-1][ok])]
    return float(thresholds[best])


def metrics_at_threshold(y_true, proba, threshold: float) -> dict:
    """Métricas de la decisión 'marcar para revisión si proba ≥ umbral'."""
    y_true, flag = np.asarray(y_true), (np.asarray(proba) >= threshold).astype(int)
    return {
        "precision": precision_score(y_true, flag, zero_division=0),
        "recall": recall_score(y_true, flag, zero_division=0),
        "flag_rate": float(flag.mean()),
        "balanced_accuracy": balanced_accuracy_score(y_true, flag),
        "f1": f1_score(y_true, flag, zero_division=0),
    }


def metrics_from_proba(y_true, proba, min_precision: float = MIN_PRECISION) -> dict:
    """Tablero completo: la métrica de negocio y las técnicas (ranking y calidad de probabilidades)."""
    y_true, proba = np.asarray(y_true), np.clip(np.asarray(proba, dtype=float), 1e-6, 1 - 1e-6)
    out = {
        "recall_at_p": recall_at_precision(y_true, proba, min_precision),  # negocio (principal)
        "pr_auc": average_precision_score(y_true, proba),
        "roc_auc": roc_auc_score(y_true, proba),
        "log_loss": log_loss(y_true, proba, labels=[0, 1]),
        "brier": brier_score_loss(y_true, proba),
    }
    thr = threshold_for_precision(y_true, proba, min_precision)
    at = metrics_at_threshold(y_true, proba, thr) if thr is not None else {
        "precision": 0.0, "recall": 0.0, "flag_rate": 0.0, "balanced_accuracy": 0.5, "f1": 0.0}
    out.update({f"{k}_at_p": v for k, v in at.items()})
    return out


# ---------------------------------------------------------------- línea base de negocio
class ShortTermRule(BaseEstimator, ClassifierMixin):
    """Regla simple de un analista: 'entre más corto el plazo, más riesgo'. Puntaje = 1 / plazo."""

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        term = pd.to_numeric(X["term_months"], errors="coerce").fillna(36).clip(lower=1).to_numpy()
        score = 1.0 / term
        return np.column_stack([1 - score, score])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


# ---------------------------------------------------------------- candidatos y pipeline
def candidates(random_state: int = RANDOM_STATE) -> dict:
    """Modelos del torneo: nombre -> (estimador, necesita escalar). Parámetros de partida conservadores:
    con una señal débil, árboles profundos memorizan ruido."""
    return {
        "línea base: tasa de mora (sin modelo)": (DummyClassifier(strategy="prior"), False),
        "línea base: regla del plazo corto": (ShortTermRule(), False),
        "regresión logística": (LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced", random_state=random_state), True),
        "random forest": (RandomForestClassifier(n_estimators=300, min_samples_leaf=50, max_features=0.5,
                                                 class_weight="balanced_subsample", n_jobs=-1, random_state=random_state), False),
        "lightgbm": (LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=100,
                                    subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                    random_state=random_state, verbose=-1, n_jobs=-1), False),
        "xgboost": (XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=4, min_child_weight=20, subsample=0.8,
                                  colsample_bytree=0.8, tree_method="hist", eval_metric="logloss",
                                  random_state=random_state, n_jobs=-1), False),
    }


def build_pipeline(model, scale: bool = False, ideas=()) -> Pipeline:
    """Pipeline completo: (variables nuevas) -> preprocesamiento -> modelo. Se guarda y se despliega entero."""
    spec = feature_set(ideas)
    if isinstance(model, (DummyClassifier, ShortTermRule)):
        return Pipeline([("model", model)])
    steps = []
    if spec["engineered"]:
        steps.append(("features", FunctionTransformer(add_features)))
    steps += [("prep", build_preprocessor(spec, scale=scale)), ("model", model)]
    return Pipeline(steps)


def split_xy(df: pd.DataFrame):
    """X con todas las columnas (incluido client_id para agrupar; el preprocesamiento lo ignora) e y."""
    return df.drop(columns=[TARGET]), df[TARGET].to_numpy()


# ---------------------------------------------------------------- validación cruzada por cliente
def oof_predictions(pipeline, X: pd.DataFrame, y: np.ndarray, cv) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Probabilidades fuera de pliegue (cada crédito predicho por un modelo que no vio a su cliente)."""
    oof, fold_id, seconds = np.zeros(len(X)), np.zeros(len(X), dtype=int), []
    for fold, (tr, va) in enumerate(cv.split(X, y, groups=X[GROUP_COL])):
        model = clone(pipeline)
        start = time.time()
        model.fit(X.iloc[tr], y[tr])
        seconds.append(time.time() - start)
        oof[va] = model.predict_proba(X.iloc[va])[:, 1]
        fold_id[va] = fold
    return oof, fold_id, seconds


def evaluate_folds(pipeline, X: pd.DataFrame, y: np.ndarray, cv, min_precision: float = MIN_PRECISION) -> pd.DataFrame:
    """Una fila por pliegue con todas las métricas y el tiempo de ajuste."""
    oof, fold_id, seconds = oof_predictions(pipeline, X, y, cv)
    rows = []
    for fold in range(fold_id.max() + 1):
        m = fold_id == fold
        rows.append({"fold": fold, **metrics_from_proba(y[m], oof[m], min_precision), "fit_seconds": seconds[fold]})
    table = pd.DataFrame(rows).set_index("fold")
    table.attrs["oof"] = oof
    return table


def summarize(table: pd.DataFrame) -> dict:
    """Media y desviación entre pliegues de cada métrica."""
    out = {f"{c}_mean": float(table[c].mean()) for c in table.columns}
    out.update({f"{c}_std": float(table[c].std(ddof=1)) for c in table.columns if c != "fit_seconds"})
    return out


def input_columns(ideas=()) -> list[str]:
    """Columnas crudas que necesita el modelo con estas ideas."""
    return raw_input_columns(feature_set(ideas))
