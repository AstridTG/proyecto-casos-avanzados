"""Calificación masiva: un archivo con muchos créditos -> probabilidad de mora y prioridad para cada uno.

Acepta dos formatos de archivo:
  1. **Formato del sistema de cartera** (las columnas originales, como `Base_sintetica_creditos.csv`): se le aplican
     las mismas transformaciones de la limpieza (se eliminan datos personales, se toman solo las columnas
     conocidas al aprobar, la tasa se pasa a %).
  2. **Formato del modelo:** las 12 columnas del esquema (`term_months`, `loan_amount`, ...).

A diferencia de la predicción de un solo crédito, aquí un valor imposible NO detiene todo el archivo: ese dato
queda vacío (lo imputa el modelo) y la fila se marca en la columna `datos_corregidos`. Los créditos reestructurados
tras la mora (`CONDICION ESPECIAL = 1`) no se califican: ya están vencidos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from proyecto.config import APPROVAL_COLUMNS, PLAUSIBLE_RANGE
from proyecto.data.cleaning import drop_personal_data, personal_columns, select_approval_columns

ID_RAW = "NUMERO DE LA COLOCACION"   # número del crédito (no es un dato personal)
ID_COL = "credito"
PRIORITY, NORMAL = "Priorizar revisión", "Seguimiento normal"
EXCLUDED = "Excluido: reestructurado tras la mora"


class BatchFormatError(ValueError):
    """El archivo no tiene las columnas necesarias; el mensaje dice cuáles faltan."""


def read_table(file, name: str = "") -> pd.DataFrame:
    """Lee CSV (coma o punto y coma) o Excel."""
    if name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    df = pd.read_csv(file, low_memory=False)
    if df.shape[1] == 1:  # probablemente separado por punto y coma
        if hasattr(file, "seek"):
            file.seek(0)
        df = pd.read_csv(file, sep=";", low_memory=False)
    return df


def detect_format(df: pd.DataFrame, schema: dict) -> str:
    model_cols = schema["numeric"] + schema["categorical"]
    if all(c in df.columns for c in model_cols):
        return "modelo"
    if all(c in df.columns for c in APPROVAL_COLUMNS):
        return "sistema"
    missing_model = [c for c in model_cols if c not in df.columns]
    missing_raw = [c for c in APPROVAL_COLUMNS if c not in df.columns]
    raise BatchFormatError(
        "El archivo no tiene las columnas necesarias. Use el formato del sistema de cartera (faltan: "
        f"{', '.join(missing_raw[:6])}{'…' if len(missing_raw) > 6 else ''}) o el formato del modelo (faltan: "
        f"{', '.join(missing_model[:6])}{'…' if len(missing_model) > 6 else ''})."
    )


def prepare_batch(df: pd.DataFrame, schema: dict) -> tuple[pd.DataFrame, pd.Series, str]:
    """Devuelve (X con las columnas del modelo, identificador de cada crédito, formato detectado).

    Nunca devuelve columnas personales.
    """
    fmt = detect_format(df, schema)
    model_cols = schema["numeric"] + schema["categorical"]
    ids = df[ID_RAW].astype(str) if ID_RAW in df.columns else pd.Series(np.arange(1, len(df) + 1), index=df.index).astype(str)
    if fmt == "sistema":
        clean = select_approval_columns(drop_personal_data(df))
        if "has_cosigner" not in clean.columns:
            clean["has_cosigner"] = np.nan
        X = clean[model_cols].copy()
    else:
        X = df[model_cols].copy()
        for col in schema["categorical"]:
            X[col] = X[col].astype("string").str.replace(r"\.0$", "", regex=True).astype(object).where(X[col].notna(), np.nan)
    X.index = df.index
    return X, ids, fmt


def fix_impossible(X: pd.DataFrame, schema: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Vacía los valores imposibles o no numéricos y dice en qué columnas lo hizo, fila por fila."""
    X = X.copy()
    fixed: list[list[str]] = [[] for _ in range(len(X))]
    ranges = {**PLAUSIBLE_RANGE, **{k: tuple(v) for k, v in schema.get("valid_range", {}).items()}}
    for col in schema["numeric"]:
        values = pd.to_numeric(X[col], errors="coerce")
        bad = (values.isna() & X[col].notna())
        if col in ranges:
            low, high = ranges[col]
            bad |= values.notna() & ~values.between(low, high)
        X[col] = values.where(~bad)
        for i in np.flatnonzero(bad.to_numpy()):
            fixed[i].append(col)
    notes = pd.Series([", ".join(f) for f in fixed], index=X.index, dtype=object)
    return X, notes


def score_batch(df: pd.DataFrame, model, schema: dict) -> pd.DataFrame:
    """Califica todos los créditos del archivo. Una fila por crédito, ordenadas de mayor a menor probabilidad."""
    X, ids, fmt = prepare_batch(df, schema)
    # Créditos reestructurados tras la mora (CONDICION ESPECIAL = 1): ya están vencidos y sus condiciones de
    # aprobación fueron reescritas (plazo 1 mes, cuota = saldo). No tiene sentido calificarlos.
    excluded = (pd.to_numeric(df["CONDICION ESPECIAL"], errors="coerce").fillna(0) == 1).to_numpy() \
        if "CONDICION ESPECIAL" in df.columns else np.zeros(len(df), dtype=bool)
    X, notes = fix_impossible(X, schema)
    notes[excluded] = ""
    proba = model.predict_proba(X)[:, 1]
    proba[excluded] = np.nan
    threshold, base_rate = float(schema["threshold"]), float(schema["base_rate"])
    priority = np.where(proba >= threshold, PRIORITY, NORMAL).astype(object)
    priority[excluded] = EXCLUDED
    out = pd.DataFrame({
        ID_COL: ids.values,
        "probabilidad_mora_30": np.round(proba, 4),
        "veces_el_promedio": np.round(proba / base_rate, 2),
        "prioridad": priority,
        "cerca_del_umbral": (np.abs(proba - threshold) < schema.get("review_margin", 0.005)) & ~excluded,
        "datos_corregidos": notes.values,
    }, index=X.index)
    out = pd.concat([out, X.reset_index(drop=True).set_axis(X.index)], axis=1)
    if "DIAS DE MORA" in df.columns:  # si el archivo trae la mora real (p. ej. la base histórica), se agrega para comparar
        out["mora_30_real"] = (pd.to_numeric(df["DIAS DE MORA"], errors="coerce") > 30).astype("Int64").values
    assert not personal_columns(out.columns), "la salida no debe tener datos personales"
    out.attrs["formato"] = fmt
    return out.sort_values("probabilidad_mora_30", ascending=False).reset_index(drop=True)


def summarize_batch(scored: pd.DataFrame) -> dict:
    """Resumen sin los créditos excluidos. Si el archivo trae la mora real, compara contra ella."""
    valid = scored[scored["prioridad"] != EXCLUDED]
    total = len(valid)
    flag = valid["prioridad"] == PRIORITY
    summary = {"creditos": len(scored), "excluidos": int(len(scored) - total), "calificados": total,
               "priorizados": int(flag.sum()), "porcentaje_priorizado": float(flag.mean()) if total else 0.0,
               "con_datos_corregidos": int((valid["datos_corregidos"] != "").sum()),
               "probabilidad_media": float(valid["probabilidad_mora_30"].mean()) if total else 0.0}
    if "mora_30_real" in valid.columns and total:
        real = valid["mora_30_real"].fillna(0).astype(int)
        summary.update({"moras_reales": int(real.sum()), "moras_detectadas": int((real[flag] == 1).sum()),
                        "precision": float(real[flag].mean()) if flag.any() else 0.0,
                        "recall": float(flag[real == 1].mean()) if real.any() else 0.0})
    return summary
