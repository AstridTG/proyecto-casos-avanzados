"""Variables nuevas y preprocesamiento. Todo se ajusta DENTRO del Pipeline, solo con entrenamiento.

Conjuntos de variables (reports/04_features.md):
  - BASE: condiciones del crédito y del cliente conocidas al aprobar.
  - ideas medidas una a una: razones financieras, historial del cliente, empresa pagadora (codificada con su
    tasa de mora de entrenamiento) y edad.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler, TargetEncoder

from proyecto.config import RANDOM_STATE

BASE_NUMERIC = ["term_months", "loan_amount", "monthly_installment", "interest_rate_ea", "due_day",
                "has_guarantee", "guarantee_value", "has_cosigner"]
BASE_CATEGORICAL = ["product", "business_type", "economic_destination", "city"]

ENGINEERED = ["installment_ratio", "log_loan_amount", "guarantee_coverage"]

# Ideas de la etapa 4: nombre -> qué agrega
IDEAS = {
    "razones": {"engineered": True},
    "historial": {"numeric": ["prior_credits"]},
    "empresa": {"target_encoded": ["employer_id"]},
    "edad": {"numeric": ["age"]},
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Razones financieras conocidas al aprobar. No usa el objetivo ni otras filas: no puede filtrar información."""
    out = df.copy()
    amount = pd.to_numeric(out["loan_amount"], errors="coerce")
    safe_amount = amount.where(amount > 0)
    out["installment_ratio"] = pd.to_numeric(out["monthly_installment"], errors="coerce") / safe_amount
    out["log_loan_amount"] = np.log1p(amount.clip(lower=0))
    out["guarantee_coverage"] = (pd.to_numeric(out["guarantee_value"], errors="coerce").fillna(0) / safe_amount).clip(upper=10)
    return out


def feature_set(ideas: list[str] | tuple[str, ...] = ()) -> dict:
    """Columnas que usa un conjunto de ideas: {'numeric', 'categorical', 'target_encoded', 'engineered'}."""
    unknown = set(ideas) - set(IDEAS)
    if unknown:
        raise ValueError(f"Ideas desconocidas: {sorted(unknown)}. Opciones: {sorted(IDEAS)}")
    spec = {"numeric": list(BASE_NUMERIC), "categorical": list(BASE_CATEGORICAL), "target_encoded": [], "engineered": False}
    for idea in ideas:
        cfg = IDEAS[idea]
        spec["numeric"] += cfg.get("numeric", [])
        spec["target_encoded"] += cfg.get("target_encoded", [])
        spec["engineered"] = spec["engineered"] or cfg.get("engineered", False)
    return spec


def raw_input_columns(spec: dict) -> list[str]:
    """Columnas CRUDAS que necesita el pipeline (las que debe llenar la app)."""
    cols = spec["numeric"] + spec["categorical"] + spec["target_encoded"]
    if spec["engineered"]:
        cols += [c for c in ("loan_amount", "monthly_installment", "guarantee_value") if c not in cols]
    return list(dict.fromkeys(cols))


def build_preprocessor(spec: dict, scale: bool = False) -> ColumnTransformer:
    """Imputa, codifica y (si el modelo lo necesita) escala. Se ajusta solo con los datos de entrenamiento."""
    numeric = spec["numeric"] + (ENGINEERED if spec["engineered"] else [])
    num_steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        num_steps.append(("scale", StandardScaler()))
    transformers = [
        ("num", Pipeline(num_steps), numeric),
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value="desconocido")),
            ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=50, sparse_output=False)),
        ]), spec["categorical"]),
    ]
    if spec["target_encoded"]:
        te_steps = [("impute", SimpleImputer(strategy="constant", fill_value="desconocido")),
                    ("te", TargetEncoder(target_type="binary", smooth="auto",
                                          cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)))]
        if scale:
            te_steps.append(("scale", StandardScaler()))
        transformers.append(("employer", Pipeline(te_steps), spec["target_encoded"]))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)
