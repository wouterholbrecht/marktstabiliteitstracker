"""Statuslogica van de drie Druckenmiller-signalen.

Kleurcodes (identiek voor alle signalen):
  GROEN  - rustig: de parameter zit ruim aan de veilige kant van de drempel.
  GEEL   - waakzaam: de vooraf gedefinieerde waarschuwingsgrens is geraakt,
           maar de eigenlijke triggervoorwaarde is nog niet vervuld.
  ROOD   - trigger: de volledige triggervoorwaarde (niveau EN eventuele
           tijdsvoorwaarde) is vervuld.
  GRIJS  - geen data beschikbaar voor die week.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd

GREEN, YELLOW, RED, GREY = "GROEN", "GEEL", "ROOD", "GEEN DATA"
_ORDER = {GREY: -1, GREEN: 0, YELLOW: 1, RED: 2}

COLOR_HEX = {GREEN: "#1a9850", YELLOW: "#e8a317", RED: "#d7191c", GREY: "#9e9e9e"}

LEGEND = {
    "ust10y": {
        GREEN: "Yield onder 4,75% - financieringskosten onder controle.",
        YELLOW: "Yield 4,75%-5,00%, of wel boven 5% maar minder dan 3 opeenvolgende handelsdagen.",
        RED: "Yield sluit 3 opeenvolgende handelsdagen boven 5,00%.",
    },
    "kre": {
        GREEN: "KRE minder dan 15% onder zijn 52-weeks hoogtepunt.",
        YELLOW: "KRE 15% tot 30% onder zijn 52-weeks hoogtepunt.",
        RED: "KRE 30% of meer onder zijn 52-weeks hoogtepunt (of onder de absolute vloer, indien die geactiveerd is).",
    },
    "credit_spread": {
        GREEN: "High yield OAS onder 4,50% - risicopremie normaal tot krap.",
        YELLOW: "High yield OAS tussen 4,50% en 6,00% - herprijzing van kredietrisico bezig.",
        RED: "High yield OAS op of boven 6,00% - kredietmarkt in stressmodus.",
    },
}


@dataclass
class SignalStatus:
    key: str
    label: str
    status: str
    value: Optional[float]
    value_text: str
    detail: str
    distance_text: str
    extras: Dict[str, Any] = field(default_factory=dict)

    @property
    def color(self) -> str:
        return COLOR_HEX[self.status]


def _fmt(value: Optional[float], unit: str, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n.v.t."
    if unit == "%":
        return f"{value:.{decimals}f}%"
    if unit == "USD":
        return f"${value:,.2f}"
    return f"{value:.{decimals}f}"


def _last_valid(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return None if s.empty else s.iloc[-1]


def status_ust10y(df: pd.DataFrame, cfg: Dict[str, Any]) -> SignalStatus:
    c = cfg["signals"]["ust10y"]
    level, warn = float(c["trigger_level"]), float(c["warn_level"])
    need = int(c["trigger_consecutive_days"])

    value = _last_valid(df, "ust10y_close")
    streak = _last_valid(df, "ust10y_max_consec_days_above_trigger")
    streak = 0 if streak is None or pd.isna(streak) else int(streak)

    if value is None:
        status, detail = GREY, "Geen yielddata beschikbaar."
    elif streak >= need:
        status = RED
        detail = f"{streak} opeenvolgende handelsdagen boven {level:.2f}% - triggervoorwaarde vervuld."
    elif value > level or streak > 0:
        status = YELLOW
        detail = f"Boven {level:.2f}% geweest gedurende {streak} opeenvolgende dag(en); er zijn er {need} nodig."
    elif value >= warn:
        status = YELLOW
        detail = f"Yield in de waarschuwingszone ({warn:.2f}%-{level:.2f}%)."
    else:
        status = GREEN
        detail = f"Yield ruim onder de waarschuwingsgrens van {warn:.2f}%."

    gap = None if value is None else level - float(value)
    return SignalStatus(
        key="ust10y",
        label=c["label"],
        status=status,
        value=None if value is None else float(value),
        value_text=_fmt(value, "%"),
        detail=detail,
        distance_text=("n.v.t." if gap is None else f"{gap:+.2f} procentpunt tot de drempel van {level:.2f}%"),
        extras={"streak": streak, "needed": need},
    )


def status_kre(df: pd.DataFrame, cfg: Dict[str, Any]) -> SignalStatus:
    c = cfg["signals"]["kre"]
    dd_trigger = float(c["drawdown_trigger_pct"])
    dd_warn = float(c["drawdown_warn_pct"])
    floor = float(c["absolute_floor"])
    floor_on = bool(c.get("absolute_floor_enabled", False))

    price = _last_valid(df, "kre_close")
    dd = _last_valid(df, "kre_drawdown_pct")
    high = _last_valid(df, "kre_52w_high")

    if price is None:
        return SignalStatus("kre", c["label"], GREY, None, "n.v.t.", "Geen koersdata beschikbaar.", "n.v.t.")

    dd = float(dd) if dd is not None and not pd.isna(dd) else 0.0
    floor_hit = floor_on and float(price) <= floor

    if dd <= dd_trigger or floor_hit:
        status = RED
        detail = f"Drawdown van {dd:.1f}% t.o.v. het 52-weeks hoogtepunt - crashdrempel van {dd_trigger:.0f}% bereikt."
        if floor_hit:
            detail = f"Koers onder de absolute vloer van ${floor:.2f}."
    elif dd <= dd_warn:
        status = YELLOW
        detail = f"Drawdown van {dd:.1f}%: correctie bezig, maar nog geen crash van {dd_trigger:.0f}%."
    else:
        status = GREEN
        detail = f"Slechts {dd:.1f}% onder het 52-weeks hoogtepunt."

    trigger_price = None if high is None or pd.isna(high) else float(high) * (1 + dd_trigger / 100.0)
    dist = (
        "n.v.t."
        if trigger_price is None
        else f"Crashniveau ligt op ${trigger_price:,.2f} (= -30% vanaf 52w high van ${float(high):,.2f}); "
        f"dat is nog {(float(price) / trigger_price - 1) * 100:+.1f}% verwijderd van de huidige koers"
    )
    return SignalStatus(
        key="kre",
        label=c["label"],
        status=status,
        value=float(price),
        value_text=_fmt(price, "USD"),
        detail=detail,
        distance_text=dist,
        extras={"drawdown_pct": dd, "high": high, "trigger_price": trigger_price,
                "floor": floor, "floor_enabled": floor_on},
    )


def status_credit(df: pd.DataFrame, cfg: Dict[str, Any]) -> SignalStatus:
    c = cfg["signals"]["credit_spread"]
    trigger, warn = float(c["trigger_level"]), float(c["warn_level"])
    value = _last_valid(df, "hy_oas")
    proxy = _last_valid(df, "hyg_agg_proxy")

    if value is None:
        status, detail = GREY, "Geen spreaddata beschikbaar."
    elif float(value) >= trigger:
        status = RED
        detail = f"OAS op {float(value):.2f}% - op of boven de stressdrempel van {trigger:.2f}%."
    elif float(value) >= warn:
        status = YELLOW
        detail = f"OAS op {float(value):.2f}% - in de waarschuwingszone vanaf {warn:.2f}%."
    else:
        status = GREEN
        detail = f"OAS op {float(value):.2f}% - ruim onder de waarschuwingsgrens van {warn:.2f}%."

    gap = None if value is None else trigger - float(value)
    return SignalStatus(
        key="credit_spread",
        label=c["label"],
        status=status,
        value=None if value is None else float(value),
        value_text=_fmt(value, "%"),
        detail=detail,
        distance_text=("n.v.t." if gap is None else f"{gap:+.2f} procentpunt tot de drempel van {trigger:.2f}%"),
        extras={"proxy": None if proxy is None or pd.isna(proxy) else float(proxy)},
    )


def all_statuses(df: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, SignalStatus]:
    return {
        "ust10y": status_ust10y(df, cfg),
        "kre": status_kre(df, cfg),
        "credit_spread": status_credit(df, cfg),
    }


def overall_status(statuses: Dict[str, SignalStatus]) -> str:
    if not statuses:
        return GREY
    return max((s.status for s in statuses.values()), key=lambda x: _ORDER[x])


def overall_message(statuses: Dict[str, SignalStatus]) -> str:
    worst = overall_status(statuses)
    reds = [s.label for s in statuses.values() if s.status == RED]
    yellows = [s.label for s in statuses.values() if s.status == YELLOW]
    if worst == RED:
        return "NIET RUSTIG - trigger actief: " + "; ".join(reds)
    if worst == YELLOW:
        return "WAAKZAAM - in de waarschuwingszone: " + "; ".join(yellows)
    if worst == GREEN:
        return "RUSTIG - alle drie de signalen staan groen, geen enkele drempel is geraakt."
    return "Onvoldoende data om een oordeel te vellen."
