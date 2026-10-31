"""Limpieza de la base de cartera de libranza: una función por decisión del EDA (reports/01_eda.md).

Orden de `clean(df)`:
  1. `drop_personal_data`     — numera al cliente (`client_id`), crea `has_cosigner` y elimina datos personales.
  2. `drop_empty_and_constant`— quita columnas vacías o con un solo valor.
  3. `add_target`             — mora_30 = DIAS DE MORA > 30.
  4. `add_prior_credits`      — créditos que el cliente ya tenía al pedir este (se calcula con la base completa).
  5. `remove_restructured_block` — quita el bloque con condiciones reescritas después de la mora (fuga).
  6. `remove_unseasoned`      — quita créditos con menos de 4 meses de vida al corte.
  7. `select_approval_columns`— conserva solo lo conocido al aprobar, con nombres y unidades del proyecto.
  8. `flag_impossible_values` — lo imposible queda vacío (no se borra la fila).

Ninguna función modifica el DataFrame que recibe: todas devuelven una copia.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from proyecto.config import (
    APPROVAL_COLUMNS, CLIENT_ID_RAW, COSIGNER_ID_RAW, GROUP_COL, MIN_SEASONING_MONTHS, MORA_DAYS, PII_COLUMNS,
    PII_PREFIXES, PLAUSIBLE_RANGE, RAW_CSV, TARGET,
)

def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Lee el CSV crudo y elimina los datos personales en el MISMO paso: nunca circulan por el proyecto."""
    df = pd.read_csv(path, low_memory=False)
    return drop_personal_data(df)


def pseudonymize(values: pd.Series) -> pd.Series:
    """Numera a los clientes por orden de aparición (c00001, c00002...): el mismo documento, el mismo número.

    El número no se calcula a partir del documento, así que no hay forma de volver a él y no hace falta clave.
    El mismo archivo da siempre los mismos números; en otro archivo un cliente podría recibir otro número.
    """
    codes, _ = pd.factorize(values.astype(str).str.strip())
    return pd.Series([f"c{code + 1:05d}" for code in codes], index=values.index)


def personal_columns(columns) -> list[str]:
    """Columnas con datos personales presentes en `columns` (nombres, documentos, direcciones, teléfonos)."""
    return [c for c in columns if c in PII_COLUMNS or c.startswith(PII_PREFIXES)]


def drop_personal_data(df: pd.DataFrame) -> pd.DataFrame:
    """Decisión 1. Crea `client_id` (seudónimo) y `has_cosigner`, y elimina todas las columnas personales."""
    out = df.copy()
    if CLIENT_ID_RAW in out.columns:
        out[GROUP_COL] = pseudonymize(out[CLIENT_ID_RAW])
    if COSIGNER_ID_RAW in out.columns:
        out["has_cosigner"] = (pd.to_numeric(out[COSIGNER_ID_RAW], errors="coerce").fillna(0) != 0).astype(int)
    return out.drop(columns=personal_columns(out.columns))


def drop_empty_and_constant(df: pd.DataFrame, keep: tuple[str, ...] = ()) -> pd.DataFrame:
    """Decisión 2. Quita columnas 100 % vacías o con un único valor: no pueden informar nada."""
    useless = [c for c in df.columns if c not in keep and df[c].nunique(dropna=True) <= 1]
    return df.drop(columns=useless)


def add_target(df: pd.DataFrame, days: int = MORA_DAYS) -> pd.DataFrame:
    """Decisión 3. mora_30 = 1 si DIAS DE MORA > 30, 0 si no. Falla si la columna trae vacíos o negativos."""
    out = df.copy()
    dias = pd.to_numeric(out["DIAS DE MORA"], errors="coerce")
    if dias.isna().any() or (dias < 0).any():
        raise ValueError("DIAS DE MORA tiene vacíos o negativos: no se puede construir el objetivo")
    out[TARGET] = (dias > days).astype(int)
    return out


def _opening_date(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["FECHA APERTURA DEL PRESTAMO"].astype(str), format="%Y%m%d", errors="coerce")


def add_prior_credits(df: pd.DataFrame) -> pd.DataFrame:
    """Decisión 7. Número de créditos que el cliente abrió ANTES de este (se conoce el día que se aprueba).

    Se calcula con la base completa (antes de filtrar), porque los créditos anteriores existieron aunque
    después se excluyan del entrenamiento.
    """
    out = df.copy()
    order = pd.DataFrame({"g": out[GROUP_COL], "d": _opening_date(out), "k": out["NUMERO DE LA COLOCACION"]})
    order = order.sort_values(["g", "d", "k"])
    out["prior_credits"] = order.groupby("g").cumcount().reindex(out.index).astype(int)
    return out


def remove_restructured_block(df: pd.DataFrame) -> pd.DataFrame:
    """Decisión 5. Quita los créditos con CONDICION ESPECIAL = 1.

    Son 3.619 créditos vencidos (+181 días) cuyas condiciones se REESCRIBIERON después de la mora: plazo = 1 mes,
    cuota = todo el saldo, tasa de mora 950. Sus condiciones de aprobación ya no existen en la base, y su 100 % de
    mora haría que el modelo aprenda "plazo de 1 mes = mora" (fuga).
    """
    return df[pd.to_numeric(df["CONDICION ESPECIAL"], errors="coerce").fillna(0) != 1].copy()


def cutoff_date(df: pd.DataFrame) -> pd.Timestamp:
    """Fecha de corte de la base: el último pago registrado."""
    return pd.to_datetime(df["FECHA EFEC ULTIMO PAGO"].astype(str), format="%Y%m%d", errors="coerce").max()


def remove_unseasoned(df: pd.DataFrame, cutoff: pd.Timestamp | None = None,
                      months: int = MIN_SEASONING_MONTHS) -> pd.DataFrame:
    """Decisión 4. Quita créditos abiertos en los últimos `months` meses antes del corte.

    Un crédito de 1–3 meses casi no ha tenido tiempo de pasar 30 días en mora: en la base, los abiertos en
    agosto–octubre de 2026 tienen 0 % de mora. Dejarlos enseñaría al modelo que "nuevo = buen pagador".
    """
    cutoff = cutoff if cutoff is not None else cutoff_date(df)
    limit = (cutoff - pd.DateOffset(months=months)).normalize()
    return df[_opening_date(df) <= limit].copy()


def select_approval_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Decisión 6. Conserva solo lo conocido al aprobar, renombrado, con unidades legibles y tipos correctos.

    Todo lo demás (saldos, pagos, cuotas vencidas, intereses, estado, calificación...) se conoce DESPUÉS de
    aprobar y contiene la respuesta: se descarta.
    """
    missing = [c for c in APPROVAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en la base: {', '.join(missing)}")
    out = df[list(APPROVAL_COLUMNS)].rename(columns=APPROVAL_COLUMNS)
    out["interest_rate_ea"] = pd.to_numeric(out["interest_rate_ea"], errors="coerce") / 1e7  # 230592400 -> 23,06 %
    out["has_guarantee"] = out["has_guarantee"].astype(str).str.strip().str.upper().map({"S": 1, "N": 0})
    for col in ["product", "business_type", "economic_destination", "employer_id"]:
        out[col] = out[col].astype("Int64").astype(str).replace("<NA>", np.nan)
    out["city"] = out["city"].astype(str).str.strip()
    for col in ["has_cosigner", "prior_credits", GROUP_COL, TARGET]:
        if col in df.columns:
            out[col] = df[col].values
    return out


def flag_impossible_values(df: pd.DataFrame, ranges: dict = PLAUSIBLE_RANGE) -> pd.DataFrame:
    """Decisión 8. Lo que está fuera del rango posible queda vacío (lo imputa el Pipeline); la fila se conserva."""
    out = df.copy()
    for col, (low, high) in ranges.items():
        if col in out.columns:
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.where(values.between(low, high))
    return out


def clean(df: pd.DataFrame, cutoff: pd.Timestamp | None = None) -> pd.DataFrame:
    """Aplica todas las decisiones del EDA en orden. Recibe la base ya sin datos personales (`load_raw`)."""
    df = drop_personal_data(df)  # idempotente: por si llega la base cruda
    cutoff = cutoff if cutoff is not None else cutoff_date(df)
    df = drop_empty_and_constant(df, keep=("CONDICION ESPECIAL",))
    df = add_target(df)
    df = add_prior_credits(df)
    df = remove_restructured_block(df)
    df = remove_unseasoned(df, cutoff)
    df = select_approval_columns(df)
    df = flag_impossible_values(df)
    return df.reset_index(drop=True)


def cleaning_log(raw: pd.DataFrame) -> dict:
    """Cuántas filas y columnas quita cada paso (para el informe)."""
    base = drop_personal_data(raw)
    cutoff = cutoff_date(base)
    step1 = drop_empty_and_constant(base, keep=("CONDICION ESPECIAL",))
    step2 = add_prior_credits(add_target(step1))
    step3 = remove_restructured_block(step2)
    step4 = remove_unseasoned(step3, cutoff)
    final = clean(raw, cutoff)
    return {
        "filas_crudas": len(raw), "columnas_crudas": raw.shape[1],
        "columnas_personales_eliminadas": len(personal_columns(raw.columns)),
        "columnas_vacias_o_constantes": base.shape[1] - step1.shape[1],
        "filas_bloque_reestructurado": len(step2) - len(step3),
        "filas_sin_maduracion": len(step3) - len(step4),
        "fecha_corte": str(cutoff.date()),
        "filas_finales": len(final), "clientes_finales": int(final[GROUP_COL].nunique()),
        "tasa_mora_final": float(final[TARGET].mean()),
        "columnas_finales": final.shape[1],
    }
