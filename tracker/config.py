"""Laden van config.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["_repo_root"] = str(REPO_ROOT)
    return cfg


def history_path(cfg: Dict[str, Any]) -> Path:
    return REPO_ROOT / cfg.get("history_file", "data/history.csv")
