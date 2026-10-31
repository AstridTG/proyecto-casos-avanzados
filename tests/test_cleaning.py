"""Pruebas de la anonimización (`src/proyecto/data/cleaning.py`) con datos inventados."""
import pandas as pd
import pytest

from proyecto.data.cleaning import (
    CLIENT_ID_COL,
    DROP_COLUMNS,
    ID_COL,
    add_client_id,
    anonymize,
    drop_personal_columns,
    hash_id,
)

KEY = b"clave-de-prueba"


def _fake_raw(ids=("123", "456", "123")) -> pd.DataFrame:
    """Tabla mínima con todas las columnas a eliminar y una columna que debe quedarse."""
    df = pd.DataFrame({col: ["x"] * len(ids) for col in DROP_COLUMNS})
    df[ID_COL] = list(ids)
    df["DIAS DE MORA"] = [0, 45, 10]
    return df


def test_hash_id_is_stable_and_hides_the_id():
    assert hash_id("123", KEY) == hash_id(" 123 ", KEY)
    assert hash_id("123", KEY) != hash_id("456", KEY)
    assert "123" not in hash_id("123", KEY)
    assert len(hash_id("123", KEY)) == 16


def test_hash_id_depends_on_the_key():
    assert hash_id("123", KEY) != hash_id("123", b"otra-clave")


def test_add_client_id_groups_same_client():
    out = add_client_id(_fake_raw(), KEY)
    assert out.columns[0] == CLIENT_ID_COL
    assert out[CLIENT_ID_COL].iloc[0] == out[CLIENT_ID_COL].iloc[2]
    assert out[CLIENT_ID_COL].iloc[0] != out[CLIENT_ID_COL].iloc[1]


def test_add_client_id_rejects_missing_id():
    with pytest.raises(ValueError):
        add_client_id(_fake_raw(ids=("123", "", "456")), KEY)


def test_drop_personal_columns_fails_if_a_column_is_missing():
    with pytest.raises(ValueError):
        drop_personal_columns(_fake_raw().drop(columns=["NOMBRE O RAZON SOCIAL"]))


def test_anonymize_keeps_client_id_and_removes_personal_data():
    raw = _fake_raw()
    out = anonymize(raw, KEY)
    assert list(out.columns) == [CLIENT_ID_COL, "DIAS DE MORA"]
    assert ID_COL not in out.columns
    assert "EVENTO" not in out.columns
    assert len(out) == len(raw)
    assert ID_COL in raw.columns  # la tabla original no se modifica
