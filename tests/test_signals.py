"""Tests voor de statuslogica en het historiekbeheer (geen netwerk nodig)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tracker.config import load_config  # noqa: E402
from tracker.datasources import consecutive_days_above, rolling_drawdown_pct  # noqa: E402
from tracker.history import merge_rows  # noqa: E402
from tracker.signals import (  # noqa: E402
    GREEN,
    RED,
    YELLOW,
    all_statuses,
    overall_status,
    status_credit,
    status_kre,
    status_ust10y,
)


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def _row(**kw):
    base = dict(
        week_end=pd.Timestamp("2026-07-24"),
        ust10y_close=4.0,
        ust10y_max_consec_days_above_trigger=0,
        kre_close=75.0,
        kre_52w_high=78.0,
        kre_drawdown_pct=-3.8,
        hy_oas=2.8,
        hyg_agg_proxy=1.9,
        as_of="2026-07-24",
        updated_at="",
        source="",
    )
    base.update(kw)
    return pd.DataFrame([base])


def test_ust10y_green(cfg):
    assert status_ust10y(_row(ust10y_close=4.20), cfg).status == GREEN


def test_ust10y_yellow_on_warn_level(cfg):
    assert status_ust10y(_row(ust10y_close=4.80), cfg).status == YELLOW


def test_ust10y_yellow_when_above_but_streak_too_short(cfg):
    s = status_ust10y(_row(ust10y_close=5.10, ust10y_max_consec_days_above_trigger=2), cfg)
    assert s.status == YELLOW


def test_ust10y_red_on_three_consecutive_days(cfg):
    s = status_ust10y(_row(ust10y_close=5.05, ust10y_max_consec_days_above_trigger=3), cfg)
    assert s.status == RED


def test_kre_thresholds(cfg):
    assert status_kre(_row(kre_drawdown_pct=-5.0), cfg).status == GREEN
    assert status_kre(_row(kre_drawdown_pct=-20.0), cfg).status == YELLOW
    assert status_kre(_row(kre_drawdown_pct=-31.0), cfg).status == RED


def test_kre_absolute_floor_optional(cfg):
    cfg2 = {**cfg, "signals": {**cfg["signals"], "kre": {**cfg["signals"]["kre"]}}}
    cfg2["signals"]["kre"]["absolute_floor_enabled"] = True
    assert status_kre(_row(kre_close=30.0, kre_drawdown_pct=-10.0), cfg2).status == RED
    assert status_kre(_row(kre_close=30.0, kre_drawdown_pct=-10.0), cfg).status == GREEN


def test_credit_thresholds(cfg):
    assert status_credit(_row(hy_oas=3.0), cfg).status == GREEN
    assert status_credit(_row(hy_oas=5.0), cfg).status == YELLOW
    assert status_credit(_row(hy_oas=6.0), cfg).status == RED


def test_overall_is_worst(cfg):
    st = all_statuses(_row(hy_oas=6.5), cfg)
    assert overall_status(st) == RED


def test_consecutive_days_above():
    s = pd.Series([4.9, 5.1, 5.2, 4.8, 5.3, 5.4, 5.5], index=pd.date_range("2026-01-01", periods=7))
    streak = consecutive_days_above(s, 5.0)
    assert list(streak) == [0, 1, 2, 0, 1, 2, 3]


def test_rolling_drawdown():
    s = pd.Series([100, 120, 90], index=pd.date_range("2026-01-01", periods=3))
    dd = rolling_drawdown_pct(s, 365)
    assert round(dd["drawdown_pct"].iloc[-1], 2) == -25.0


def test_merge_keeps_history_and_updates_current_week():
    existing = merge_rows(pd.DataFrame(), _row(week_end="2026-07-17", ust10y_close=4.5))
    step2 = merge_rows(existing, _row(week_end="2026-07-24", ust10y_close=4.7))
    assert len(step2) == 2
    step3 = merge_rows(step2, _row(week_end="2026-07-24", ust10y_close=4.9))
    assert len(step3) == 2  # geen duplicaat
    assert float(step3.iloc[-1]["ust10y_close"]) == 4.9  # laatste waarde wint
    assert float(step3.iloc[0]["ust10y_close"]) == 4.5  # oude week onaangeroerd
