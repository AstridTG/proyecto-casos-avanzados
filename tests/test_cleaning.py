"""Una prueba por decisión del EDA, con datos hechos a mano (no necesitan la base real)."""
import numpy as np
import pandas as pd
import pytest

from proyecto.config import GROUP_COL, PII_COLUMNS, TARGET
from proyecto.data import cleaning as C


def raw_rows(**overrides) -> pd.DataFrame:
    """Tres créditos crudos mínimos con las columnas que usa la limpieza."""
    base = {
        "NUMERO DE LA COLOCACION": [1, 2, 3],
        "NUMERO DE IDENTIFICACION": [111, 111, 222],
        "NOMBRE O RAZON SOCIAL": ["ANA", "ANA", "LUIS"],
        "TELEFONO 1": [300, 300, 301],
        "DIRECCION LINEA 1": ["Calle 1", "Calle 1", "Calle 2"],
        "TELEFONO CODEUDOR.3": [0, 0, 0],
        "NRO IDENTIDAD CODEUDOR": [0, 999, 0],
        "DIAS DE MORA": [0, 45, 10],
        "CONDICION ESPECIAL": [0, 0, 1],
        "FECHA APERTURA DEL PRESTAMO": [20250101, 20260115, 20260901],
        "FECHA EFEC ULTIMO PAGO": [20261030, 20261001, 20261015],
        "NUMERO DEL PRODUCTO": [118, 120, 120],
        "PLAZO UNIDAD TIEMPO PRODUCTO": [12, 36, 1],
        "VALOR ORIGINAL DEL PRESTAMO": [5_000_000.0, 10_000_000.0, 2_000_000.0],
        "VLR CUOTA MES": [480_000.0, 380_000.0, 2_000_000.0],
        "VALOR EQUI. EFECTIVA VENCIDA": [230592400, 215000000, 250000000],
        "DIA VENCIMIENTO CUOTA": [20, 10, 5],
        "TIPO NEGOCIO": [1, 1, 9],
        "DESTINO ECONOMICO": [12013, 12013, 70046],
        "NOMBRE CIUDAD": ["CALI - VALLE", "CALI - VALLE", "BELLO - ANTIOQUIA"],
        "EDAD DEL CLIENTE": [38, 38, 51],
        "GARANTIA S/N": ["N", "S", "N"],
        "VALOR DE LA GARANTIA": [0, 15_000_000, 0],
        "NRO DEL CANAL DEL PRESTAMO": [29853, 29853, 11713],
        "CODIGO DE MONEDA": [0, 0, 0],          # constante
        "GESTOR": [np.nan, np.nan, np.nan],      # vacía
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_personal_data_is_removed_and_client_is_pseudonymized():
    out = C.drop_personal_data(raw_rows())
    assert not set(PII_COLUMNS) & set(out.columns)
    assert not any(c.startswith(("DIRECCION CODEUDOR", "TELEFONO CODEUDOR")) for c in out.columns)
    assert out[GROUP_COL].nunique() == 2 and out[GROUP_COL].iloc[0] == out[GROUP_COL].iloc[1]
    assert "111" not in "".join(out[GROUP_COL])                 # el seudónimo no contiene el documento
    assert out["has_cosigner"].tolist() == [0, 1, 0]


def test_load_raw_never_returns_personal_columns(tmp_path):
    path = tmp_path / "base.csv"
    raw_rows().to_csv(path, index=False)
    assert not C.personal_columns(C.load_raw(path).columns)


def test_empty_and_constant_columns_are_dropped_but_kept_on_request():
    out = C.drop_empty_and_constant(raw_rows(), keep=("CODIGO DE MONEDA",))
    assert "GESTOR" not in out.columns and "CODIGO DE MONEDA" in out.columns


def test_target_is_more_than_30_days():
    out = C.add_target(raw_rows(**{"DIAS DE MORA": [30, 31, 0]}))
    assert out[TARGET].tolist() == [0, 1, 0]                      # 30 días exactos NO es mora_30


def test_target_refuses_missing_or_negative_days():
    with pytest.raises(ValueError, match="DIAS DE MORA"):
        C.add_target(raw_rows(**{"DIAS DE MORA": [0, -1, 5]}))


def test_restructured_block_is_removed():
    out = C.remove_restructured_block(raw_rows())
    assert out["CONDICION ESPECIAL"].eq(0).all() and len(out) == 2


def test_unseasoned_loans_are_removed():
    cutoff = pd.Timestamp("2026-10-30")
    out = C.remove_unseasoned(raw_rows(), cutoff, months=4)        # límite: 2026-06-30
    assert out["NUMERO DE LA COLOCACION"].tolist() == [1, 2]


def test_prior_credits_counts_only_earlier_loans_of_the_same_client():
    df = C.drop_personal_data(raw_rows(**{"FECHA APERTURA DEL PRESTAMO": [20260115, 20250101, 20250301]}))
    out = C.add_prior_credits(df)
    assert out["prior_credits"].tolist() == [1, 0, 0]              # el crédito 1 es el segundo del cliente 111


def test_approval_columns_have_project_names_and_units():
    df = C.add_prior_credits(C.add_target(C.drop_personal_data(raw_rows())))
    out = C.select_approval_columns(df)
    assert out["interest_rate_ea"].iloc[0] == pytest.approx(23.05924)
    assert out["has_guarantee"].tolist() == [0, 1, 0]
    assert out["product"].iloc[0] == "118" and out["employer_id"].iloc[0] == "29853"
    assert "DIAS DE MORA" not in out.columns and "SALDO DEL PRESTAMO" not in out.columns   # nada posterior


def test_approval_columns_fail_loudly_if_a_column_is_missing():
    with pytest.raises(ValueError, match="Faltan columnas"):
        C.select_approval_columns(raw_rows().drop(columns=["VLR CUOTA MES"]))


def test_impossible_values_become_missing_without_dropping_rows():
    df = pd.DataFrame({"age": [38, 7, 130], "term_months": [12, 0, 36]})
    out = C.flag_impossible_values(df)
    assert len(out) == 3
    assert out["age"].isna().tolist() == [False, True, True]
    assert out["term_months"].isna().tolist() == [False, True, False]


def test_clean_end_to_end_keeps_only_valid_loans_and_no_personal_data():
    out = C.clean(raw_rows(), cutoff=pd.Timestamp("2026-10-30"))
    assert len(out) == 2 and set(out[TARGET]) == {0, 1}
    assert not C.personal_columns(out.columns)
    assert {GROUP_COL, TARGET, "has_cosigner", "prior_credits"} <= set(out.columns)
