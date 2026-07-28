"""Streamlit-dashboard: Market Stability Tracker (Druckenmiller-signalen).

Start lokaal met:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from tracker.charts import chart_credit, chart_kre, chart_kre_drawdown, chart_ust10y
from tracker.commentary import CROSS_SIGNAL, TEXTS
from tracker.config import history_path, load_config
from tracker.datasources import build_weekly_frame
from tracker.history import load_history, merge_rows, save_history, to_timeseries
from tracker.signals import COLOR_HEX, LEGEND, all_statuses, overall_message, overall_status

st.set_page_config(page_title="Market Stability Tracker", page_icon="📉", layout="wide")

cfg = load_config()
HIST = history_path(cfg)


# ---------------------------------------------------------------------------
# Header + updateknop
# ---------------------------------------------------------------------------
st.title("Market Stability Tracker")
st.caption(
    "Drie marktbrede stresssignalen volgens het Druckenmiller-raamwerk: de prijs van geld, "
    "het bankkanaal en de prijs van krediet. Weekfrequentie, historiek blijft altijd bewaard."
)

col_a, col_b, col_c = st.columns([1.1, 1.1, 3])
with col_a:
    do_update = st.button("Update - haal de recentste waarden op", type="primary", width="stretch")
with col_b:
    do_backfill = st.button("Historiek 1 jaar (her)opbouwen", width="stretch")

status_box = st.empty()

if do_update or do_backfill:
    with st.spinner("Data ophalen bij FRED en Yahoo Finance..."):
        try:
            if do_backfill:
                years = float(cfg.get("history_years", 1))
                start = dt.date.today() - dt.timedelta(days=int(365 * years) + 7)
            else:
                start = dt.date.today() - dt.timedelta(days=21)
            new_rows = build_weekly_frame(cfg, start=start)
            merged = merge_rows(load_history(HIST), new_rows)
            save_history(merged, HIST)
            status_box.success(
                f"Bijgewerkt op {dt.datetime.now():%d-%m-%Y %H:%M}. "
                f"{len(new_rows)} week(en) verwerkt, totale historiek: {len(merged)} weken. "
                "Bestaande datapunten bleven behouden."
            )
        except Exception as exc:  # noqa: BLE001
            status_box.error(f"Update mislukt: {exc}. De bestaande historiek is ongewijzigd.")

raw = load_history(HIST)
if raw.empty:
    st.warning("Nog geen historiek. Klik op 'Historiek 1 jaar (her)opbouwen' om te starten.")
    st.stop()

df = to_timeseries(raw)
statuses = all_statuses(df, cfg)
worst = overall_status(statuses)

# ---------------------------------------------------------------------------
# Statusoverzicht
# ---------------------------------------------------------------------------
st.markdown("## Statusoverzicht")
banner = {"GROEN": "success", "GEEL": "warning", "ROOD": "error"}.get(worst, "info")
getattr(st, banner)(overall_message(statuses))

last = df.iloc[-1]
st.caption(
    f"Laatste week in de tracker: {pd.to_datetime(last['week_end']):%d-%m-%Y} "
    f"(data t.e.m. {last['as_of']}) - {len(df)} weken historiek - "
    f"laatst bijgewerkt: {last['updated_at']}"
)

cols = st.columns(3)
for col, key in zip(cols, ["ust10y", "kre", "credit_spread"]):
    s = statuses[key]
    with col:
        st.markdown(
            f"""
            <div style="border:1px solid #e3e3e3;border-radius:10px;padding:14px 16px;">
              <div style="font-size:0.85rem;color:#555;">{s.label}</div>
              <div style="font-size:1.9rem;font-weight:700;line-height:1.2;">{s.value_text}</div>
              <div style="display:inline-block;margin-top:6px;padding:3px 12px;border-radius:12px;
                          background:{COLOR_HEX[s.status]};color:#fff;font-weight:700;font-size:0.8rem;">
                  {s.status}
              </div>
              <div style="margin-top:10px;font-size:0.85rem;color:#333;">{s.detail}</div>
              <div style="margin-top:6px;font-size:0.8rem;color:#666;">{s.distance_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Legende kleurcodes"):
            for lvl in ("GROEN", "GEEL", "ROOD"):
                st.markdown(
                    f"<span style='display:inline-block;width:11px;height:11px;border-radius:50%;"
                    f"background:{COLOR_HEX[lvl]};margin-right:7px;'></span>"
                    f"<b>{lvl}</b> - {LEGEND[key][lvl]}",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"<span style='display:inline-block;width:11px;height:11px;border-radius:50%;"
                f"background:{COLOR_HEX['GEEN DATA']};margin-right:7px;'></span>"
                "<b>GEEN DATA</b> - geen observatie beschikbaar voor die week.",
                unsafe_allow_html=True,
            )

st.divider()

# ---------------------------------------------------------------------------
# Grafieken + duiding
# ---------------------------------------------------------------------------
st.plotly_chart(chart_ust10y(df, cfg), width="stretch")
st.markdown(TEXTS["ust10y"])
st.divider()

st.plotly_chart(chart_kre(df, cfg), width="stretch")
st.plotly_chart(chart_kre_drawdown(df, cfg), width="stretch")
st.markdown(TEXTS["kre"])
st.divider()

st.plotly_chart(chart_credit(df, cfg), width="stretch")
st.markdown(TEXTS["credit_spread"])
st.divider()

st.markdown("## Samenhang tussen de drie signalen")
st.markdown(CROSS_SIGNAL)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
with st.expander("Onderliggende data (weekhistoriek)"):
    st.dataframe(raw.sort_values("week_end", ascending=False), width="stretch", height=420)
    st.download_button(
        "Download historiek als CSV",
        raw.to_csv(index=False).encode("utf-8"),
        file_name="market_stability_history.csv",
        mime="text/csv",
    )

st.caption(
    "Bronnen: 10-jaarsrente en high yield OAS via FRED (reeksen DGS10 en BAMLH0A0HYM2), "
    "KRE/HYG/AGG via Yahoo Finance. Alle waarden worden rechtstreeks opgehaald; er worden geen "
    "waarden geschat of geinterpoleerd. Dit is geen beleggingsadvies."
)
