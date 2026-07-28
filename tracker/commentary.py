"""Vaste duidingsteksten per signaal (Druckenmiller-raamwerk).

De teksten zijn bewust statisch: ze beschrijven de logica, niet de actuele stand.
De actuele stand komt uit signals.py zodat er nooit een cijfer 'verzonnen' wordt.
"""

UST10Y = """
**Waarom volgen we dit op?**
Druckenmiller kijkt in de eerste plaats naar liquiditeit en naar de prijs van geld, niet naar
bedrijfswinsten. De 10-jaarsrente is de risicovrije discontovoet voor zowat elke andere
activaklasse: als die stijgt, daalt de contante waarde van toekomstige kasstromen, verzwaart de
herfinanciering van de Amerikaanse staatsschuld en verliezen de lange obligaties op bankbalansen
marktwaarde. Hij heeft zijn portefeuille de voorbije jaren expliciet gepositioneerd tegen langlopend
Amerikaans staatspapier, precies omdat hij verwacht dat de combinatie van hoge tekorten en een
te soepele Fed de lange rente omhoog duwt ([Reuters/The Financial Wire](https://www.newsbreak.com/the-financial-wire-382710013/4769734113822-stanley-druckenmiller-is-betting-against-u-s-treasury-bonds-wagering-the-fed-reignites-inflation)).

**Wat betekent stijgen of dalen?**
- *Oplopend:* strakkere financiele condities. De obligatiemarkt eist een hogere termijnpremie, meestal
  omdat ze inflatie, een te groot begrotingstekort of een verlies aan geloofwaardigheid van de Fed
  inprijst. Dat is het gevaarlijke soort rentestijging: aandelen en obligaties dalen dan samen.
- *Dalend:* ofwel verzachting van de inflatiedruk (gunstig), ofwel een vlucht naar veiligheid omdat de
  groei instort (ongunstig). De richting alleen volstaat dus niet - lees ze samen met signaal 2 en 3.

**Waarom ligt de drempel op 5% gedurende 3 opeenvolgende dagen?**
5% is het niveau waarop de rente in de vorige cyclus telkens is afgeketst: de 10-jaarsrente piekte op
4,98% op 19 oktober 2023 en heeft sinds 2007 geen enkele handelsdag boven 5,00% gesloten
([FRED, reeks DGS10](https://fred.stlouisfed.org/series/DGS10)). Een breuk boven dat niveau is dus geen
gewone beweging maar een regimewissel. De eis van drie opeenvolgende dagen filtert intradag-ruis,
veilingongelukjes en eendaagse uitschieters weg: pas als de markt het niveau drie dagen op rij
vasthoudt, gaat het om een aanvaard nieuw prijsniveau en niet om een technische piek.

**Uitzonderingen en beperkingen**
- Een hogere rente die volledig gedreven wordt door sterkere reele groei (stijgende reele rente met
  stabiele of dalende inflatieverwachtingen) is historisch niet bearish voor risicoactiva. De drempel
  vangt het niveau, niet de oorzaak - controleer altijd of het om een termijnpremie- of een groeischok gaat.
- Het signaal is gebaseerd op dagelijkse *slotkoersen* van FRED. Intradag is de rente in oktober 2023
  wel degelijk kort boven 5% gegaan zonder dat de slotkoers dat bevestigde; zo'n dag telt hier niet mee.
- De reeks kent gaten op Amerikaanse feestdagen. "Opeenvolgende dagen" betekent opeenvolgende
  *handelsdagen*, niet kalenderdagen.
"""

KRE = """
**Waarom volgen we dit op?**
De regionale banken zijn in dit raamwerk het transmissiekanaal tussen hoge rente en de reele economie.
Druckenmiller wees er na de val van SVB expliciet op dat de mediane regionale bank ongeveer 43% van
haar kredietportefeuille in commercieel vastgoed heeft zitten, waarvan ongeveer 40% kantoren, en dat
SVB "waarschijnlijk het topje van de ijsberg" was
([Fortune/Yahoo Finance](https://finance.yahoo.com/news/billionaire-investor-stanley-druckenmiller-warns-200255702.html),
[GuruFocus - Sohn 2023](https://www.gurufocus.com/news/2011956/stanley-druckenmiller-notes-from-the-may-2023-sohn-conference)).
KRE is de meest liquide manier om die stress in realtime af te lezen: de ETF prijst de gepercipieerde
solvabiliteit van dat deel van het banksysteem elke seconde opnieuw.

**Wat betekent stijgen of dalen?**
- *Dalend:* de markt prijst kredietverliezen, deposito-uitstroom of kapitaalbehoefte in. Banken
  reageren daarop door minder krediet te verstrekken - de kredietimpuls valt weg voordat het in de
  officiele economische cijfers zichtbaar is. Een scherpe daling is dus een vooruitlopende indicator.
- *Stijgend:* vertrouwen in bankbalansen, doorgaans samen met een steilere rentecurve (betere
  netto-rentemarge) of verwachte deregulering. Dat wijst op een gezonde kredietverstrekking.

**Waarom ligt de drempel op -30%?**
-30% is geen gewone correctie meer: het is het niveau waarop de markt niet langer lagere winsten
maar mogelijke insolventie inprijst. Ter kalibratie: tijdens de regionalebankencrisis van maart 2023
verloor KRE binnen enkele weken ruim een derde van zijn waarde. De drempel wordt in deze tracker
*relatief* berekend, tegenover het rollende 52-weeks hoogtepunt, zodat hij automatisch meebeweegt met
de koers en dus jaren later nog altijd hetzelfde betekent.

**Belangrijke correctie op de oorspronkelijke drempel**
De oorspronkelijk opgegeven vloer van $31,50 ging uit van een koers van ongeveer $45. KRE noteert
intussen aanzienlijk hoger, waardoor die absolute vloer overeenkomt met een veel diepere daling dan de
bedoelde -30%. De vaste vloer staat daarom standaard uitgeschakeld (wel zichtbaar als paarse lijn in de
grafiek) en de statuslogica gebruikt de relatieve -30%-regel. Je kan de vaste vloer terug activeren via
`absolute_floor_enabled: true` in `config.yaml`.

**Uitzonderingen en beperkingen**
- KRE is een gelijkgewogen ETF met een beperkt aantal namen. Een idiosyncratisch probleem bij een of
  twee grote leden kan de index bewegen zonder dat er systeemrisico is. Kijk in dat geval of de daling
  breed gedragen is.
- Fusies, kapitaalverhogingen en de jaarlijkse herweging veranderen de samenstelling. Een sprong in de
  koers is niet altijd een marktoordeel.
- Sinds de invoering van de Fed-faciliteiten in 2023 kan een liquiditeitsprobleem sneller worden
  afgedekt dan vroeger. De ETF kan dus dalen zonder dat er effectief bankfalingen volgen; het signaal
  meet gepercipieerd risico, geen uitkomst.
"""

CREDIT = """
**Waarom volgen we dit op?**
Kredietmarkten breken bijna altijd voor aandelenmarkten. De high yield option-adjusted spread (OAS) is
de extra vergoeding die beleggers eisen boven staatspapier om bedrijfsrisico te dragen; het is de
zuiverste marktprijs van wanbetalingsrisico en van de bereidheid om risico te financieren. In het
Druckenmiller-raamwerk sluit dit signaal de keten: dure financiering (signaal 1) plus een krimpend
bankkanaal (signaal 2) leidt tot herfinancieringsproblemen, en die worden hier zichtbaar voordat ze in
winstcijfers opduiken.

**Wat betekent stijgen of dalen?**
- *Oplopend:* beleggers eisen meer compensatie, de herfinancieringsmarkt sluit voor de zwakste
  emittenten en de kans op een wanbetalingsgolf stijgt. Een snelle verwijding is belangrijker dan het
  absolute niveau: het tempo verraadt of het om herprijzing of om paniek gaat.
- *Dalend/krap:* overvloedige liquiditeit en risicobereidheid. Erg krappe spreads zijn comfortabel op
  korte termijn, maar betekenen ook dat de markt weinig buffer heeft voor tegenvallers.

**Waarom ligt de drempel op 6%?**
6% ligt net boven de piek van de vorige verkrappingscyclus: in juli 2022 topte de high yield spread rond
583-600 basispunten zonder dat er een recessie volgde
([MUFG](https://www.mufgamericas.com/sites/default/files/document/2022-08/chart-of-the-day-8-2-hy-spreads-and-yields-tightened-in-july-to-well-below-recession-thresholds.pdf),
[NAIC](https://content.naic.org/sites/default/files/capital-markets-special-reports-ye2022-markets-wrap-up.pdf)).
Alles daarboven is historisch pas voorgekomen in echte stressepisodes: 1.087 bp in maart 2020
([CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2025/think-weve-seen-the-last-1000-bps-high-yield-spread-think-again))
en meer dan 21% in december 2008. Een OAS van 6% markeert dus de grens tussen "duurder krediet" en
"gesloten kredietmarkt". De waarschuwingsgrens op 4,5% komt overeen met de recentste stresspieken
zonder recessie: 4,53% in oktober 2023 en 4,61% op 7 april 2025 tijdens de tariefschok
([FRED, reeks BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)).

**Over HYG vs AGG**
De oorspronkelijke vraag was om de spread af te leiden uit HYG tegenover AGG. Die twee ETF's leveren
geen echte spread op: AGG is geen staatspapierbenchmark maar een brede aggregaatindex met een andere
looptijd en kredietmix, en beide fondsen publiceren geen historische OAS. De tracker gebruikt daarom de
officiele ICE BofA US High Yield OAS van FRED als hoofdreeks - exact de reeks waar de 6%-drempel op
geijkt is - en toont het TTM-yieldverschil tussen HYG en AGG als stippellijn ter kruispeiling. Die proxy
ligt structureel lager dan de OAS en telt niet mee in de statusbepaling.

**Uitzonderingen en beperkingen**
- Spreads kunnen mechanisch verwijden wanneer de onderliggende staatsrente scherp *daalt* in een
  vlucht naar veiligheid, zonder dat het kredietrisico zelf verslechtert.
- De samenstelling van de high yield index is de voorbije jaren kwalitatief verbeterd (meer BB, minder
  CCC). Bij gelijk economisch risico noteert de index daardoor structureel krapper dan vroeger, wat de
  6%-drempel vandaag strenger maakt dan tien jaar geleden.
- De OAS wordt eenmaal per handelsdag gepubliceerd en verschijnt met een dag vertraging op FRED. In een
  snel bewegende markt loopt dit signaal dus een dag achter op de aandelenmarkt.
"""

CROSS_SIGNAL = """
**Hoe lees je de drie signalen samen?**
De volgorde is niet toevallig: rente (prijs van geld) leidt tot bankstress (aanbod van krediet) leidt tot
kredietstress (prijs van krediet). Een enkel rood signaal is een waarschuwing; twee tegelijk betekent dat
het mechanisme effectief doorwerkt. Wanneer alle drie tegelijk rood staan gaat het niet meer om een
correctie maar om een systeemgebeurtenis. Omgekeerd: zolang de kredietspreads krap blijven, is een
scherpe daling van bankaandelen historisch vaker een sectorprobleem dan het begin van een crisis.
"""

TEXTS = {
    "ust10y": UST10Y,
    "kre": KRE,
    "credit_spread": CREDIT,
}
