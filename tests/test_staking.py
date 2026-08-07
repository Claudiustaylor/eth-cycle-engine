from __future__ import annotations

import pandas as pd

from staking.model import StakingModel


def test_staking_rewards_and_compounding(config):
    model = StakingModel(config)
    model.stake(10, pd.Timestamp("2020-01-01"))
    reward = model.staking_reward(pd.Timestamp("2020-01-02"))
    assert reward > 0
    model.apply_compounding(pd.Timestamp("2020-01-02"))
    assert model.total_staked() > 10


def test_lockup_blocks_unstake(config):
    cfg = {**config, "staking": {**config["staking"], "lockup_days": 10}}
    model = StakingModel(cfg)
    model.stake(1, pd.Timestamp("2020-01-01"))
    assert model.unstake(1, pd.Timestamp("2020-01-02")) == 0
