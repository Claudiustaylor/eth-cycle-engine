from __future__ import annotations

import pandas as pd

from metrics.robustness import (
    monte_carlo_reshuffling,
    multiple_testing_correction,
    robustness_rating,
)


def test_overfitting_helpers():
    returns = pd.Series([0.01, -0.02, 0.03, -0.01] * 20)
    mc = monte_carlo_reshuffling(returns, 10)
    assert 0 <= mc["p_value"] <= 1
    assert multiple_testing_correction([0.01, 0.02]) == [0.02, 0.04]
    assert robustness_rating({"std": 0}, {}, {}, mc["p_value"])[0] in {"strong", "moderate", "weak", "likely_overfit"}
