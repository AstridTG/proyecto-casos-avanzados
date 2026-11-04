"""Partición por cliente.

Un cliente puede tener hasta 4 créditos (12.627 clientes tienen más de uno). Si se parte por fila, los créditos
de un mismo cliente caen a ambos lados y la métrica sale inflada (fuga). Aquí TODAS las particiones respetan
al cliente completo.
"""
import hashlib
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

from proyecto.config import EXPECTED_SPLIT, GROUP_COL, RANDOM_STATE, RAW_SHA256


class ReproducibilityError(AssertionError):
    """El CSV o la partición no son los que obtuvo el grupo; el mensaje dice qué revisar."""


def split_by_group(df: pd.DataFrame, group_col: str = GROUP_COL, test_size: float = 0.2, seed: int = RANDOM_STATE):
    """Separa entrenamiento y prueba sin repartir a ningún cliente entre los dos. No pierde filas."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, groups=df[group_col]))
    train = df.iloc[train_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)
    assert_disjoint_groups(train, test, group_col=group_col)
    return train, test


def assert_disjoint_groups(*frames: pd.DataFrame, group_col: str = GROUP_COL) -> None:
    """Falla si algún cliente aparece en más de una partición."""
    seen: set = set()
    for i, frame in enumerate(frames):
        groups = set(frame[group_col])
        overlap = seen & groups
        if overlap:
            raise AssertionError(f"{len(overlap)} clientes aparecen en más de una partición (partición {i})")
        seen |= groups


def file_sha256(path) -> str:
    """Huella SHA-256 de un archivo: cambia si se modifica un solo carácter (por ejemplo, al guardarlo desde Excel)."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check_split_reproducibility(raw_path, train: pd.DataFrame, test: pd.DataFrame, group_col: str = GROUP_COL,
                                expected_sha256: str = RAW_SHA256, expected: dict = EXPECTED_SPLIT) -> dict:
    """Falla si el CSV original o las cifras de la partición no son las del grupo. Devuelve lo que midió."""
    observed = {"filas_entrenamiento": len(train), "filas_prueba": len(test),
                "clientes_prueba": int(test[group_col].nunique())}
    problems = []
    sha = file_sha256(raw_path)
    if sha != expected_sha256:
        problems.append(f"la huella del CSV original es {sha[:16]}…, se esperaba {expected_sha256[:16]}… "
                        "(¿otro archivo o se guardó desde Excel?)")
    for name, value in expected.items():
        if observed[name] != value:
            problems.append(f"{name} = {observed[name]:,}, se esperaba {value:,}")
    if problems:
        raise ReproducibilityError(
            "La partición no es la del grupo: " + "; ".join(problems)
            + ". Revisa: el mismo CSV, `git pull`, RANDOM_STATE = 42 y librerías de requirements.txt.")
    return observed


def group_cv(n_splits: int = 5, seed: int = RANDOM_STATE) -> StratifiedGroupKFold:
    """Validación cruzada que mantiene a cada cliente en un solo pliegue y conserva la tasa de mora en cada uno."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
