"""Parquet storage utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _dataset_path(name: str, base_path: str | Path = "data/parquet/") -> Path:
    return Path(base_path) / name


def save_parquet(df: pd.DataFrame, name: str, base_path: str | Path = "data/parquet/") -> Path:
    """Save a DataFrame as a year-partitioned Parquet dataset and return its path."""

    path = _dataset_path(name, base_path)
    path.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if not isinstance(out.index, pd.DatetimeIndex):
        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"])
            out = out.set_index("date")
        elif "timestamp" in out.columns:
            out["timestamp"] = pd.to_datetime(out["timestamp"])
            out = out.set_index("timestamp")
    out.index = pd.to_datetime(out.index)
    out.index.name = out.index.name or "date"
    out["year"] = out.index.year
    out.reset_index().to_parquet(path, engine="pyarrow", partition_cols=["year"], index=False)
    return path


def load_parquet(name: str, base_path: str | Path = "data/parquet/") -> pd.DataFrame | None:
    """Load a Parquet dataset by name, returning None when it is unavailable."""

    path = _dataset_path(name, base_path)
    if not path.exists():
        return None
    df = pd.read_parquet(path, engine="pyarrow")
    date_col = None
    for candidate in ("date", "timestamp", "Date", "Datetime"):
        if candidate in df.columns:
            date_col = candidate
            break
    if date_col is None:
        for column in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                date_col = str(column)
                break
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
    return df.drop(columns=["year"], errors="ignore")


def data_exists(name: str, base_path: str | Path = "data/parquet/") -> bool:
    """Return whether a cached Parquet dataset exists."""

    return _dataset_path(name, base_path).exists()
