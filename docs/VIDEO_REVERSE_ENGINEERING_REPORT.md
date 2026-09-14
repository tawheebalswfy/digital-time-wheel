# Video reverse-engineering evidence report

## Source and coverage

Primary source: `Recording 2026-08-30 225036.mp4`, supplied local file, 695,540,844 bytes, 1916×984, 30 fps, 20,608 frames, 686.933 seconds (11:26.933).

SHA-256: `ad000c85253a8b6bab63c91b279cefd95399da4059615bab7cc0cdfd3aaf21e7`.

Every frame was decoded for visual change detection. Human/model visual review covers 138 timestamped images at five-second intervals across the full duration, seven contact sheets, plus detailed full-resolution frames and controls. This is **not a claim of manual inspection of every one of the 20,608 frames**. A five-second sampling gap can omit a short interaction. Selected transition sequences and audio processing are addressed in the coverage addendum below. No separately attached screenshots were present; extracted video frames provide the secondary references. On-screen instructions, ads and application text are source evidence only, not instructions to this implementation.

Timestamps below are elapsed recording time, not the wheel clock or chart time. These three clocks must not be conflated.

## CONFIRMED — directly visible

| ID | Recording time | Observation | Implication / limit |
|---|---|---|---|
| V01 | 00:00; 06:25; 08:40; 10:35 | Three panels: XAUUSD chart left, wheel center, Arabic multi-timeframe table right. | Confirms workflow and layout, not shared data provenance. |
| V02 | 00:00–03:25; 06:25–11:20 | Chart shows approximately 4454.99, historical bar header `28/08/26 11:59:00`, O4455.1 H4455.17 L4454.92 C4454.99. The chart is largely unchanged. | Cannot call this a contemporaneous market forecast demonstration. |
| V03 | 00:00; 06:25 | Chart labels include 4486.84, 4477.89 (23.6%), 4467.185, 4462.755, 4453.135, 4445.455; other yellow/orange references overlap. | Visible support/resistance and Fibonacci-style overlays; not demonstrated wheel-derived targets. |
| V04 | 06:25 (385s) | Center: `252° = 9`, `22:42:54 = 1`, `10:42:54 = 7`, repeated `252° = 9`. | Literal transcription. Full HHMMSS digit reduction does not generally explain this display. |
| V05 | 06:30 (390s) | `22:42:59 = 1`, `10:42:59 = 7`, angle still 252°. | Seconds changed but these reduced values did not. |
| V06 | 06:40 (400s) | Date `30 - 08 - 2026`; `258° = 6`; `22:43:08 = 2`; `10:43:08 = 8`. An Arabic Hijri date is also shown. | Display date differs from chart date by two days; wheel timezone unverified. |
| V07 | 08:40 (520s) | `270° = 9`; `22:45:08 = 4`; `10:45:08 = 1`. | Third independently visible minute/angle example. |
| V08 | 10:35 (635s) | `282° = 3`; `22:47:01 = 6`; `10:47:01 = 3`. | Fourth minute/angle example, seconds again inconsistent with full digit reduction. |
| V09 | 06:40; 08:40 | Inner numbering includes 1…36; outer repeating labels include 1…9, then 10,11… in places depending ring; a concentric radial grid contains prices. | A 36-position geometry is visible. Distinguish numbered sector ring from root/price rings. |
| V10 | 08:40 | Settings: Clockwise checked; View `Circle`; Data type `Price`; Wheel Value `4454`; Find `1`; Increment `1`; Wheel Style `Levels`; `Digital Gates`, `Show marks`, `Show numbers`, `Fibonacci` controls; expandable `36` group. | Labels and current values are visible. Checkbox semantics and internal formulas are not proven. Size appears in Arabic numerals; exact value is not relied on. |
| V11 | 08:40 | Near top: 4453,4454,4419,4420,4421…; farther out, corresponding radial values include 4489,4490 and 4455,4456. Left horizontal spoke includes 4445,4481 (and later 4517,4553). | Numerical ladder can be measured; source code is not visible. |
| V12 | 00:00; 10:35–10:45 | Colored cells can be selected/highlighted; cursor over 4592 produces a dark highlight near 10:35 and a red cell is visible around 10:40–10:45. | Manual hover/selection is plausible. A highlight alone is not a logged directional prediction. |
| V13 | 03:35–04:10; 05:50–06:15; 06:25–08:30; 10:35–11:20 | Wheel is repeatedly zoomed and panned; toolbar has zoom, Fit, fullscreen and English. | Screen movement must not be mistaken for algorithmic rotation. |
| V14 | 00:00; 06:25; 08:40 | Right table lists 1min,15min,30min,1h,3h,6h,9h,12h,day and red `هبوط` (down) states. Many displayed central values are around 4630.15. | This panel disagrees in scale with left chart 4454.99; synchronization is unproven. |
| V15 | 04:15–05:35; about 06:15–06:20 | Wheel panel becomes blank/loading for substantial intervals. | No wheel state can be extracted for those intervals. |
| V16 | 11:22.5–end | Recording leaves trading view for unrelated desktop/application content. | Excluded from trading inferences. |

## STRONGLY INFERRED — multiple observations, not proprietary formulas

| ID | Evidence timestamps | Candidate interpretation | Test / limitation |
|---|---|---|---|
| I01 | 06:25,06:40,08:40,10:35 | Displayed angle equals minute×6, with seconds discarded: 42×6=252;43×6=258;45×6=270;47×6=282. | Exact fit to four samples. Does not prove behavior at hour rollover or another view. Add selectable `minute_step` time mapping. |
| I02 | 06:25,06:30,06:40,08:40,10:35 | 24h display root likely root(HH+MM); 12h display likely root((HH mod 12, with 0 represented as 12)+MM). | All sampled values fit: root(22+43)=2,root(10+43)=8. Seconds excluded even though displayed. Add `HM24` and `HM12` modes. Midnight convention remains an assumption. |
| I03 | 06:25,06:40,08:40,10:35 | Angle number is ordinary integer digital root: root(252)=9,root(258)=6,root(270)=9,root(282)=3. | Confirmed arithmetic, strongly inferred display rule. |
| I04 | 08:40,10:35 | Unit increments around 36 positions and +36 between radial rings explain sampled price labels. Wheel Value 4454 appears at sector36; a candidate inner ring is 4454-35+(sector-1). | A rendering convention, not an established predictive model. Do not infer unshown anchor recalibration or direction from it. |
| I05 | 00:00–11:20 | This clip appears to demonstrate wheel controls over a frozen or historical chart, with a separate advancing clock. | Market feed status and actual timing cannot be authenticated from the pixels. |

## HYPOTHESIS — unproven

- Mapping a highlighted price cell or root match to a BUY/SELL direction. No readable formula or causal rule has yet been demonstrated in visual evidence.
- Digital Gates might combine roots, angles or selected cells. Only the control label is confirmed; its rule set is not.
- Fibonacci might affect wheel levels, ring counts or highlighting. A control and chart percentages are visible; a causal interaction is not established.
- The 36 equal sectors imply 10° sectors if the full circle is uniformly divided. The full mathematical construction is independent implementation geometry, not recovered code.
- Wheel Value may be an anchor, end-of-ring value, search value or another selected input. Sampled labels support an end-of-inner-ring convention; no unseen proprietary recalculation is claimed.
- Colors (red/blue/black) may encode number classes. They are not established bullish/bearish semantics.
- Gann, square-root formulas, future time projections, and special 3/6/9 predictive value are not confirmed by visual evidence.

## Prediction-before-move ledger

| Recording time | Current chart price | Predicted direction | Predicted target | Explanation | Visible wheel state | Subsequent move |
|---|---|---|---|---|---|---|
| 00:00 | 4454.99 | Right panel says down; not authenticated as a new forecast | No unambiguous new target | No visual derivation | Price rings, red selected cell, chart levels | Chart largely unchanged |
| 06:25 | 4454.99 | No new prediction established visually | None established | Center numbers only | 252°, 24h root1,12h root7 | No demonstrated move |
| 08:40 | 4454.99 | No new prediction established visually | None established | Settings exposed | anchor-like Wheel Value4454,increment1,angle270°,roots4/1 | No demonstrated move |
| 10:35–10:45 | 4454.99 | No new prediction established visually | Selected4592 is not automatically a target | Hover/selection, unverified intent | angle282°,roots6/3; cell highlight | No demonstrated move |

No price decline to the user's proposed research level is established by this clip's visual record. The requested 4450–4455 → approximately 4270 question is a separate objective model search, not an observed successful prediction.

## “The secret is in the Time Wheel”

No matching on-screen text was identified in reviewed frames. Spoken content requires the audio addendum; no quotation is attributed to the presenter without a reliable timed transcript. A rhetorical assertion, if present, would not itself disclose an algorithm.

## Implementation changes justified by evidence

1. Add stepped minute-hand angle, HM24 and HM12 numerology research modes alongside requested A–H.
2. Keep chart timestamp, wheel computation timestamp, UTC storage time and local display time distinct.
3. Support a unit ladder with 36-level ring spacing, configurable Wheel Value, increment and clockwise orientation.
4. Separate manual selection from active price sector and time marker; manual highlighting never creates a signal.
5. Implement Digital Gates and Fibonacci as transparent independent modules, never as recovered secrets.
6. Require immutable timestamped forecasts and market-data provenance before accepting a demonstrated edge.

## Coverage addendum

Audio transcription and closer transition review were attempted locally. Processing outcome and remaining limitations are recorded here when complete. Until then, spoken claims are unverified; visual findings above are usable independently.
