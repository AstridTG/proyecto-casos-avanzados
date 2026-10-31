"""Calificación masiva por archivo (se salta si no hay modelo exportado)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proyecto.inference.batch import (
    EXCLUDED, PRIORITY, BatchFormatError, read_table, score_batch, summarize_batch,
)
from proyecto.inference.predict import load_model
from proyecto.inference.schema import load_schema

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "models" / "model.joblib").exists(), reason="sin modelo exportado")


@pytest.fixture(scope="module")
def artifacts():
    return load_model(ROOT / "models" / "model.joblib"), load_schema(ROOT / "models" / "input_schema.json")


def system_rows() -> pd.DataFrame:
    """Tres créditos en el formato del sistema de cartera, con datos personales incluidos."""
    return pd.DataFrame({
        "NUMERO DE LA COLOCACION": [11, 22, 33], "NUMERO DE IDENTIFICACION": [1, 2, 3],
        "NOMBRE O RAZON SOCIAL": ["ANA", "LUIS", "EVA"], "TELEFONO 1": [300, 301, 302],
        "NRO IDENTIDAD CODEUDOR": [0, 5, 0], "CONDICION ESPECIAL": [0, 0, 1], "DIAS DE MORA": [0, 40, 400],
        "NUMERO DEL PRODUCTO": [118, 120, 120], "PLAZO UNIDAD TIEMPO PRODUCTO": [6, 60, 1],
        "VALOR ORIGINAL DEL PRESTAMO": [3e6, 2e7, 5e6], "VLR CUOTA MES": [540000.0, 450000.0, 5e6],
        "VALOR EQUI. EFECTIVA VENCIDA": [230592400, 215000000, 250000000], "DIA VENCIMIENTO CUOTA": [5, 15, 10],
        "TIPO NEGOCIO": [1, 1, 1], "DESTINO ECONOMICO": [12013, 12013, 12013],
        "NOMBRE CIUDAD": ["MEDELLIN - ANTIOQUIA"] * 3, "EDAD DEL CLIENTE": [40, 50, 60],
        "GARANTIA S/N": ["N", "S", "N"], "VALOR DE LA GARANTIA": [0, 1e7, 0], "NRO DEL CANAL DEL PRESTAMO": [1, 2, 3],
    })


def test_system_format_is_scored_without_personal_data(artifacts):
    model, schema = artifacts
    out = score_batch(system_rows(), model, schema)
    assert out.attrs["formato"] == "sistema" and len(out) == 3
    assert not {"NOMBRE O RAZON SOCIAL", "TELEFONO 1", "NUMERO DE IDENTIFICACION"} & set(out.columns)
    excluded = out[out["credito"] == "33"].iloc[0]
    assert excluded["prioridad"] == EXCLUDED and np.isnan(excluded["probabilidad_mora_30"])
    short, long_ = out.set_index("credito").loc[["11", "22"], "probabilidad_mora_30"]
    assert short > long_                                           # plazo corto = más riesgo
    s = summarize_batch(out)
    assert s["excluidos"] == 1 and s["calificados"] == 2 and s["moras_reales"] == 1


def test_model_format_and_impossible_values_do_not_stop_the_file(artifacts):
    model, schema = artifacts
    ex = pd.DataFrame([schema["examples"]["Crédito típico (36 meses)"]] * 2)
    ex.loc[1, "term_months"] = -5
    out = score_batch(ex, model, schema)
    assert out.attrs["formato"] == "modelo" and len(out) == 2
    assert (out["datos_corregidos"] == "term_months").sum() == 1
    assert out["probabilidad_mora_30"].notna().all()


def test_wrong_file_gives_a_clear_error(artifacts):
    model, schema = artifacts
    with pytest.raises(BatchFormatError, match="columnas necesarias"):
        score_batch(pd.DataFrame({"a": [1]}), model, schema)


def test_read_table_accepts_semicolon_csv(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    with open(path, "rb") as f:
        assert list(read_table(f, "x.csv").columns) == ["a", "b"]
