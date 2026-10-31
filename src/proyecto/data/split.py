"""Partición por cliente.

Un cliente puede tener hasta 4 créditos (12.627 clientes tienen más de uno). Si se parte por fila, los créditos
de un mismo cliente caen a ambos lados y la métrica sale inflada (fuga). Aquí TODAS las particiones respetan
al cliente completo.
"""
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

from proyecto.config import GROUP_COL, RANDOM_STATE


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


def group_cv(n_splits: int = 5, seed: int = RANDOM_STATE) -> StratifiedGroupKFold:
    """Validación cruzada que mantiene a cada cliente en un solo pliegue y conserva la tasa de mora en cada uno."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
