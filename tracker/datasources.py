"""Databronnen voor de tracker.

Alle data komt uit publieke, gratis bronnen zonder API-key:
  * FRED (Federal Reserve Bank of St. Louis) via de publieke CSV-endpoint
      - DGS10          : 10-jaars US Treasury constant maturity yield
      - BAMLH0A0HYM2   : ICE BofA US High Yield Index Option-Adjusted Spread
  * Yahoo Finance via yfinance
      - KRE, HYG, AGG  : slotkoersen + uitgekeerde distributies

Er wordt niets geschat of ingevuld: ontbrekende observaties blijven leeg (NaN).
"""
from __future__ import annotations

import datetime as dt
import io
from typing import Iterable

import pandas as pd
import requests

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
USER_AGENT = "market-stability-tracker/1.0 (+https://github.com)"


# ---------------------------------------------------------------------------
# FRED
# ---------------------------------------------------------------------------
def fetch_fred(series_id: str, start: dt.date) -> pd.Series:
    """Dagelijkse FRED-reeks als pandas Series (index = datum, float waarden)."""
    resp = requests.get(
        FRED_CSV,
        params={"id": series_id, "cosd": start.isoformat()},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    # FRED gebruikt "." voor feestdagen / ontbrekende observaties
    values = pd.to_numeric(df[series_id], errors="coerce")
    out = pd.Series(values.values, index=df[date_col], name=series_id)
    return out.dropna().sort_index()


# ---------------------------------------------------------------------------
# Yahoo Finance
# ---------------------------------------------------------------------------
def _yf_ticker(ticker: str):
    import yfinance as yf

    return yf.Ticker(ticker)


def fetch_close(ticker: str, start: dt.date) -> pd.Series:
    """Dagelijkse (niet-aangepaste) slotkoers."""
    hist = _yf_ticker(ticker).history(
        start=start.isoformat(), auto_adjust=False, actions=False
    )
    if hist.empty:
        raise RuntimeError(f"Geen koersdata ontvangen voor {ticker}")
    close = hist["Close"].copy()
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    close.name = ticker
    return close.dropna().sort_index()


def fetch_dividends(ticker: str) -> pd.Series:
    """Volledige distributiehistoriek (per ex-datum)."""
    div = _yf_ticker(ticker).dividends
    if div is None or div.empty:
        return pd.Series(dtype="float64")
    div.index = pd.to_datetime(div.index).tz_localize(None).normalize()
    return div.sort_index()


def ttm_yield_series(ticker: str, start: dt.date) -> pd.Series:
    """Trailing-twelve-month distributierendement in % (som uitkeringen / koers).

    Wordt gebruikt voor de HYG-vs-AGG proxy. Dit is expliciet GEEN OAS.
    """
    # koersen ruim genoeg ophalen om 12 maanden terug te kunnen kijken
    close = fetch_close(ticker, start - dt.timedelta(days=400))
    div = fetch_dividends(ticker)
    if div.empty:
        return pd.Series(dtype="float64", name=ticker)
    div = div[div.index >= pd.Timestamp(start) - pd.Timedelta(days=400)]
    ttm = pd.Series(index=close.index, dtype="float64", name=ticker)
    for date in close.index:
        window = div[(div.index > date - pd.Timedelta(days=365)) & (div.index <= date)]
        if window.empty:
            continue
        ttm.loc[date] = float(window.sum()) / float(close.loc[date]) * 100.0
    return ttm.dropna()


# ---------------------------------------------------------------------------
# Afgeleide reeksen
# ---------------------------------------------------------------------------
def consecutive_days_above(series: pd.Series, level: float) -> pd.Series:
    """Aantal opeenvolgende handelsdagen (t.e.m. die dag) boven `level`."""
    above = series > level
    streak = above.groupby((~above).cumsum()).cumsum()
    return streak.astype(int)


def rolling_drawdown_pct(series: pd.Series, window_days: int) -> pd.DataFrame:
    """Rollend hoogtepunt en drawdown in % t.o.v. dat hoogtepunt."""
    roll_max = series.rolling(f"{window_days}D", min_periods=1).max()
    dd = (series / roll_max - 1.0) * 100.0
    return pd.DataFrame({"level": series, "rolling_high": roll_max, "drawdown_pct": dd})


def week_ends(index: pd.DatetimeIndex, anchor: str = "W-FRI") -> pd.DatetimeIndex:
    return pd.DatetimeIndex(sorted(set(index.to_period(anchor.replace("W-", "W-")).to_timestamp(how="end").normalize())))


# ---------------------------------------------------------------------------
# Hoofdfunctie: bouw een weekframe
# ---------------------------------------------------------------------------
def build_weekly_frame(cfg: dict, start: dt.date, end: dt.date | None = None) -> pd.DataFrame:
    """Haalt alle bronnen op en aggregeert naar weekniveau (default: vrijdagclose).

    Retourneert een DataFrame met 1 rij per week en kolom `week_end`.
    """
    end = end or dt.date.today()
    anchor = cfg.get("week_anchor", "W-FRI")
    sig = cfg["signals"]

    fetch_start = start - dt.timedelta(days=420)  # extra buffer voor 52w high / TTM

    # --- 1. 10y treasury ---------------------------------------------------
    ust = fetch_fred(sig["ust10y"]["source"].split(":", 1)[1], fetch_start)
    level = float(sig["ust10y"]["trigger_level"])
    streak = consecutive_days_above(ust, level)

    # --- 2. KRE ------------------------------------------------------------
    kre = fetch_close(sig["kre"]["source"].split(":", 1)[1], fetch_start)
    kre_dd = rolling_drawdown_pct(kre, int(sig["kre"]["drawdown_window_days"]))

    # --- 3. Credit spread (OAS) -------------------------------------------
    oas = fetch_fred(sig["credit_spread"]["source"].split(":", 1)[1], fetch_start)

    # --- 3b. Proxy HYG - AGG ----------------------------------------------
    try:
        hyg = ttm_yield_series("HYG", fetch_start)
        agg = ttm_yield_series("AGG", fetch_start)
        proxy = (hyg - agg).dropna()
    except Exception:  # proxy is optioneel, mag de update nooit blokkeren
        proxy = pd.Series(dtype="float64")

    # --- weekaggregatie ----------------------------------------------------
    def last_in_week(s: pd.Series) -> pd.Series:
        return s.resample(anchor).last()

    def max_in_week(s: pd.Series) -> pd.Series:
        return s.resample(anchor).max()

    def count_in_week(s: pd.Series, lvl: float) -> pd.Series:
        return (s > lvl).resample(anchor).sum()

    frame = pd.DataFrame(
        {
            "ust10y_close": last_in_week(ust),
            "ust10y_week_high": max_in_week(ust),
            "ust10y_days_above_trigger": count_in_week(ust, level),
            "ust10y_max_consec_days_above_trigger": max_in_week(streak),
            "kre_close": last_in_week(kre),
            "kre_52w_high": last_in_week(kre_dd["rolling_high"]),
            "kre_drawdown_pct": last_in_week(kre_dd["drawdown_pct"]),
            "hy_oas": last_in_week(oas),
            "hyg_agg_proxy": last_in_week(proxy) if not proxy.empty else pd.Series(dtype="float64"),
        }
    )

    # as_of = laatste effectieve observatiedatum binnen die week
    obs_dates = pd.Series(1.0, index=ust.index.union(kre.index).union(oas.index))
    as_of = obs_dates.resample(anchor).apply(
        lambda s: s.index.max() if len(s) else pd.NaT
    )
    frame["as_of"] = as_of

    frame.index.name = "week_end"
    frame = frame.loc[frame.index >= pd.Timestamp(start)]
    frame = frame.loc[frame.index <= pd.Timestamp(end) + pd.Timedelta(days=6)]
    frame = frame.dropna(how="all")
    frame = frame.reset_index()
    frame["week_end"] = frame["week_end"].dt.date.astype(str)
    frame["as_of"] = pd.to_datetime(frame["as_of"]).dt.date.astype(str)
    for col in ("ust10y_days_above_trigger", "ust10y_max_consec_days_above_trigger"):
        frame[col] = frame[col].fillna(0).astype(int)
    for col in ("ust10y_close", "ust10y_week_high", "kre_close", "kre_52w_high",
                "kre_drawdown_pct", "hy_oas", "hyg_agg_proxy"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce").round(4)
    frame["source"] = "FRED:DGS10;FRED:BAMLH0A0HYM2;YF:KRE,HYG,AGG"
    return frame


def latest_snapshot(cfg: dict) -> pd.DataFrame:
    """Enkel de meest recente (deels afgelopen) week ophalen - gebruikt door 'Update'."""
    today = dt.date.today()
    frame = build_weekly_frame(cfg, start=today - dt.timedelta(days=21), end=today)
    return frame.tail(1)
