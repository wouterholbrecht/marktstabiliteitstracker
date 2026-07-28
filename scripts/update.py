"""CLI-update: haalt de meest recente week op en voegt die toe aan de historiek.

Gebruik:
    python scripts/update.py            # enkel de lopende/laatste week
    python scripts/update.py --weeks 8  # de laatste 8 weken herberekenen
    python scripts/update.py --backfill # volledige historiek (config: history_years)
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tracker.config import history_path, load_config  # noqa: E402
from tracker.datasources import build_weekly_frame  # noqa: E402
from tracker.history import load_history, merge_rows, save_history  # noqa: E402
from tracker.signals import all_statuses, overall_message  # noqa: E402


def run_update(weeks: int | None = None, backfill: bool = False) -> Path:
    cfg = load_config()
    path = history_path(cfg)

    if backfill:
        years = float(cfg.get("history_years", 1))
        start = dt.date.today() - dt.timedelta(days=int(365 * years) + 7)
    else:
        start = dt.date.today() - dt.timedelta(days=7 * (weeks or 2) + 7)

    new_rows = build_weekly_frame(cfg, start=start)
    merged = merge_rows(load_history(path), new_rows)
    save_history(merged, path)

    from tracker.history import to_timeseries

    ts = to_timeseries(merged)
    statuses = all_statuses(ts, cfg)
    print(f"Historiek bijgewerkt: {len(merged)} weken -> {path}")
    for s in statuses.values():
        print(f"  [{s.status:>9}] {s.label}: {s.value_text} - {s.detail}")
    print(overall_message(statuses))
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=None)
    ap.add_argument("--backfill", action="store_true")
    args = ap.parse_args()
    run_update(weeks=args.weeks, backfill=args.backfill)
