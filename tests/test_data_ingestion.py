from __future__ import annotations

from data.ingestion import DataIngestion
from data.storage import data_exists, load_parquet, save_parquet


def test_parquet_roundtrip(tmp_path, synthetic_ohlcv):
    save_parquet(synthetic_ohlcv, "eth_test", tmp_path)
    loaded = load_parquet("eth_test", tmp_path)
    assert loaded is not None
    assert data_exists("eth_test", tmp_path)
    assert "close" in loaded


def test_optional_sources_return_none(config):
    ingestion = DataIngestion(config)
    assert ingestion.fetch_onchain("2020-01-01", "2020-01-02") is None
    assert ingestion.fetch_derivatives("2020-01-01", "2020-01-02") is None
