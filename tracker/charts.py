"""Plotly-grafieken met leesbare datumlabels en zichtbare drempels."""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go

LINE = "#1f4e79"
RED = "#d7191c"
AMBER = "#e8a317"
GREY = "#8c8c8c"

_LAYOUT = dict(
    template="plotly_white",
    height=430,
    margin=dict(l=60, r=30, t=60, b=50),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)


def _date_axis(fig: go.Figure) -> go.Figure:
    """Max ~8 goed leesbare datumlabels op de X-as."""
    fig.update_xaxes(
        nticks=8,
        tickformat="%d %b %y",
        tickangle=0,
        showgrid=True,
        gridcolor="#eeeeee",
        title_text="Week (vrijdagclose)",
    )
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")
    return fig


def chart_ust10y(df: pd.DataFrame, cfg: Dict[str, Any]) -> go.Figure:
    c = cfg["signals"]["ust10y"]
    trigger, warn = float(c["trigger_level"]), float(c["warn_level"])
    d = df.dropna(subset=["ust10y_close"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=d["week_end"], y=d["ust10y_close"], name="10y yield (weekclose)",
            mode="lines+markers", line=dict(color=LINE, width=2.2), marker=dict(size=4),
        )
    )
    hit = d[d["ust10y_max_consec_days_above_trigger"].fillna(0) >= int(c["trigger_consecutive_days"])]
    if not hit.empty:
        fig.add_trace(
            go.Scatter(x=hit["week_end"], y=hit["ust10y_close"], name="Trigger vervuld (3 dagen >5%)",
                       mode="markers", marker=dict(color=RED, size=11, symbol="x")),
        )
    fig.add_hline(y=trigger, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"Trigger {trigger:.2f}% (3 dagen op rij)", annotation_position="top left")
    fig.add_hline(y=warn, line=dict(color=AMBER, width=1.6, dash="dot"),
                  annotation_text=f"Waarschuwing {warn:.2f}%", annotation_position="bottom left")
    fig.update_layout(title="1. 10-jaars US Treasury yield", yaxis_title="Yield (%)", **_LAYOUT)
    return _date_axis(fig)


def chart_kre(df: pd.DataFrame, cfg: Dict[str, Any]) -> go.Figure:
    c = cfg["signals"]["kre"]
    d = df.dropna(subset=["kre_close"]).copy()
    dd_trigger = float(c["drawdown_trigger_pct"]) / 100.0
    dd_warn = float(c["drawdown_warn_pct"]) / 100.0
    d["crash_line"] = d["kre_52w_high"] * (1 + dd_trigger)
    d["warn_line"] = d["kre_52w_high"] * (1 + dd_warn)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["kre_52w_high"], name="52-weeks hoogtepunt",
                             mode="lines", line=dict(color=GREY, width=1.2, dash="dot")))
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["warn_line"], name="Waarschuwing (-15% vs 52w high)",
                             mode="lines", line=dict(color=AMBER, width=1.6, dash="dot")))
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["crash_line"], name="Crashdrempel (-30% vs 52w high)",
                             mode="lines", line=dict(color=RED, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["kre_close"], name="KRE slotkoers",
                             mode="lines+markers", line=dict(color=LINE, width=2.2), marker=dict(size=4)))
    floor = float(c["absolute_floor"])
    fig.add_hline(y=floor, line=dict(color="#7b3294", width=1.4, dash="dashdot"),
                  annotation_text=f"Absolute vloer ${floor:.2f} (legacy)", annotation_position="bottom right")
    fig.update_layout(title="2. KRE - regionale banken", yaxis_title="Koers (USD)", **_LAYOUT)
    return _date_axis(fig)


def chart_kre_drawdown(df: pd.DataFrame, cfg: Dict[str, Any]) -> go.Figure:
    c = cfg["signals"]["kre"]
    d = df.dropna(subset=["kre_drawdown_pct"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["kre_drawdown_pct"], name="Drawdown vs 52w high",
                             mode="lines+markers", line=dict(color=LINE, width=2), marker=dict(size=4),
                             fill="tozeroy", fillcolor="rgba(31,78,121,0.10)"))
    fig.add_hline(y=float(c["drawdown_warn_pct"]), line=dict(color=AMBER, width=1.6, dash="dot"),
                  annotation_text="-15% waarschuwing", annotation_position="bottom left")
    fig.add_hline(y=float(c["drawdown_trigger_pct"]), line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="-30% crashdrempel", annotation_position="bottom left")
    layout = dict(_LAYOUT)
    layout["height"] = 320
    fig.update_layout(title="2b. KRE drawdown t.o.v. 52-weeks hoogtepunt", yaxis_title="Drawdown (%)", **layout)
    return _date_axis(fig)


def chart_credit(df: pd.DataFrame, cfg: Dict[str, Any]) -> go.Figure:
    c = cfg["signals"]["credit_spread"]
    trigger, warn = float(c["trigger_level"]), float(c["warn_level"])
    d = df.dropna(subset=["hy_oas"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["week_end"], y=d["hy_oas"], name="ICE BofA US High Yield OAS",
                             mode="lines+markers", line=dict(color=LINE, width=2.2), marker=dict(size=4)))
    p = df.dropna(subset=["hyg_agg_proxy"])
    if not p.empty:
        fig.add_trace(go.Scatter(x=p["week_end"], y=p["hyg_agg_proxy"],
                                 name="Proxy HYG-AGG (TTM yieldverschil)",
                                 mode="lines", line=dict(color="#6a9fb5", width=1.6, dash="dot")))
    fig.add_hline(y=trigger, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"Stressdrempel {trigger:.2f}%", annotation_position="top left")
    fig.add_hline(y=warn, line=dict(color=AMBER, width=1.6, dash="dot"),
                  annotation_text=f"Waarschuwing {warn:.2f}%", annotation_position="top left")
    fig.update_layout(title="3. Credit spreads (high yield)", yaxis_title="Spread (procentpunten)", **_LAYOUT)
    return _date_axis(fig)
