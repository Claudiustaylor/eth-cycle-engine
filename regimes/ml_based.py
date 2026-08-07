"""Optional lazy-import ML regime classifiers."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class MLRegimeClassifier:
    """Optional ML regime classifier with lazy third-party imports."""

    def __init__(self, method: str = "hmm", config: dict[str, Any] | None = None) -> None:
        self.method = method
        self.config = config or {}
        self.model: Any = None
        self.columns: list[str] = []

    def fit(self, features_df: pd.DataFrame, train_end_idx: int) -> MLRegimeClassifier:
        """Fit only on rows through train_end_idx."""

        train = features_df.iloc[: train_end_idx + 1].select_dtypes("number").dropna()
        self.columns = list(train.columns)
        if train.empty:
            logger.warning("No numeric rows available for ML regime fitting.")
            return self
        try:
            if self.method == "hmm":
                from hmmlearn.hmm import GaussianHMM

                self.model = GaussianHMM(n_components=4, random_state=self.config.get("seed", 42))
            elif self.method == "kmeans":
                from sklearn.cluster import KMeans

                self.model = KMeans(n_clusters=4, random_state=self.config.get("seed", 42), n_init="auto")
            elif self.method in {"rf", "gbm", "logistic"}:
                logger.warning("%s requires labels and is unavailable for unsupervised regimes.", self.method)
                return self
            else:
                logger.warning("Unknown ML regime method: %s", self.method)
                return self
            self.model.fit(train)
        except Exception as exc:  # pragma: no cover - optional dependency fallback
            logger.warning("ML regime classifier unavailable: %s", exc)
            self.model = None
        return self

    def predict(self, features_df: pd.DataFrame, idx: int) -> int | None:
        """Predict cluster/state for idx using the fitted model."""

        if self.model is None or not self.columns:
            return None
        row = features_df.iloc[[idx]][self.columns].dropna(axis=1)
        cols = [c for c in self.columns if c in row.columns]
        if not cols:
            return None
        return int(self.model.predict(row[cols])[0])

    def compare_with_rule_based(
        self, features_df: pd.DataFrame, rule_based_labels: pd.Series
    ) -> dict[str, float]:
        """Compare ML cluster availability against rule labels."""

        preds = [self.predict(features_df, i) for i in range(len(features_df))]
        valid = sum(p is not None for p in preds)
        return {"coverage": valid / max(len(preds), 1), "rule_labels": float(rule_based_labels.nunique())}
