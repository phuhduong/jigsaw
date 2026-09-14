# Live verification progress

Recorded 2026-09-13, with continuation on 2026-09-14 UTC, from the named local run
JSON snapshots and focused-test execution notes. This is a diagnostic progress
record, not a frozen acceptance result.
**The fifteen earlier full-request attempts below did not establish a positive baseline.** No release-readiness,
free-tier quota, or engineering-reliability claim follows from these runs.

## BOM-only scope implementation and verification

### Current autonomous-completion goal (2026-09-14)

The user clarified that a manually guided/source-audited BOM does not satisfy the
goal. Acceptance requires a fresh original-query run, without a parent,
component choices or source-page instructions supplied by the developer, that
finishes compatibility checking and passes independent source review. Earlier
guided results remain diagnostics only. The first accepted fresh baseline is
prompt-18 run `149dc53304e146f584d6159366e663ee`, documented below. Earlier failures
remain recorded; one accepted case is not a measured reliability rate.

The reproduced recovery defect was repaired in prompt 11: corrections can request
source rereads by component ID, including omitted facts on already-interpreted
pages. Those requests go through scoped reading/extraction before assembly;
unaffected source state is retained for whole-BOM review. Mapping-only corrections
skip unnecessary engineering regeneration. Numeric failures now name the unusable
operand and source owners. Two-selected-endpoint I2C interfaces need both driving
directions, without numbered pins or per-wire duplication. Selected-product model
context no longer repeats offer/history data already represented in purchasing
totals; original technical parameters and saved records remain intact. Forty-five
short local backend tests and the two Python supplier-boundary tests passed.

Fresh `97089c678693480498be731554d0e351` used the original sensor query, prompt 11,
Flash-Lite/provider-default thinking, no parent and no modification. Outcome:
`finished / incomplete / partial`, input-budget stop at 138.65 seconds;
22 model calls, 283,695 input / 32,085 output tokens, 26 supplier calls, five
document attempts, 43 PDF page inputs and two corrections. Source rereading did
execute during correction and recovered previously omitted facts, but no final
assembly/review fit after those reads. It is not a successful automatic BOM.

Independent source review found actual remaining problems: 390 ohm +/-5% pull-ups
can violate the documented sensor minimum, and the AP2112K thermal allowance was
raised without a package/ambient justification. Signal operands were still missing
or misattributed. External MCU/sensor/regulator support parts were present, but
model use of `included` instead of `satisfied` created additional bookkeeping gaps.
Prompt 12 clarified the applicable source questions and support-status meaning,
and experimentally delayed full-source review until known numeric gaps were
repaired. No model switch, manual BOM rescue or budget increase was used.

Fresh `961fad1f491b4d48ad3bfc37ae06ffa5`, again the unchanged original query,
ended `finished / incomplete / partial` at the correction limit: 105.68 seconds,
18 calls, 192,343 input / 29,448 output tokens, 20 supplier calls, seven document
attempts, 19 PDF inputs and two corrections. Its optional local SSE recording is
`data/evaluations/prompt12-fresh-events.jsonl`. Initial extraction recovered the
MCU output limits, sensor logic levels, and regulator current/dropout/thermal
specifications. The selected 3.3 kohm +/-1% I2C pullups fixed the prior tolerance
problem, and automatic correction eventually represented both bus directions.
However, the recorded upstream current still mislabeled MCU current as regulator
input current, and external EN support was claimed fulfilled with no placements.
Independent review also found a thermal allowance computed without subtracting
ambient temperature and regulator output bounds missing load/line effects.

This trace falsified the numeric-first scheduling experiment: both corrections
were consumed without any source reviewer feedback, despite substantial input
budget remaining. Prompt 13 restores whole-BOM review before corrections, including
numeric gaps, and removes duplicate extracted PDF text from review only. Every
original PDF page and its label remains attached; HTML text and extraction/quote
verification are unchanged. Source-support and converter-input diagnostics now
identify the specific missing fulfillment or derived-current assumption. These
are workflow/record repairs, not permission to waive material compatibility checks.

Fresh prompt-13 run `144d0c45a45847eb88939e1bd4f0b6cc` reached a final current
whole-BOM review inside the unchanged budget: 128.47 seconds, 21 calls, 288,149
input / 30,725 output tokens, 23 supplier calls, seven document attempts, 47 PDF
inputs and two corrections. It selected all 15 placements / 11 MPNs with available
offers and a $9.61 saved subtotal. Result remained `finished / incomplete / available`.
Its sole code unknown was an empty interface citation list, although a current
signals review explicitly named that interface and cited both endpoints' evidence.
The original run is not retroactively reclassified or counted as success.

The independent audit also identified record claims requiring correction: the
sensor heater was inaccurately included in a sub-1 mA assumption, regulator
light-load initial output tolerance was treated as the full output envelope, and
a blanket capacitor-dielectric description misstated one selected part. The
actual support placements and pullups were suitable. Peak supply capacity and
separately declared average thermal load were now represented; the .462 W thermal
allowance correctly subtracted 40 C ambient from a 125 C junction target.

Prompt 14 accepts an explicit current source-backed signals review naming an
interface as alternative provenance, without requiring duplicate citations on
the interface record. Nonempty invalid citations, stale/uncited/generic reviews,
missing endpoints/configuration, signal directions and numeric failures still
cannot pass. Source-assisted review now requests concrete regulator/mode checks
instead of umbrella power approval. Fifty deterministic backend tests pass.

Fresh prompt-14 run `dfc40e2ded4544d6b73967bdf33d5a45` selected a different
documented regulator (AZ1117CH-3.3TRG1) and USB-C connector (USB4125-GF-A).
It ended `finished / incomplete / available`: 147.74 seconds, 22 calls, 287,075
input / 38,954 output tokens, 27 supplier calls, five document attempts, 50 PDF
inputs and one correction. A further correction did not fit the input reservation.
The final current review completed, but three receiver input-range records copied
source-rail values instead of the receivers' operating specifications.
The [independent audit](prompt14-sensor-audit.md) also found a material thermal
configuration contradiction: the stored 0.84 W scalar did not match its own
(125-55)/125 = 0.56 W assumption, and review prose mentioned alternative copper
conditions without adopting them consistently in the design. No previous run is
reclassified or manually repaired.

Prompt 15 gives receiving-device range fields explicit schema descriptions and
moves the demonstrated thermal arithmetic error into code. `RegulatorCheck`
records `ambient_max`, `junction_target`, and source-owned `theta_ja`; the checker
computes (target-ambient)/theta. Documented typical package thermal resistance is
allowed as a conditioned estimate. The historical scalar still loads for reporting
but is absent from new response schemas and cannot substitute for missing operands.
Peak-capacity and optional average-load checks are unchanged. Two short regression
tests cover the arithmetic contradiction, missing/invalid operands and legacy-only
claims; all 52 backend tests pass. No new workflow, model, budget or part-specific
rule is introduced.

Fresh prompt-15 run `7501797c452a4188942842d7b763227e` ended
`finished / incomplete / available`: 139.79 seconds, 21 calls, 294,528 input /
29,595 output tokens, 25 supplier calls, five document attempts, 49 PDF inputs
and two corrections. Code correctly found the initially selected TLV757 SOT-23
package's thermal allowance insufficient under the model's chosen workload.
Automatic correction selected a better WSON package, but its source coverage
was lost: the catalog URL returned a blank script-only TI distributor wrapper,
and the previously discovered family PDF was not rediscovered after replacement.
Wrong claims attributed to the blank HTML were discarded. Final review did not
fit. The [independent audit](prompt15-sensor-audit.md) preserves that incomplete
status rather than treating the plausible $9.59 parts selection as acceptance.

Prompt 16 fixes the demonstrated transport case: the exact TI distributor-wrapper
route's explicit HTTPS TI `/lit/` destination is followed within the existing
redirect/deadline and public-address checks, with the requested URL retained.
No JavaScript is executed. A real read verified the wrapper now returns the
original 41-page TLV757P PDF. Explicitly requested passive-source rereads are no
longer silently skipped; ordinary commodity selection still does not fetch a PDF
for every passive. Correction progress includes the actual structured proposal,
and the model is directed to address electrical failures together with record
cleanup. Fifty-five local backend tests pass.

Fresh prompt-16 run `02b754f77e834394acdfa4936c3efc23` ended
`finished / incomplete / partial`: 140.50 seconds, 21 calls, 278,727 input /
37,241 output tokens, 25 supplier calls, eight document attempts, 42 PDF inputs
and two corrections. Both recorded corrections reread the AZ1117 source for a
literal input minimum; the final 4.6 V calculation stayed assumption-only despite
existing output/dropout observations. Final review did not fit. The
[source audit](prompt16-sensor-audit.md) also identifies one unsourced-offer
capacitor, imprecise current/envelope claims and one unnecessary resistor; it does
not count the run as acceptance.

Prompt 17 clarifies that a regulator input requirement can be calculated from
source relationships while preserving any separate VIN minimum/UVLO restriction.
The derived quantity must cite those operands, using output maximum rather than
nominal. Diagnostics name any assumption ID and ask for the existing relationship
citations rather than repeatedly searching for a nonexistent printed literal.
There is no numeric-review bypass. Review navigation reuses the existing
TOC-prioritized projection with a 3,000-character/document cap; richer reading
navigation and every original PDF/HTML evidence block remain unchanged. Measured
on prompt16, this removes about 6,844 reserved input tokens across two reviews.
All 55 local tests remain passing; budgets and model stay unchanged.

Fresh prompt-17 run `bbafb862ecf647ebab38dbc8cd126b5b` ended
`finished / issues_found / available`: 22 calls, 282,119 input / 29,224 output
tokens, 139.22 seconds and one correction, before the input allowance prevented
final review. All 15 placements / 12 MPNs have available saved offers, totaling
$9.18. Automatic correction replaced an undersized regulator, but the
[independent source audit](prompt17-sensor-audit.md) found a genuine 0.1 uF versus
1 uF input-capacitor mismatch and 390 ohm +/-5% pull-ups below the sensor limit.
The saved thermal target also fails its calculation. Minor reporting errors with
adequate actual margin were not treated as rejection reasons. This is not an
accepted automatic BOM.

Prompt 18 removes the correction-instructions-to-assembly handoff when selected
parts and source facts are unchanged. Correction can return the complete repaired
compatibility record, applied through existing source protection and checks, then
reviewed afresh. Conflicting part/source edits in that mode are rejected. Its
7,000-token output allowance replaces the separate assembly request; run limits
remain unchanged. Selection also rejects explicit nominal-capacitance mismatches
against labeled catalog values, with SI normalization and a confirmed-detail
recheck. Missing/ranged values still need ordinary review. All 59 local tests pass.

The first prompt-18 attempt `2ef6fa859864477e8b8e3c2b907dd595` ended
`error / incomplete / available` on a provider read timeout during the first
source extraction: 67.90 seconds, six calls, 36,435 input / 6,320 output tokens.
It did not exercise correction or produce a checked BOM. The next attempt uses
the identical code, model, budgets and original request, without manual guidance.

That fresh retry, `149dc53304e146f584d6159366e663ee`, completed
`finished / checked / partial`, revision 3, with current whole-BOM review and zero
failed/unknown checks. It used 21 model calls, 274,131 input / 34,685 output tokens,
27 supplier calls, six document attempts, 45 PDF inputs, two corrections and
131.60 seconds. The first correction exercised the direct-record path; a later
targeted reread recovered missing MCU limits and corrected a USB source citation.
The final complete review fit inside the unchanged budgets.

The [independent original-source audit](prompt18-sensor-audit.md) accepts the
selected 15 placements / 13 MPNs as compatible under the recorded operating
conditions. It distinguishes minor current/envelope wording from actual margins
and explicitly describes using already-selected, same-rail capacitance in the
ordinary pre-layout arrangement. No parts, operating values, source facts or run
status were manually changed for acceptance. Sourcing remains partial: C4 has
no supplier price/stock offer, but retains its DigiKey purchase link. The known
$9.34 subtotal excludes C4; it is not a fabricated complete price.

Verification independently recomputed checks/BOM from the saved JSON and compared
them with the terminal SSE snapshot, live GET endpoint, JSON export and CSV rows.
All agree; all 13 grouped rows retain purchase links. All 59 local backend tests,
two Python supplier-boundary tests, three MCP tests, MCP build, frontend typecheck
and frontend build pass. Independent implementation/simplicity review found no
substantive defect in the direct-correction or capacitance-selection changes.
No browser interaction or physical hardware test is claimed. The earlier timeout
and failed runs remain evidence that broader unattended reliability is unmeasured,
not a reason to relabel this one successful run as a guarantee.

### Earlier scope-alignment work

The subsequent user clarification makes the deliverable component compatibility,
not schematic/wiring design. The earlier `180b9079` enable-pin and programming-pad
criticisms below describe faulty/missing wiring instructions, not demonstrated
wrong purchased parts. They must not be used as BOM-only completion requirements.
Material power, interface/resource and necessary-support judgments still apply.

Prompt 7 implements that boundary: legacy pin fields load but are excluded from
new model schemas/reports, wiring-only checks are removed, and support is recorded
by function/values/quantities. Exact supplier parameters plus an explicit current
evidence review can establish commodity connector/passive specifications; active
devices/modules still need manufacturer documentation, and support-purpose
obligations remain separate. Invalid observations are discarded with visible
guidance; using their missing IDs in actual claims remains blocking. A final
review must cover all five areas, using the existing bounded schema retry.

### First narrowed trial: `94602a69`

The original sensor request on Flash-Lite/provider default, prompt 7, ended
`finished / incomplete / available`: 20 model calls, 291,202 input tokens,
24,770 output tokens, 23 supplier calls, nine document attempts, 46 PDF page inputs,
two corrections and 135.65 seconds. Input reservation exhausted the unchanged
300,000-token allowance before the final revision's review. There were 15 selected
placements and 17 current unknown checks, not 17 independent incompatibilities.

This trial recovered WROOM-32E-N4 bulk/bypass and EN support and its 379 mA radio
condition. Its main unresolved choice was the Slkormicro `AMS1117-3.3 SOT-223`
regulator, whose exact supplier record had no datasheet locator. Attempts to read
the catalog page and discover a source did not establish its operating/output or
support specifications. Borrowing the MCU's operating range for the regulator
and assuming regulator limits did not resolve the gap.

Independent inspection later found a manufacturer family source at
https://www.slkoric.com/upload/file/20220317/AMS1117-3.3%20SOT-89.pdf . Despite its
filename, it covers SOT-223 too. Its output-capacitor guidance specifies tantalum
or aluminum; the selected 22 uF ceramic output capacitor was not established
suitable by that source. This is a support-component suitability question, not
a demand for a schematic, and not a measured claim of oscillation. The source
was found during independent audit, not read by the pipeline; it does not
retroactively repair the saved run.

The resulting narrow prompt-8 fix plans required active power conversion alongside
the other primary parts, before compatibility assembly. Selection now rejects an
active/module detail record with no HTTP(S) datasheet locator, leaving it pending
for the existing broader-query attempt. This is bounded-workflow source eligibility,
not a claim that every product-page-only part is electrically bad. A source URL
still must be fetched and checked for applicability. There is no part whitelist,
new discovery service, model switch or budget increase. At that point, 37 backend
tests and two supplier-boundary tests passed.

### Second narrowed trial: `346f3ee5`

Flash-Lite/provider default, prompt 8, selected WROOM-32E-N4, SHT40-AD1B-R3,
Amphenol 10155435-00011LF and documented AP2112K-3.3TRG1. It ended
`finished / incomplete / partial`: 16 model calls, 288,514 input tokens,
26,665 output tokens, 24 supplier calls, six document attempts, 36 PDF inputs,
two corrections and 130.58 seconds. The next input reservation did not fit;
the two CC resistor placements were pending reselection, and final review did
not complete. No provider quota error occurred; local rate-limit waits worked.

The main source error was concrete: the model selected the WROOM module's internal
schematic on physical page 37 but omitted external peripheral guidance on page 39.
It turned internal observations into external support: 20 kohm enable resistance,
10 uF bulk capacitance and no enable-delay capacitor. External guidance instead
recommends 10 kohm / 1 uF enable support and 22 uF + 0.1 uF supply capacitance.
Those are unsupported BOM choices, not concerns about numbered pins. Regulator
output bounds still borrowed MCU input limits; current/thermal assumptions were
not adequately supported. This does not establish that the principal components
are intrinsically incompatible or that hardware would fail.

Prompt 9 retains the same model, architecture and budgets. A small navigation
helper includes an explicitly leading `Peripheral Schematics` page from selected
module sources within the existing reading cap; it has no MPN/page constants and
does not treat headings as electrical evidence. It finds the actual cached WROOM
page 39 and C6 page 40. Focused extraction now receives request/modification and
operating assumptions, asks for relevant BOM facts rather than every supplied
table row, and distinguishes module-internal parts from external support.
Model projections omit successful findings and empty catalog placeholders, while
saved reports retain all findings and meaningful source/operating data. Local
tests: 39 backend tests pass. The following actual trial tested these changes.

### Third narrowed trial: `7c9effbc`

Flash-Lite/provider default, prompt 9, ended `finished / incomplete / available`
in 131.16 seconds: 20 model calls, 279,442 input tokens, 29,317 output tokens,
25 supplier calls, seven document attempts, 33 PDF page inputs and two corrections.
All 15 placements were selected. The final revision's review did not fit the
remaining input allowance; `review_completed` stayed false. Available sourcing
and a normal finish do not establish BOM acceptance.

The external WROOM support was now correctly identified as 22 uF + 0.1 uF supply
capacitance and 10 kohm / 1 uF EN support. Independent inspection still found
material issues: R2/R3 are 390 ohm ±5% pull-ups, which can reach 370.5 ohm, below
the source's 390 ohm condition for the cited sensor output-low specification.
The AP2112's 0.85 W thermal allowance is unsupported: converting approximately
400 mA from 5 V to 3.3 V dissipates about 0.68 W, corresponding to roughly 125 C
temperature rise at the cited 184 C/W package figure. This does not establish
thermal suitability under the saved assumptions, nor prove a measured failure.
Electrical/source references and support disposition also remained incomplete.

At this point the automatic-completion milestone was **not achieved**. The guided
refinements recorded below followed; they are not unaided generations.

### Guided refinements: `848be681` and `eba1d0a3`

These are explicitly **guided audit refinements**, not successful unaided generations.
Independent inspection supplied part corrections and source-page instructions through
the existing `/api/refine` endpoint; no saved status or evidence was manually promoted.
The actual purchase list and conditional independent assessment are in the
[sensor BOM audit](sensor-bom-audit.md).

`848be681f949489282a1db8ff2219c0d`, prompt 9, replaced the small AP2112 with
AP2114D-3.3TRG1 in TO-252/DPAK, changed its two capacitors to 4.7 uF ceramics,
changed the I2C pull-ups to 10 kohm 1%, and selected X7R sensor bypass. All 15
placements were available. The run ended `finished / incomplete / available` in
104.23 seconds: 11 model calls, 263,650 input / 25,502 output tokens, 28 supplier
calls, one document, 23 PDF page inputs and two corrections. The next review did
not fit the unchanged input allowance. The independent source audit found the
purchased BOM compatible under its explicit operating assumptions, but the
automated input-voltage, interface and signal records were still incomplete.

Three small demonstrated software issues were repaired for prompt 10:

- Refinement instructions now reach source-page selection; previously that stage
  could not see the explicit request to reread an unchanged part's current/logic table.
- Corrections can repair only the component mappings of existing requirements,
  validating IDs and preserving clauses/descriptions. Previously a missing mapping
  could not be repaired after planning. Refinements also record the current prompt
  version instead of inheriting the parent's obsolete version label.
- Purchasing prefers available ordinary packaging over custom Digi-Reel offers
  with unquoted setup fees. Custom-only offers disclose the unknown fee. The
  example now selects cut tape for its CC resistors: $11.08 rather than an apparent
  $11.06 that excluded the reeling fee. This is not a checkout-total guarantee.

`eba1d0a3e6634fedb1654f255e54b62f`, prompt 10, retained every selected identity,
purpose and search query. It ended `finished / incomplete / available` in
111.71 seconds: 12 model calls, 275,892 input / 31,253 output tokens, 12 supplier
calls, no new documents, 41 PDF page inputs and two corrections. The requested
WROOM/SHT pages were interpreted; regulator input limits and the broad consumer-use
requirement mapping were repaired. The remaining two signal records wrongly cite
the sensor's output-low observation as evidence for the MCU driver, and do not
cover the reverse SDA direction. The ownership check correctly rejects them.
The other five unknowns are consequences of the final revision not receiving a
completed review, not five new physical incompatibilities. Its next review could
not fit within the 300,000 input-token allowance. There was no provider quota error.

The independent BOM audit remains a conditional pass for these unchanged parts;
the pipeline did not establish a completed automatic compatibility result. A
source-reviewed purchasable example is delivered, while unattended backend
completion remains unresolved. Do not equate either local tests or this guided
artifact with general model reliability, or fix the result by deleting material
signal/provenance checks. No model switch, budget increase or architecture rewrite
was made.

Verification after the fixes: 42 deterministic backend tests, two Python supplier
boundary tests, three MCP tests/build, and frontend typecheck/build passed. Actual
HTTP retrieval and JSON export matched saved state; CSV matched all 12 grouped
BOM lines / 15 placements and retained `incomplete`. Every line had an available
purchase link, the cut-tape subtotal was $11.08, and health returned `busy: false`.
The final refreshed offer snapshots are from 2026-09-14 03:23 UTC. This checks the
observed software contracts, not the absence of every possible bug.

## Earlier Flash-Lite smoke run, before the scope clarification

The user requested a fresh actual run using only `gemini-3.5-flash-lite`, with
the practical criterion that our pipeline works and any remaining model errors
are minor. Stronger-model comparisons and the earlier three-frozen-trial gate
are not prerequisites for this decision. No model, framework, prompt, budget,
or production code was changed for the following test.

`180b90791e3a48cba715bc0ad871cd4e` ran the original P0 request with provider-default
thinking and prompt 6. It finished normally in 94.93 seconds, with 13 model calls,
157,879 input tokens, 19,103 output tokens, 20 supplier calls, eight document
attempts, and 24 PDF page inputs. There was no quota failure or budget stop.
The correction call proposed no changes, leaving zero applied correction rounds.
Outcome: `finished / incomplete / available`, with 12 current unknown checks.

The result contains 15 placements grouped into ten purchasable BOM lines:
ESP32-C6-MINI-1-N4, SHT40-AD1B-R3, AP2114H-3.3TRG1,
Amphenol 10155435-00011LF, and supporting passives. The saved offer snapshot totals
USD 8.81 for one board, excluding shipping, tax, PCB fabrication, assembly, and
the external programmer. Available sourcing is not an electrical-quality verdict.

Independent implementation inspection found no demonstrated handoff, arithmetic,
budget, or persistence fault causing this result. Thirty-two backend and two
Python supplier-boundary local-fake tests passed again. Actual HTTP checks verified
that saved state matched JSON export, CSV contained the same ten BOM lines and
`incomplete` status, every line had an available purchase link, and health returned
`busy: false` after completion. These checks do not prove the absence of all bugs.

Independent source inspection separates the remaining issues:

- **Material connection error:** source support `D1S2` and its fulfilled circuit
  instruction connect the ESP32-C6 enable RC network to module pin 8. The actual
  module's pin 8 is NC; EN is pin 9 (datasheet pages 10-11 and Figure 9-1 on
  physical page 40). Following the numbered instruction would leave EN without
  its intended connection. The 10 kohm / 1 uF values are reasonable; calling the
  resistor R8 in the new design is not itself an error. The extracted source fact
  also wrongly attributes the reference diagram's R8 to EN rather than GPIO8.
- **Material completeness gap:** `INT_PROG` specifies only UART TX/RX test pads.
  Neither configuration nor support establishes GPIO8 high / GPIO9 low at reset
  for download mode, or the required reset/boot access (Table 4-3, physical page
  13). This can be resolved with an explicit off-board-fixture/test-pad arrangement;
  it does not require an onboard programmer or a full schematic generator.
- **Unsupported power assurance, not demonstrated overheating:** the model uses
  354 mA from supplier metadata while citing an unrelated manufacturer supply
  condition. The inspected datasheet has a 382 mA Wi-Fi peak under its stated
  operating mode (page 27). Its 0.7 W thermal allowance cites a USB-source
  assumption that says nothing about thermal conditions. The review's safe-thermal
  pass is therefore unsupported, although the selected 1 A regulator is not shown
  to be undersized and physical failure has not been measured.
- **Traceability/review defects:** the regulator output bounds cite the processor's
  input limits; the connector sources returned 403/404; CC resistors lack cited
  support; and the model omitted support-area review findings despite claiming
  complete coverage. A claimed correction to an invalid quotation was only review
  prose, not an actual correction. The code preserved these unknowns. These are
  not twelve independently demonstrated electrical failures.
- **Do not import historical defects:** this result includes the module bulk and
  bypass capacitors, sensor decoupling, two I2C pull-ups, two CC pull-downs, and
  both regulator input/output capacitors. Its SHT logic ratios were converted to
  voltages. The exact AP2114H SOT-223 variant has no EN pin (AP2114 page 3), so a
  missing regulator-enable connection is not a defect in this BOM.

Source files are the unchanged runtime-cached manufacturer PDFs with hashes
`26691033f31cbebf623842c16624e61151b152533c13a850c091c8e858c510a2` (C6),
`8db4a43f17149b76811cfb504caaeca4ef844ddc710cb9b45905c51c7ddfe3c2` (SHT4x), and
`d20cd46c5f472fe220f3e1ffb82b2679bc37e3dd145891bfdedf0acb78089d51` (AP2114).
This audit used original manufacturer pages, including visual inspection, not
another generated BOM as ground truth. It is a practical pre-layout review,
not certification or a hardware test.

**Decision:** the backend passed this end-to-end runtime smoke test, but the user's
"only minor model errors" criterion was not met. Keep Flash-Lite and the existing
workflow. The next bounded improvement should target source-to-connection accuracy,
boot/programming completeness, and the review/correction response to those gaps;
there is no result here justifying an architecture rewrite or larger budgets.
Experimental iteration can proceed, but this particular BOM should not be presented
as compatibility-checked or ready to order without correction.

## Full workflow trials

The first eight saved runs, `b7deafb8`, and `6a8a641f` used `gemini-3.5-flash-lite`;
`54f35df0` and `dc113c62` used `gemini-3.6-flash` with medium thinking.
Attempts `8928c0d0` and `f0105dca` used `gemini-3.8-flash` with medium thinking;
the latest `180b9079` used Flash-Lite with provider-default thinking.
All ended with lifecycle `finished` except `dc113c62` (provider quota exhaustion)
and `8928c0d0`/`f0105dca` (model unavailable), which ended with `error`.
P0 is the public USB-C temperature/humidity/WiFi/Bluetooth request. H1 is the
held-out BMP280 four-wire-SPI pressure logger from the
[independently prepared acceptance oracle](sensor_acceptance_oracle.md).

IDs are unique prefixes of the local `backend/data/runs/<id>.json` filenames.
Numbers below are the saved usage fields, not independently verified provider
billing. A budget refusal can occur below the cap when the next input/output
reservation would exceed it; the request counter can include an attempt stopped
at reservation.

| Run prefix | Case | Compatibility | Model calls | Input / output tokens | Corrections | Seconds | Stopping reason |
|---|---|---|---:|---:|---:|---:|---|
| `6dfc8ccf` | P0 | incomplete | 6 | 118,922 / 6,485 | 0 | 58.25 | Input budget |
| `d2edc2d5` | P0 | incomplete | 6 | 91,791 / 7,909 | 0 | 54.70 | Input budget |
| `4e9d8c92` | P0 | issues_found | 8 | 143,335 / 13,672 | 1 | 69.55 | Input budget |
| `4d570535` | P0 | incomplete | 21 | 295,964 / 29,706 | 2 | 132.73 | Input budget |
| `d6839c54` | P0 | incomplete | 19 | 286,677 / 27,122 | 1 | 134.82 | No further supported correction |
| `8ad61fe4` | H1 | incomplete | 25 | 280,140 / 34,218 | 2 | 135.29 | Input budget |
| `a05b7a88` | P0 | incomplete | 9 | 176,126 / 10,413 | 0 | 98.46 | Input budget |
| `3ddec445` | P0, medium thinking | incomplete | 16 | 110,968 / 37,973 | 0 | 154.84 | Output budget |
| `54f35df0` | P0, 3.6 medium | incomplete | 8 | 46,361 / 35,402 | 0 | 218.24 | Output budget, before assembly |
| `dc113c62` | P0, 3.6 medium | issues_found | 11 | 78,185 / 40,923 | 0 | 219.70 | Provider quota, before whole-design review |
| `b7deafb8` | P0, Flash-Lite medium | issues_found | 24 | 293,560 / 50,277 | 2 | 194.83 | Input budget, before final current-revision review |
| `6a8a641f` | P0, Flash-Lite medium, prompt 5 | incomplete | 27 | 250,242 / 60,927 | 1 | 219.14 | Input budget, before final current-revision review |
| `8928c0d0` | P0, 3.8 medium | incomplete | 2 | 3,568 / 5,600 reserved | 0 | 5.29 | Both attempts HTTP 503, before any design |
| `f0105dca` | P0, 3.8 medium, prompt 6 | incomplete | 2 | 3,568 / 5,600 reserved | 0 | 3.69 | Both attempts HTTP 503, before any design |
| `180b9079` | P0, Flash-Lite default, prompt 6 | incomplete | 13 | 157,879 / 19,103 | 0 | 94.93 | No further supported correction |

The first three had 150,000/20,000 input/output caps; the next six used
300,000/40,000, and the last six used 300,000/64,000. The first two stopped without
a correction; `4e9d8c92` did start one. None finished a successful final
review/correction. Supplier-call counts
were respectively 18, 26, 25, 18, 24, 17, 23, 22, 10, 13, 27, 23, 0, 0, and 20;
PDF page-input counts were 14, 14, 28, 67, 62, 61, 12, 32, 22, 16, 54, 44, 0, 0, and 24.
Sourcing was `partial` for the first two, `3ddec445`, and `dc113c62`; `unknown`
for `8928c0d0` and `f0105dca`; and `available` for the other nine. Available parts
did not make the designs compatible. The two 3.8 attempts' token counters are failed-attempt
reservations, not observed provider generation usage.

These were changing development versions, not three repetitions of a frozen
implementation. Saved prompt-version labels alone do not identify all intervening
edits, so the table cannot establish an improvement rate.

## Engineering inspection

The oracle was prepared independently from manufacturer text and visual inspection
of the relevant original circuit/table pages. It is a manual source reference,
not another model's generated answer used as truth. It is not an exhaustive
electrical certification. Its exact-part distinctions matter: recommendations for
the C6/AP2112 candidate pair must not be blindly applied to WROOM/AP2114 replacements.

- `4d570535` had substantive issues documented in the oracle: slice-index citations,
  incorrect C6 reset-circuit interpretation, missing module bulk decoupling,
  unspecified regulator enable, missing programming access, and unsupported numeric
  citations. It was not merely an overly cautious rejection.
- `d6839c54` selected a WROOM module and AP2114 regulator. Its own evidence `D5E6`
  describes separate input/output support capacitors, but the proposed placements
  provide no regulator-input capacitor. Its LDO output range cites the module's
  receiving supply range (`D1E1`), and minimum recommended supply capacity (`D1E4`)
  is reused as maximum consumption and USB-source proof. Dropout cites an output
  tolerance observation; a thermal allowance cites a USB-supply assumption. These
  are evidence/application errors, not ordinary later layout cautions. The saved
  model review completed, but 13 current unknown checks remained and compatibility
  stayed `incomplete`.
- Held-out `8ad61fe4` also remained incomplete: it had 21 current unknown checks,
  including source/support, SPI threshold, and regulator-headroom gaps, and no
  completed final review after its last correction. It selected an Adafruit
  BMP280 breakout (`2651`), so chip-level support expectations need interpretation
  against that module boundary. This first held-out result is reported as a failure
  to complete, not a successful generalization example.
- `a05b7a88` selected Microchip WFI32E02UE-I under an ESP32 planning name, and
  onsemi NCP114 under an AP2114 planning name. Stale document hints then attached
  ESP32/AP2114 sources to those replacements; actual ESP32 observations and support
  needs were accepted for the Microchip placement. The supplier metadata itself
  labeled that module Bluetooth/WiFi, so a keyword check would not establish BLE
  capability. The 300 mA regulator also warranted scrutiny against the module's
  catalog transmit range reaching 359 mA. The run ended before final review with
  15 current unknown checks. All 13 placements were selected, but that was not a
  successful design. An attached 821-page family manual also exposed excessive
  navigation-context size; only 176,126 input tokens were recorded before the next
  reservation exhausted the 300,000-token allowance.
- `3ddec445` records Google/medium thinking and prompt version 3. It ended at the
  output allowance with 22 current unknown checks, no completed whole-design
  review, and zero correction rounds. Eight document operations were recorded.
  Lower input use did not establish a successful end-to-end improvement: repeated
  source interpretation during support expansion still consumed output budget.
- `54f35df0` used 3.6/medium with the new source-reuse path and an experimental
  5-RPM limit. It stopped in evidence processing before assembly: five document
  operations, 17 current unknown checks, no completed review, and no corrections.
  The next assembly output reservation could not fit after 35,402 recorded output
  tokens against the 40,000 cap. This result does not demonstrate that source reuse
  or the alternative model completes a device design.
- `dc113c62` reached assembly and passive selection but hit provider quota before
  whole-design review. It recorded five document operations and no corrections.
  A code check estimated LDO dissipation at 0.700825 W against a stated 0.6 W
  allowance, so compatibility remained `issues_found`. This is a failed check under
  an assumed thermal allowance, not measured junction temperature. The 64,000-output
  cap did not establish completion; further 3.6 trials were stopped after quota
  exhaustion rather than silently switching billing or bypassing the limit.
- `b7deafb8` used Flash-Lite/medium, prompt version 4, and the 64,000-output
  allowance. It reached revision 3 after two corrections but exhausted input
  budget before completing that revision's whole-design review. All 15 placements
  were selected and sourcing was available; 18 current unknown checks and one
  failed check remained. The failed rail-current check compared a recorded
  350.5 mA load with 300 mA source capacity under the run's stated assumptions.
  Seven document operations were recorded. This was not a successful final review
  or a positive baseline.
- `6a8a641f` exercised prompt version 5 with Flash-Lite/medium. It selected an
  ESP32-WROOM-32E-N4, not an integrated USB-C controller assembly, and stopped at
  input budget on revision 2 after one correction. All 14 placements were selected;
  17 current unknown checks and no completed current-revision review remained.
  Six document operations were recorded. Independent source inspection still found
  material interpretation errors: the module's internal page-37 circuit was treated
  as external support, the EN resistance was interpreted as 20 kohm, and SHT logic
  threshold supply ratios were used as voltages. Absence of a saved failed code
  check did not establish correctness. This is not a positive carrier-board baseline.
- `8928c0d0` failed at planning: the initial 3.8 request and its one bounded retry
  both returned HTTP 503. It produced no design and made no supplier or document
  calls. This is a model-availability failure, not an electrical-quality result or
  evidence of a quota limit. Its saved token counters retain the failed reservations.

## Focused source capability

These small public-source probes isolate extraction from circuit assembly; they
are not complete BOMs or replacements for the positive-case gate.

| Saved run prefix | Probe | Model calls | Input / output tokens | PDF pages | Observed result |
|---|---|---:|---:|---:|---|
| `60abd23c` | SHT4x pages 3, 9, 17 | 1 | 4,261 / 1,843 | 3 | 9 reference-valid observations; targeted circuit, limits, and pin facts recovered |
| `ed1e94a4` | ESP32-C6 source pages | 1 | 11,005 / 3,180 | 8 | 11 initially accepted observations; 5 additional quotes initially rejected by text normalization |
| `2c4295c5` | ESP32-C6, explicit medium thinking | 1 | 11,196 / 2,855 | 8 | 8 valid observations and two source-owned support needs; one remaining guidance note |

The SHT probe still recorded two source-gap notes; it was not a whole-design review.
For C6, the targeted facts were checked against the source. The five rejected quotes
passed the later local exact-character revalidation after Unicode NFKC/layout-space
normalization was corrected; this was not semantic/fuzzy acceptance of paraphrases.
The original saved C6 snapshot retains its historical rejections and has not been
rewritten to imply a new live success. The first two focused snapshots leave `model`
empty, so they do not independently establish model identity from that field. Their
saved elapsed counters are not used here as end-to-end latency measurements.

`2c4295c5` records `gemini-3.5-flash-lite/medium` and prompt version 2. It recovered
22 uF plus 0.1 uF supply decoupling and the EN 10 kohm/1 uF recommendation. Its one
guidance note concerned establishing the exact N4 flash variant from the supplied
family pages. This is a useful focused capability observation, not a passing BOM.
Other prompt/schema changes occurred between probes; the result does not isolate a
thinking-level effect or establish that medium thinking is better. The new separate
`model_configuration` field was not yet populated on this focused record.

A further unsaved public ESP32-C3 physical-page-34 probe used Flash-Lite with high
thinking and a 6,000-token output allowance: one call, 2,443 input and 5,162 output
tokens. It returned source facts but still incorrectly assigned R9 to the EN
network despite also reading adjacent 10 kohm/1 uF prose. This is a material circuit
interpretation error; increasing thinking alone has not demonstrated a fix. These
numbers and observations come from the execution notes, not a retained run JSON.

Two separate public-source comparisons with `gemini-3.8-flash` returned HTTP 503.
The first issued one provider attempt, then lacked reservation budget for its retry;
the second allowed two bounded attempts and both returned 503. These are availability
failures, not evidence that the stronger model is electrically better or worse, and
not proof of a project quota limit. No automatic paid fallback was used.

Further bounded public C3 page-34 comparisons (execution notes, not saved run JSON):

| Model / probe configuration | Attempts | Recorded input / output tokens | Result |
|---|---:|---:|---|
| 3.7 Flash, high thinking | 2 | Not recorded here | Both HTTP 503 |
| 3.5 Flash, high thinking (not Flash-Lite) | 2 | Not recorded here | Both HTTP 503 |
| 3.6 Flash, high thinking | 1 | 2,443 / 7,240 | EN interpreted correctly; R8 incorrectly assigned to GPIO9 |
| 3.6 Flash, medium thinking, high-resolution native PDF | 2 | 7,172 / 11,216 | First HTTP 503, then response; R8 still incorrectly assigned to GPIO9 |
| 3.5 Flash-Lite, medium, original page plus four magnified native-PDF views | 1 | 4,715 / 1,106 | R8 still assigned to IO9; R2=0 described as a pull-up |

Source inspection confirms R8 belongs to GPIO8. None of these probes passed the
targeted circuit-interpretation check. The 3.6 high probe requested a 6,000-token
output allowance; its reported output includes thinking tokens. The medium probe's
accounting includes the failed-attempt reservation. The magnified Flash-Lite probe
used five PDF page inputs including the four views; it did not fix the connection
interpretation. These figures are not directly
comparable billed-generation totals. Production PDF resolution and default model/
thinking settings remain unchanged: Flash-Lite with provider-default thinking.
The completed 3.6 full-run experiments are recorded above as `54f35df0` and
`dc113c62`, not as successful baselines. Additional selected support is not presumed
wrong merely because it differs from an earlier plan.

### Bounded availability continuation

A tiny free-tier 3.8 structured health probe succeeded at
2026-09-14T00:16:58 UTC, reporting 19 input and 184 output tokens, including
173 reasoning tokens. That availability change prompted one resumed P0 run,
`f0105dca`: both planning attempts returned HTTP 503, with no supplier/document
calls or corrections. It never exercised prompt 6's engineering stages.

A separate public plain-text primary-parts proposal succeeded with 72 input and
1,139 output tokens, including 954 reasoning tokens. Controlled full-`Plan`
schema probes using native `json_schema` and `function_calling` each returned
HTTP 503 on their single attempt. Tiny/plain-text success therefore did not
establish full structured-workflow readiness; these observations do not prove
that schema size or structured-output mode caused the failures.

A final proposed plain-JSON-plus-`Plan`-schema probe was rejected by auto-review
**before execution**, requiring explicit approval for external transmission of
the private-repository-derived schema. It made no provider call and consumed no
provider usage. No workaround or production response-method change followed.
The successful probe counters above come from execution notes, not saved
full-run snapshots, and do not demonstrate engineering accuracy.

A separate public-source-only probe at 2026-09-14T00:28:10 UTC sent original
physical pages 21, 22, and 34 of the Espressif ESP32-C3-MINI-1 datasheet v2.2,
with their extracted public text and plain-prose reading questions. The freshly
downloaded PDF hash matched the independently inspected cached source
(`de7361381348d82a1abd337f10170be7a420675987568f71fe3c5b100deed270`).
This direct Google SDK call used 3.8/medium, a 3,000-output allowance, a 30-second
timeout, and one attempt with SDK retries disabled. It contained no repository
schema or saved design and did not perform the rejected diagnostic. It returned
HTTP 503 before an interpretation, so there is no new model-quality result or
reported token usage. This also shows that a non-schema source-reading request
can fail; the earlier structured-output failures cannot yet be attributed to
their output method alone.

At that point the implementation goal remained unachieved. After three consecutive
goal turns ending at the model-access/diagnostic-authority barrier, autonomous work
was marked blocked. The user's subsequent Flash-Lite-only actual-run request
resumed useful work without performing the rejected diagnostic; see the current
decision above. No paid fallback, production response-method change, or further
budget increase followed.

## Implemented fixes and remaining verification

Source extraction now retains separate source-owned support obligations. Circuit
assembly must provide same-ID fulfillment; omitting a source obligation leaves an
explicit unresolved need. Configuration-only corrections can reuse observations
when parts are unchanged and no source gap or newly requested unread page requires
another extraction; whole-design review still reruns against original pages.

The `a05b7a88` trial exercised the new support handoff but exposed upstream identity
contamination. The current code now names selections by their actual MPN and clears
preselection document hints; additional guides must be discovered for the selected
part. Each extraction packet must explicitly identify applicable selected owners
before observations can be accepted. Source navigation is capped at approximately
10,000 characters per document and 30,000 across the current documents; omitted
pages remain requestable. Open-drain high-level checks can reference their actual
pull-up rail instead of inventing a push-pull VOH specification.

New full runs record provider/thinking configuration separately. After `3ddec445`,
support-expansion passes were changed to interpret
only newly introduced parts' sources, retaining earlier observations instead of
re-extracting every source. `54f35df0` still exhausted output before assembly.
Following that result, an independently reviewed bounded experiment raises the
output cap to 64,000 and per-source extraction allowance to 4,000. It keeps the
480-second, 30-call, 300,000-input, 120-page, and two-correction limits. The purpose
is to measure the first complete assembly/review, not declare the larger cap
sufficient or keep raising limits indefinitely. Prompt version 4 defaults to an
off-board programmer and named test pads; an onboard USB bridge needs an explicit
request or a concrete necessity for the selected device.

The 64,000-output trials are now recorded above: `dc113c62` stopped at provider
quota; `b7deafb8` and `6a8a641f` stopped at input budget after two and one
corrections respectively; `8928c0d0` and `f0105dca` failed before planning returned
a design.
None completed its current whole-design review.

Prompt version 5 now gives the page-selection call the existing observations,
source-owned support obligations, and current issues so it can request missing,
invalid, or newly relevant context instead of rereading unchanged sources after
a replacement. Retained observation pages remain inputs to whole-design review
even when no new reading is requested. Rereading one source packet unions its
new pages with the pages supporting retained observations rather than discarding
that context.

The planner also now prefers a documented board-mountable controller assembly
integrating requested USB-C/power functions when it meets the request and reduces
external circuitry. Such a result is explicitly a carrier-board design around
a purchased assembly: exposed pins, supply inputs, external-rail capacity after
onboard loads, and mounting still need review. This is not a part whitelist or
a finished sensor-kit substitution; internal components are not bought twice.
Requirement IDs are normalized with a `req:` prefix to distinguish them from
physical references such as `R1`. The first prompt-5 trial, `6a8a641f`, remained
incomplete and did not select that integrated-assembly route. These changes have
**not established a positive full-device baseline** or resolved the demonstrated
interpretation problems. The bounded free-tier 3.8 attempts, `8928c0d0` and the
resumed `f0105dca`, are recorded as unavailable above despite the small successful
availability probes. No production method, framework, or budget was changed;
there is no automatic paid fallback.

The final prompt-6 handoff change addresses observations omitted during the
`6a8a641f` source reread. Each extraction now receives previous observations and
source-owned support from the same document, after pruning owners no longer
applicable to the selected parts. It still returns one complete replacement
packet: preserve correct concrete values, conditions, and unrelated applicable
facts, while correcting or removing mistakes against the original supplied pages.
This adds no merge system or new state. Independent implementation review and a
local fake verified the handoff. The later `180b9079` trial reached its engineering
and review stages but retained material interpretation errors, as recorded above.
Prior interpretations can also anchor old mistakes, so original-source review
remains necessary. No positive baseline follows from this change.

Production default model/thinking remain Flash-Lite/provider default; optional
tracing is disabled. Production PDF handling
was not changed by the magnified-view experiment. Neither the combined fixes nor
increased thinking have **produced an independently inspected positive full-device
baseline here**.
Further source and full-design evaluation is required before asserting completion,
comparative model quality, or release readiness.

Before the availability continuation, final local verification passed: 32 backend tests, two Python supplier-boundary
tests, three MCP tests with the TypeScript build, and frontend typecheck/production
build. The frontend build reported only the stale Browserslist-data warning.
Read-only HTTP checks found health responsive with `busy: false`; for `6a8a641f`
and `8928c0d0`, saved JSON matched JSON export exactly, CSV rows matched the BOM
(11 and zero respectively), and incomplete status was preserved. These checks
verify runtime/export behavior, not the electrical accuracy of a BOM. The owned
test servers were then stopped; saved runs and source documents were retained.

The earlier proposed gate was an independently inspected positive baseline,
followed by three frozen trials of the positive case and each material reviewer
mutation (M1-M4), plus the reported held-out outcome. The user's latest practical
smoke-test criterion supersedes that gate for the immediate proceed decision;
it does not turn a material connection error into a minor imperfection. An
unrelated `unknown` does not count as detecting a deliberately introduced
incompatibility. Live calls remain separate
from deterministic tests; use [the manual smoke command](../README.md#verification)
and retain outcomes/usage without committing credentials or full runtime caches.
