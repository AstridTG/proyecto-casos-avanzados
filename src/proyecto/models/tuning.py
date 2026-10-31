"""Optimización de hiperparámetros con Optuna (cada ensayo registrado en MLflow) e intervalos por cliente."""
from __future__ import annotations

from pathlib import Path

import mlflow
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from proyecto.config import MIN_PRECISION, RANDOM_STATE
from proyecto.models.train import build_pipeline, evaluate_folds
from proyecto.tracking.mlflow_utils import log_run


def lgbm_space(trial: optuna.Trial) -> dict:
    """Rangos pensados para señal débil: árboles pequeños, hojas con muchos créditos y regularización."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 600),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 4, 31),
        "min_child_samples": trial.suggest_int("min_child_samples", 50, 800, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
    }


def xgb_space(trial: optuna.Trial) -> dict:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 600),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.1, log=True),
        "max_depth": trial.suggest_int("max_depth", 2, 6),
        "min_child_weight": trial.suggest_float("min_child_weight", 5, 200, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
    }


def make_lgbm(params: dict, random_state: int = RANDOM_STATE) -> LGBMClassifier:
    return LGBMClassifier(subsample_freq=1, random_state=random_state, verbose=-1, n_jobs=-1, **params)


def make_xgb(params: dict, random_state: int = RANDOM_STATE) -> XGBClassifier:
    return XGBClassifier(tree_method="hist", eval_metric="logloss", random_state=random_state, n_jobs=-1, **params)


# Parámetros de partida (los del torneo) para la comprobación honesta
START_PARAMS = {
    "lightgbm": {"n_estimators": 300, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 100,
                 "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0},
    "xgboost": {"n_estimators": 300, "learning_rate": 0.03, "max_depth": 4, "min_child_weight": 20,
                "subsample": 0.8, "colsample_bytree": 0.8},
}
MODELS = {"lightgbm": (lgbm_space, make_lgbm), "xgboost": (xgb_space, make_xgb)}

OBJECTIVES = {"pr_auc": "maximize", "roc_auc": "maximize", "recall_at_p": "maximize", "log_loss": "minimize"}


def tune(name: str, X: pd.DataFrame, y: np.ndarray, cv, n_trials: int, ideas=(), metric: str = "pr_auc",
         seed: int = RANDOM_STATE, log: bool = True, storage: str | Path | None = None) -> optuna.Study:
    """Estudio de Optuna que optimiza `metric`. Cada ensayo queda como ejecución anidada en MLflow con TODAS las
    métricas (negocio y técnicas), para poder ordenarlas por cualquiera. Con `storage` el estudio se reanuda."""
    if metric not in OBJECTIVES:
        raise ValueError(f"Métrica no soportada: {metric}. Opciones: {sorted(OBJECTIVES)}")
    space_fn, make_fn = MODELS[name]

    def objective(trial: optuna.Trial) -> float:
        params = space_fn(trial)
        folds = evaluate_folds(build_pipeline(make_fn(params), ideas=ideas), X, y, cv)
        board = {c: float(folds[c].mean()) for c in folds.columns}
        board.update({f"{c}_std": float(folds[c].std(ddof=1)) for c in folds.columns if c != "fit_seconds"})
        for k, v in board.items():
            trial.set_user_attr(k, v)
        if log:
            log_run(f"{name}-ensayo-{trial.number}", params, board,
                    tags={"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric}, nested=True)
        return board[metric]

    study = optuna.create_study(
        direction=OBJECTIVES[metric], sampler=optuna.samplers.TPESampler(seed=seed),
        study_name=f"libranzaradar-{name}-{metric}",
        storage=f"sqlite:///{Path(storage).as_posix()}" if storage else None, load_if_exists=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    remaining = max(n_trials - len([t for t in study.trials if t.state.is_finished()]), 0)
    if log:
        with mlflow.start_run(run_name=f"optuna-{name}") as parent:
            study.optimize(objective, n_trials=remaining)
            mlflow.log_metric(f"best_{metric}", study.best_value)
            mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
            mlflow.set_tags({"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric})
            study.set_user_attr("mlflow_parent_run_id", parent.info.run_id)
    else:
        study.optimize(objective, n_trials=remaining)
    return study


def _rows_by_group(groups) -> np.ndarray:
    groups = np.asarray(groups)
    return pd.Series(np.arange(len(groups))).groupby(groups).apply(lambda s: s.to_numpy()).to_numpy()


def bootstrap_metric_ci(y_true, proba, groups, metric_fn, n_boot: int = 500, seed: int = RANDOM_STATE):
    """Métrica con intervalo del 95 %, remuestreando CLIENTES completos (no filas). Devuelve (valor, inf, sup)."""
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    index = _rows_by_group(groups)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_boot):
        rows = np.concatenate(index[rng.integers(0, len(index), len(index))])
        values.append(metric_fn(y_true[rows], proba[rows]))
    return float(metric_fn(y_true, proba)), float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def bootstrap_metric_difference(y_true, proba_a, proba_b, groups, metric_fn, n_boot: int = 500, seed: int = RANDOM_STATE):
    """Diferencia (A − B) de una métrica con intervalo del 95 %, remuestreando clientes completos.
    Positiva = A obtiene más (para métricas donde más es mejor)."""
    y_true, proba_a, proba_b = np.asarray(y_true), np.asarray(proba_a), np.asarray(proba_b)
    index = _rows_by_group(groups)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        rows = np.concatenate(index[rng.integers(0, len(index), len(index))])
        diffs.append(metric_fn(y_true[rows], proba_a[rows]) - metric_fn(y_true[rows], proba_b[rows]))
    full = metric_fn(y_true, proba_a) - metric_fn(y_true, proba_b)
    return float(full), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def recall_at_fixed_threshold(threshold: float):
    """Función métrica (y, proba) -> recall con un umbral FIJO (el elegido en validación, no en la prueba)."""
    def fn(y, p):
        y, flag = np.asarray(y), np.asarray(p) >= threshold
        return float(flag[y == 1].mean()) if (y == 1).any() else 0.0
    return fn


def precision_at_fixed_threshold(threshold: float):
    def fn(y, p):
        y, flag = np.asarray(y), np.asarray(p) >= threshold
        return float(y[flag].mean()) if flag.any() else 0.0
    return fn


__all__ = ["tune", "bootstrap_metric_ci", "bootstrap_metric_difference", "START_PARAMS", "MODELS", "MIN_PRECISION"]
