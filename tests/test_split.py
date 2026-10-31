import numpy as np
import pandas as pd
import pytest

from proyecto.config import GROUP_COL, TARGET
from proyecto.data.split import assert_disjoint_groups, group_cv, split_by_group


@pytest.fixture
def df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    clients = np.repeat([f"c{i}" for i in range(300)], rng.integers(1, 5, 300))
    return pd.DataFrame({GROUP_COL: clients, TARGET: rng.integers(0, 2, len(clients)), "x": rng.normal(size=len(clients))})


def test_no_client_in_both_sides_and_no_row_lost(df):
    train, test = split_by_group(df, test_size=0.2)
    assert len(train) + len(test) == len(df)
    assert not set(train[GROUP_COL]) & set(test[GROUP_COL])
    assert 0.1 < len(test) / len(df) < 0.3


def test_split_is_reproducible(df):
    a, _ = split_by_group(df)
    b, _ = split_by_group(df)
    assert a.equals(b)


def test_disjoint_check_detects_a_row_wise_split(df):
    """Si alguien parte por fila, esta comprobación debe fallar (así se detecta la fuga)."""
    shuffled = df.sample(frac=1, random_state=1)
    cut = int(len(df) * 0.8)
    with pytest.raises(AssertionError, match="más de una partición"):
        assert_disjoint_groups(shuffled.iloc[:cut], shuffled.iloc[cut:])


def test_group_cv_keeps_each_client_in_one_fold(df):
    folds = {}
    for k, (_, valid) in enumerate(group_cv(5).split(df, df[TARGET], groups=df[GROUP_COL])):
        for client in df.iloc[valid][GROUP_COL].unique():
            assert client not in folds
            folds[client] = k
    assert len(folds) == df[GROUP_COL].nunique()
