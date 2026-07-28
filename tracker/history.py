"""Beheer van de historiek-CSV.

Regels:
  * Bestaande rijen worden NOOIT verwijderd.
  * Een nieuwe update overschrijft enkel de rij van dezelfde `week_end`
    (de lopende week wordt dus verfijnd tot ze afgesloten is).
  * Elke rij krijgt een `updated_at` timestamp (UTC).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

COLUMNS = [
    "week_end",
    "as_of",
    "ust10y_close",
    "ust10y_week_high",
    "ust10y_days_above_trigger",
    "ust10y_max_consec_days_above_trigger",
    "kre_close",
    "kre_52w_high",
    "kre_drawdown_pct",
    "hy_oas",
    "hyg_agg_proxy",
    "source",
    "updated_at",
]


def load_history(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(path)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[COLUMNS].sort_values("week_end").reset_index(drop=True)


def merge_rows(existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    """Voeg nieuwe weekrijen toe; bestaande weken worden geactualiseerd."""
    new_rows = new_rows.copy()
    new_rows["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for col in COLUMNS:
        if col not in new_rows.columns:
            new_rows[col] = pd.NA
    new_rows = new_rows[COLUMNS]

    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = combined.drop_duplicates(subset=["week_end"], keep="last")
    return combined.sort_values("week_end").reset_index(drop=True)


def save_history(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def to_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Historiek met een echte datetime-index, klaar voor de grafieken."""
    out = df.copy()
    out["week_end"] = pd.to_datetime(out["week_end"])
    numeric = [c for c in COLUMNS if c not in ("week_end", "as_of", "source", "updated_at")]
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values("week_end").reset_index(drop=True)
