# Market Stability Tracker

Wekelijkse tracker van drie marktbrede stresssignalen volgens het macroraamwerk van
Stanley Druckenmiller: **de prijs van geld**, **het bankkanaal** en **de prijs van krediet**.

De tracker is een Streamlit-app met een **Update-knop**: elke klik haalt de meest recente
waarden op, voegt ze als nieuw weekdatapunt toe aan `data/history.csv` en laat alle eerdere
datapunten ongemoeid. De historiek groeit dus permanent aan.

---

## De drie signalen

| # | Signaal | Reeks | Waarschuwing (geel) | Trigger (rood) |
|---|---------|-------|---------------------|----------------|
| 1 | 10-jaars US Treasury yield | FRED `DGS10` | >= 4,75% | 3 opeenvolgende handelsdagen boven 5,00% |
| 2 | Regionale banken (KRE) | Yahoo Finance `KRE` | -15% t.o.v. 52-weeks hoogtepunt | -30% t.o.v. 52-weeks hoogtepunt |
| 3 | High yield credit spread | FRED `BAMLH0A0HYM2` | >= 4,50% | >= 6,00% |

Kleurlegende (identiek voor alle drie):

| Kleur | Betekenis |
|-------|-----------|
| 🟢 GROEN | Rustig - de parameter zit ruim aan de veilige kant van de drempel. |
| 🟡 GEEL | Waakzaam - waarschuwingsgrens geraakt, triggervoorwaarde nog niet vervuld. |
| 🔴 ROOD | Trigger - niveau **en** eventuele tijdsvoorwaarde zijn vervuld. |
| ⚪ GEEN DATA | Geen observatie beschikbaar voor die week. |

De globale status is altijd de slechtste van de drie afzonderlijke statussen.

### Twee bewuste afwijkingen van de oorspronkelijke specificatie

1. **KRE-drempel.** De opgegeven vloer van $31,50 ging uit van een koers rond $45. KRE noteert
   intussen aanzienlijk hoger, waardoor die vaste vloer een veel diepere daling dan -30% zou
   vereisen. De statuslogica gebruikt daarom de **relatieve** -30%-regel tegenover het rollende
   52-weeks hoogtepunt. De vaste vloer blijft zichtbaar in de grafiek en kan worden geactiveerd via
   `absolute_floor_enabled: true` in `config.yaml`.
2. **Credit spread.** HYG versus AGG levert geen echte kredietspread op (AGG is geen
   staatspapierbenchmark en beide ETF's publiceren geen historische OAS). De hoofdreeks is daarom de
   officiele **ICE BofA US High Yield OAS** van FRED - de reeks waarop de 6%-drempel geijkt is. Het
   TTM-yieldverschil tussen HYG en AGG wordt als stippellijn getoond ter kruispeiling en telt niet
   mee in de statusbepaling.

---

## Installatie

```bash
git clone <jouw-repo-url>
cd market-stability-tracker
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

De app draait op http://localhost:8501.

## Gebruik

- **Update - haal de recentste waarden op**: haalt de laatste weken op en werkt de historiek bij.
  Bestaande weken worden nooit verwijderd; enkel de lopende week wordt verfijnd tot ze afgesloten is.
- **Historiek 1 jaar (her)opbouwen**: bouwt de volledige jaarhistoriek opnieuw op.
- Onderaan kan je de volledige weekhistoriek bekijken en als CSV downloaden.

Zonder interface kan het ook via de command line:

```bash
python scripts/update.py             # laatste weken bijwerken
python scripts/update.py --weeks 8   # laatste 8 weken herberekenen
python scripts/update.py --backfill  # volledige jaarhistoriek opbouwen
```

## Automatische wekelijkse update

`.github/workflows/weekly-update.yml` draait elke zaterdag om 07:00 UTC, werkt `data/history.csv`
bij en commit het resultaat terug naar de repo. Je kan de workflow ook manueel starten via
**Actions -> Weekly tracker update -> Run workflow**. Zet in **Settings -> Actions -> General**
de workflowrechten op *Read and write permissions*.

## Structuur

```
app.py                      Streamlit-dashboard (updateknop, grafieken, duiding)
config.yaml                 Alle drempels en instellingen
data/history.csv            Weekhistoriek - groeit aan, wordt nooit overschreven
tracker/datasources.py      Ophalen bij FRED en Yahoo Finance + weekaggregatie
tracker/history.py          Laden, samenvoegen en bewaren van de historiek
tracker/signals.py          Statuslogica en kleurcodes
tracker/charts.py           Plotly-grafieken met drempellijnen en datumlabels
tracker/commentary.py       Duidingsteksten per signaal
scripts/update.py           CLI-update (ook gebruikt door GitHub Actions)
tests/test_signals.py       Tests op de statuslogica (geen netwerk nodig)
```

## Databronnen

- 10-jaarsrente: [FRED DGS10](https://fred.stlouisfed.org/series/DGS10)
- High yield OAS: [FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)
- KRE, HYG, AGG: Yahoo Finance via `yfinance`

Alle waarden worden rechtstreeks bij de bron opgehaald. Er wordt niets geschat, gemodelleerd of
geinterpoleerd; ontbrekende observaties blijven leeg. De meegeleverde `data/history.csv` bevat
echte, opgehaalde weekdata over de voorbije 12 maanden.

## Tests

```bash
pytest -q
```

## Disclaimer

Dit is een monitoringinstrument, geen beleggingsadvies. De drempels zijn kalibraties op basis van
historische episodes en geen voorspellingen.
