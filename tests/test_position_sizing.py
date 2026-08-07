from __future__ import annotations

from risk.limits import RiskLimits
from risk.position_sizing import PositionSizer


def test_tranche_sizing(config):
    sizer = PositionSizer(config)
    assert sizer.size_by_score(65, 1000, 500, 1500) == 100
    assert sizer.size_by_score(95, 1000, 500, 1500) == 300
    assert sizer.size_by_score(20, 1000, 500, 1500) == -200


def test_risk_limits(config):
    limits = RiskLimits(config)
    assert limits.check_exposure(90, 100)
    assert not limits.check_exposure(99, 100)
