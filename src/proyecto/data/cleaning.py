"""Anonimización de la base de créditos (criterio 8 de `criterios-dataset.md`).

Lee el CSV original de `data/raw/` (que nunca se modifica) y:
  1. Crea `id_cliente`, un código anónimo de la cédula (`NUMERO DE IDENTIFICACION`), para poder partir los
     datos por cliente. Es un HMAC-SHA256 con una clave secreta (`ANON_KEY` en `.env`): sin la clave no se
     puede volver a la cédula probando números, como sí pasaría con un hash simple.
  2. Elimina las columnas con datos personales: nombres, direcciones, teléfonos y números de identificación
     del cliente y de los codeudores, el dígito de chequeo y la dirección de la garantía. También cuatro
     campos personales que hoy están vacíos (zona postal, gerente, gestor y número de cuenta).
  3. Elimina `EVENTO`: no se usa como objetivo (ver `especificacion-proyecto.md`, sección 3).
  4. Guarda el resultado en `data/processed/`.

Las columnas con nombre repetido en el CSV llegan con sufijo (`TELEFONO CODEUDOR.1`, `.2`...): así las
nombra pandas al leer el archivo.
"""
import hashlib
import hmac
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
RAW_CSV = ROOT / "data" / "raw" / "Base_sintetica_creditos.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "creditos_anonimizados.csv"

ID_COL = "NUMERO DE IDENTIFICACION"
CLIENT_ID_COL = "id_cliente"

# Datos personales del cliente
CLIENT_PII = [
    "NUMERO DE IDENTIFICACION",
    "NUMERO DE IDENTIFICACION DEL",
    "NUMERO DE IDENTIFICACION DEL.1",
    "DIGITO DE CHEQUEO",
    "NOMBRE O RAZON SOCIAL",
    "DIRECCION LINEA 1",
    "DIRECCION LINEA 2",
    "DIRECCION LINEA 3",
    "TELEFONO 1",
    "TELEFONO 2",
    "TELEFONO 3",
]

# Datos personales de los codeudores (hasta 4 por crédito: sin número, 1, 2 y 3)
CODEBTOR_PII = (
    ["NRO IDENTIDAD CODEUDOR"] + [f"NRO IDENTIDAD CODEUDOR {i}" for i in (1, 2, 3)]
    + ["NOMBRE CODEUDOR"] + [f"NOMBRE CODEUDOR {i}" for i in (1, 2, 3)]
    + ["DIRECCION CODEUDOR"] + [f"DIRECCION CODEUDOR.{i}" for i in range(1, 12)]
    + ["TELEFONO CODEUDOR"] + [f"TELEFONO CODEUDOR.{i}" for i in range(1, 16)]
)

# Dirección del inmueble en garantía
GUARANTEE_PII = ["DIRECCION GARANTIA"]

# Campos personales vacíos al 100 % en la base actual: se quitan por si algún día llegan con datos
EMPTY_PII = ["ZONA POSTAL", "NOMBRE GERENTE CONDICION", "GESTOR", "NRO DE LA CUENTA"]

PII_COLUMNS = CLIENT_PII + CODEBTOR_PII + GUARANTEE_PII + EMPTY_PII

# Columnas que no son personales pero se descartan
DISCARDED_COLUMNS = ["EVENTO"]

DROP_COLUMNS = PII_COLUMNS + DISCARDED_COLUMNS


def get_anon_key() -> bytes:
    """Lee la clave secreta `ANON_KEY` desde `.env`; sin ella no se puede anonimizar."""
    load_dotenv(ROOT / ".env")
    key = os.getenv("ANON_KEY", "").strip()
    if not key:
        raise RuntimeError("Falta ANON_KEY en .env (ver .env.example)")
    return key.encode("utf-8")


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Lee el CSV original sin modificarlo. La cédula se lee como texto para no perder ceros ni dígitos."""
    return pd.read_csv(path, dtype={ID_COL: str}, low_memory=False)


def hash_id(value: str, key: bytes) -> str:
    """Código anónimo de 16 caracteres: siempre el mismo para la misma cédula y la misma clave."""
    return hmac.new(key, value.strip().encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def add_client_id(df: pd.DataFrame, key: bytes) -> pd.DataFrame:
    """Agrega `id_cliente` (código anónimo de la cédula) como primera columna."""
    if ID_COL not in df.columns:
        raise ValueError(f"Falta la columna {ID_COL!r}")
    ids = df[ID_COL].astype("string").str.strip()
    if ids.isna().any() or (ids == "").any():
        raise ValueError(f"Hay filas sin {ID_COL!r}: no se les puede asignar id_cliente")
    out = df.copy()
    out.insert(0, CLIENT_ID_COL, ids.map(lambda v: hash_id(v, key)))
    return out


def drop_personal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina los datos personales y `EVENTO`. Falla si alguna columna esperada no está en los datos."""
    missing = [c for c in DROP_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"No se encontraron estas columnas: {', '.join(missing)}")
    return df.drop(columns=DROP_COLUMNS)


def anonymize(df: pd.DataFrame, key: bytes) -> pd.DataFrame:
    """Crea `id_cliente` y después elimina las columnas personales (el orden importa: la cédula se borra)."""
    return drop_personal_columns(add_client_id(df, key))


def build_anonymized_dataset(raw_path=RAW_CSV, out_path=PROCESSED_CSV) -> pd.DataFrame:
    """Lee el CSV original, lo anonimiza y guarda el resultado en `data/processed/`."""
    df = anonymize(load_raw(raw_path), get_anon_key())
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    result = build_anonymized_dataset()
    print(f"Guardado {PROCESSED_CSV.relative_to(ROOT)}: {result.shape[0]} filas x {result.shape[1]} columnas")
