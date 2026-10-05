# Live verification results

Recorded 2026-09-13–14, 2026-09-30, and 2026-10-05 UTC from named local run JSON snapshots,
event streams and focused-test execution notes. The current cleanup verification uses the
user-approved binary review policy. Earlier frozen and practical evaluations below retain
their original criteria and outcomes, without retrospective relabeling.
Earlier accepted conditional BOMs include `29c85ccd` and `149dc533`.
Older sections preserve unsuccessful and guided trials as historical diagnostics, not
current blockers or successful unattended examples. No general reliability, current stock,
provider-quota or hardware-qualification claim follows from these records.

Raw snapshots, event streams, document caches, and evaluation artifacts under
`backend/data/` stay local and are excluded from source control. Saved-run IDs and
localhost links refer to those local records; this repository publishes the audit summaries.

## Preset generalization (2026-10-04 local / 2026-10-05 UTC, unchanged prompt 41)

The [declared eight-run batch and independent audits](preset-generalization-2026-10-04.md)
completed on unchanged backend code, model, and limits: one wireless control, two exact
battery-logger requests, two exact light/display requests, and three new requests.
The backend passed six and failed two. Independent source inspection found three plausible
sets without an identified compatibility error, two correctly rejected unsuitable results,
and **three false acceptances** (wireless control, first battery attempt, first display attempt).
Failures involved inadequate power capability, an incompatible battery holder, or stale
supply/interface configuration after part replacement. Unknowns and missing ordinary passive
procurement were not treated as functional failures. The two extra frontend presets remain removed.

All saved/streamed/GET/JSON/CSV comparisons passed; no run stopped on quota or budget.
Usage was 115 model calls, 956,598 input tokens, 114,238 output tokens, and 661.87 seconds.
No output was manually repaired, no historical verdict was rewritten, and no tuning cycle
followed. These counts describe this small fixed batch, not general reliability.

## Reporting handoff audit (2026-09-30, unchanged prompt 41)

The follow-up pass audited all backend modules after clarifying that verbose success narratives
and unsupported electrical figures do not belong in the normal product report. **No further
runtime deletion or rewrite was justified.** The backend source hashes are identical to the
preceding functional-component cleanup. There was no prompt, model, schema, budget or dependency change.

Passing model findings still support catalog, passive-load and interface evidence checks and
completed-review detection. Failure explanations and remedies guide source reading and correction.
`design_context` already excludes successful findings and selection rationale from subsequent
model calls. Removing these records from saved state would change useful behavior or diagnostics,
not merely remove UI noise. Numeric source bindings, evidence references and binding errors
likewise retain distinct purposes.

The changes in this pass are documentation and verification. AGENTS, backend README and current
architecture now distinguish normal UI content from diagnostic records, retain full JSON and
parts CSV exports, and specify that empty historical support sections should not appear on new
runs. The root README identifies this as pending frontend alignment, not completed UI work.
In particular, current frontend quantity/rail formatters display values without inspecting
`binding_error`; backend numerical checks already reject those unresolved operands. Fixing
that presentation requires frontend work, not a new backend reporting layer.

Independent read-only reviews found no additional justified backend cut. Verification again
passed **106 backend tests**, **21 frontend tests**, frontend typecheck/build, **3 MCP tests plus
build**, compatibility of 55 Python packages, and `git diff --check`. The existing nonblocking
Browserslist data-age warning remains. No frontend source files were edited in this pass.

### Every fresh attempt

One fresh unattended run used the original sensor request without hints or manual repair:

> Make me a temperature and humidity sensor with WiFi and Bluetooth powered by USB-C for consumer use.

| Run | Verdict / sourcing | Placements / rows | Calls | Input / output tokens | Duration | Corrections |
|---|---|---|---:|---:|---:|---:|
| `efb7a3217200441d93a1921248458879` | checked / available | 6 / 5 | 9 | 75,755 / 11,532 | 49.86 s | 0 |

All six placements were selected and all five grouped rows have purchase links and sufficient
recorded stock. They are the same four functional parts as the preceding run, plus two Panasonic
ERJ-3EKF5101V 5.1 kΩ resistors. Those CC resistors are electrically plausible, but their procurement
is a model scope-adherence deviation from the instruction to leave ordinary support as notes.
The backend did not restore support-completeness requirements or fulfillment records.

The run consumed ten supplier calls, five document acquisition attempts and ten PDF page inputs.
It finished without model/provider errors, with zero blocking failures and eleven nonblocking
failed/unknown check details. The regulator and connector source access limitations remain.
The 36 stream events, saved GET, JSON export, and CSV identities/quantities/links/verdicts agree.
Legacy support arrays are empty and frozen runtime hashes match. The isolated port-3002 server
did not alter existing application/MCP processes.

Artifacts are in `backend/data/evaluations/reporting-cleanup-20260930-v41/`: the original saved
run, `sensor-events.jsonl`, `report.json`, `bom.csv`, `manifest.json`, and `verification.json`.
This is a repeat smoke test of unchanged software, not evidence that this pass improved model
accuracy. The result was not manually repaired or replaced with a more favorable retry.

### Independent output audit

Visual source inspection again found a plausible functional-component set with no obvious
inherent inter-part voltage/logic conflict or missing functional block. The selected 5.1 kΩ,
±1%, 0.1 W CC resistors fit that supporting role, although their inclusion was outside the
notes-only generation instruction. Their presence is not evidence that the backend reinstated
a completeness gate.

The **model's thermal pass is wrong**, not merely missing a citation. It claims roughly
82 °C junction at 40 °C ambient using 65 °C/W and a 150 °C maximum. The exact Slkor source
specifies 135 °C/W for SOT-223 and 125 °C operating junction maximum; 150 °C is thermal
shutdown, not an operating approval. With the recorded 379.5 mA peak load treated as sustained
and up to 10 mA regulator own current, nominal 5 V/3.3 V produces about 134 °C. At the recorded
5.25 V input and source 3.234 V output corner, the screen is about 150 °C. Both exceed the
record's 120 °C target. The model also reuses the catalog's blanket 1 A capacity, whereas the
source recommends a 600 mA SOT-223 DC maximum.

This does not establish that the regulator must be replaced for an ordinary sensor. This run
actually extracted Espressif's 239 mA active TX average as `D1E4N2`, distinct from 379 mA peak.
Using that average plus 0.5 mA sensor and 10 mA regulator own current gives about 0.535 W and
112 °C at 40 °C ambient with 135 °C/W. That is a plausible operating case, but the saved
configuration left `average_output_current` null and did not adopt it. The independent audit
must not silently repair the record or endorse the original thermal pass. The report also
contains wrong-owner/missing I2C operands despite physically compatible source thresholds.

Audit sources were the cached ESP32 pages 28–29, SHT4x page 9 and exact Slkor pages 2–3 retained
with the preceding evaluation. The PDF skill's visual table review was used. Backend numerical
checks left the unsupported thermal operands unknown; the model supplied the misleading pass
prose. This reinforces the documented separation of user-facing output from diagnostic claims,
but hiding that prose does not itself improve engineering accuracy. No follow-on prompt,
special-case, model or architectural tuning cycle was started.

## Functional-component cleanup (2026-09-30, prompt 41)

This pass implements the clarified product boundary: a BOM of functional components plus
source-grounded support/configuration notes, not a complete PCB supporting-parts inventory.
The earlier support-count audits below remain historical assessments under their original scope.

### Cleanup and verification

- Removed new-run support-requirement/fulfillment schemas, same-ID matching, omitted-obligation
  reinsertion, support-completeness checks, and forced peripheral-schematic page selection.
  Source evidence and configuration notes retain material supporting-circuit dependencies.
- Retained operating configuration, source-owned numerical binding, voltage/current/logic,
  interface/resource and regulator checks, selected-part correctness, and bounded addition and
  source reading of missing functional blocks. Explicitly requested passives remain supported.
- Renamed the circuit proposal/configuration path to `OperatingConfiguration`, `_configure_bom`
  and `_source_and_configure`. Removed obsolete tests and made legacy-only fixtures explicit.
- Historical support arrays remain serialized and readable. New execution clears those arrays;
  model context excludes them, and retrieval/export never regrades historical saved results.
- Aligned AGENTS, both READMEs, current architecture and all model stages. Kept the same free
  Flash-Lite model, binary review policy, execution limits, dependencies, services and API.
- Independent code/doc reviews found no blocking regression or additional justified boundary
  refactor. Backend runtime is 4,400 lines across the same 11 modules, down 189 lines from the
  immediately preceding cleanup state. This count includes schemas, prompts and comments.

Verification passed: **106 backend tests**, **21 frontend tests**, frontend typecheck and
production build, **3 MCP tests plus build**, dependency compatibility for 55 installed Python
packages, and `git diff --check`. Tests remain deterministic and local. The frontend build
reported a stale Browserslist database warning, not a build failure; dependencies were unchanged.

### Every fresh attempt

One unattended run used the unchanged original request, without component hints or manual repair:

> Make me a temperature and humidity sensor with WiFi and Bluetooth powered by USB-C for consumer use.

| Run | Verdict / sourcing | Placements / rows | Calls | Input / output tokens | Duration | Corrections |
|---|---|---|---:|---:|---:|---:|
| `d4b525bee91246a4aeb3086f015174c8` | checked / available | 4 / 4 | 8 | 63,952 / 10,135 | 41.99 s | 0 |

The BOM contains ESP32-WROOM-32E-N4, SHT40-AD1B-R2, Amphenol 10155435-00011LF and
Slkor AMS1117-3.3 SOT-223. All four rows have purchase links and adequate recorded stock.
Routine support is configuration guidance, not purchased placements or fulfillment records.
The run consumed eight supplier calls, five document acquisition attempts and twelve PDF page
inputs. There were no provider/quota errors. The regulator's source and connector's PDF returned
403; the connector also had catalog specifications and the general manufacturer USB-C guide.

The 31 SSE events have consistent run IDs and contiguous sequences. Terminal snapshot, saved
GET, JSON export, and CSV identities/quantities/links/verdicts agree. Both legacy support arrays
are empty. Runtime hashes match the manifest frozen before the run. Verification used an isolated
server on port 3002 without changing the existing backend or MCP processes.

Artifacts are retained under `backend/data/evaluations/scope-cleanup-20260930-v41/`, including
the original saved run, `sensor-events.jsonl`, `report.json`, `bom.csv`, `manifest.json` and
`verification.json`. No result was manually repaired or hidden by retrying the request.

The passing badge is not evidence that every calculation passed. Ten current code checks
remain unknown: missing regulator source/operating data, incorrect multiple-reference MCU
voltage bindings, an omitted I2C return-direction record and unresolved signal/thermal operands.
The model's broad power/interface approvals exceed what those recorded checks establish.
These are retained review limitations under the existing binary policy, not silently converted
into individually verified checks. Independent practical inspection is recorded below.

### Independent practical output audit

A separate reviewer and the main agent inspected original manufacturer tables visually, using
the PDF skill. No obvious inherently incompatible functional-part choice was identified for an
ordinary indoor sensor. The ESP32's radio/controller functions and SHT40's temperature/humidity
function fit the request. At a common 3.3 V, the documented input ranges and bidirectional I2C
levels are compatible with suitable ordinary pull-ups and bus loading. This independently
established plausibility does not repair the backend's missing/bad numeric references.

The exact regulator deserves a specific qualification. The independent reviewer located the
Slkor [part page](https://www.slkoric.com/productDetail/12254697) and its linked
[AMS1117 Rev.2 datasheet](https://www.slkoric.com/upload/file/1788315374_5857.pdf), which the
backend did not acquire. Physical pages 2–3 give **135 °C/W** junction-to-ambient thermal
resistance for SOT-223, **600 mA** recommended DC output current and **750 mW** maximum
dissipation. The report instead assumes 65 °C/W and broadly approves a 1 A capacity from
catalog data. Those are not trustworthy operating assurances. The source also gives 3.234–3.366 V
under its stated output test conditions and up to 10 mA own current, rather than the report's
3.23–3.3 V window and 2 mA own-current value. Its headroom and minimum-load conditions also
need consideration during schematic design; catalog labels are not a substitute for that source.

This does not demonstrate that the regulator is unusable for the requested sensor. Treating
the full recorded 500.5 mA downstream reservation as continuous load at 5.25 V would dissipate
about 1.06 W including 10 mA own current and exceed this package's stated thermal envelope.
But Espressif physical page 29 distinguishes actual radio draw from its 500 mA supply-capability
recommendation: the listed highest Wi-Fi TX mode has 379 mA peak and 239 mA average at its test
conditions. An **independent feasibility screen**, using that 239 mA average plus 0.5 mA sensor
load, 10 mA regulator own current, 5.25 V input, 3.234 V output and the recorded 25 °C ambient,
gives about 0.535 W and 97 °C junction using 135 °C/W. That is a plausible ordinary operating
case, not a workload established by the saved backend report or a guaranteed board result.
Likewise, the report's 500 mA upstream assumption does not cover its own downstream reservation
plus regulator consumption, although that reservation is not demonstrated actual continuous draw.

The audit used cached ESP32-WROOM-32E/32UE physical pages 28–29 and SHT4x page 9, plus the
independently retrieved Slkor pages 2–3. The latter is retained as
`slkor-ams1117-audit-source.pdf` alongside the evaluation artifacts. Ordinary capacitor counts,
reset wiring, and a complete support-parts shopping list were not acceptance criteria.

**Conclusion:** the cleanup preserves a functioning natural-language-to-functional-BOM path and
the selected parts are reasonable for the stated project scope. The model's electrical report
still overstates what it established. This single attempt does not prove consistent correctness,
and the independent findings must not be described as checks the backend itself completed.
No further prompt additions, special cases, model changes, or automatic tuning cycle followed.

## Backend cleanup (2026-09-30, prompt 40)

The cleanup preserves the explicit Python workflow, Flash-Lite, resource limits and public
saved-run contract. Completed reviews have two outcomes. Unknown evidence/calculation details
are not failures, and no completed review is represented by a null verdict.

### Code review and verification

- Consolidated numerical unit conversion, named binding/read/parse/build helpers consistently,
  simplified retry and terminal-state handling, and removed unused source-fetch bookkeeping.
- Removed blanket evidence-gap-triggered correction rereads. Part changes, explicit source
  reread requests and newly introduced active support still acquire/read their sources.
- Removed rejection solely for a missing datasheet locator. Catalog identity confirmation and
  source discovery/applicability review remain; an absent source is not a component mismatch.
- Fixed malformed supplier links crashing report projection and aligned unsupported saved-base
  refinement with retrieval/export's 404 behavior. Purchase multiples use exact integer rounding.
- Retained all six checking domains, source-number binding, acquisition protections, bounded
  retries, atomic persistence and legacy readers because each has demonstrated product value.
  No new dependency, service, orchestration layer, model or acceptance gate was introduced.
- Independent cross-reviews covered the workflow, numeric checks, integration boundaries,
  API, persistence and exports. They found no blocking cleanup regressions.

Verification passed: **109 backend tests**, **21 frontend tests**, frontend typecheck and
production build, and **3 MCP tests plus build**. Unit tests use local fakes without live
models, networks or timing injection. `git diff --check` passed. `uv pip check` verified all
55 installed packages after the existing environment proved to have no pip module;
no package installation or dependency change was made.

### Fresh end-to-end attempt

One unattended attempt used the original request, without component hints or manual repair:

> Make me a temperature and humidity sensor with WiFi and Bluetooth powered by USB-C for consumer use.

| Run | Backend verdict / sourcing | Placements / BOM rows | Model calls | Input / output tokens | Duration | Corrections |
|---|---|---|---:|---:|---:|---:|
| `036695dc824148e1b64e7bdb714635aa` | checked / partial | 13 selected / 11 rows | 14 | 175,416 / 21,648 | 95.61 s | 0 |

All 11 purchasing rows have purchase links; 10 have sufficient stock in the recorded offers.
The TLV75733PDBVR regulator had zero stock. The completed review contains zero blocking failures
and seven nonblocking failed/unknown details. No provider error or quota stop occurred.
The server was isolated on port 3002; the existing application and MCP processes were untouched.

SSE sequences, terminal snapshot, saved GET, JSON export, CSV identities/quantities/links and
verdicts were checked for agreement. Runtime hashes matched the frozen pre-run manifest.
Artifacts are retained under `backend/data/evaluations/cleanup-20260930-v40/`, including the
unchanged saved run, event stream, `report.json`, `bom.csv`, `manifest.json` and `verification.json`.

### Independent practical output audit

The main ESP32-WROOM-32E-N4, SHT40-AD1B-R2 and TLV75733PDBVR choices are plausible for the
requested functions and a 3.3 V sensor board. The two 3.9 kΩ I2C pullups and two 5.1 kΩ
USB-C pull-downs are present. This is not schematic or exhaustive layout qualification.

**One concrete support-part omission remains.** C1 is the single 22 µF capacitor, but the
model claims it satisfies both the regulator's 5 V input and its 3.3 V output/module bulk
requirement. Those are distinct rails. The TLV757P datasheet's pin/application material on
physical pages 3–4 requires separate input and output capacitance. The other capacitors are
0.1 µF bypass parts and a 1 µF part already allocated to the module's EN delay. The ordinary
repair is a separate suitable input capacitor, nominally at least 1 µF and retaining the
datasheet's required effective capacitance above 0.47 µF under operating conditions.
No such repair was manually applied to the saved BOM.

The thermal report also uses the evaluation-board figure of 100.8 °C/W rather than the
ordinary JEDEC figure of 231.1 °C/W. At its recorded 150 mA average, 40 °C ambient and worst
recorded supply drop, the latter gives approximately 109 °C. That is below the device's
125 °C limit but above the report's chosen 100 °C target. This is a conditioning/report
limitation, not proof that the selected regulator cannot serve an ordinary duty-cycled sensor.

Source audit used the cached original manufacturer PDFs, including TLV757P document
`doc_84930bb4785ab3ddf29a6d1731a50c9bd37abeb9cbb91db86d476a9ff54033f0`, with relevant tables
and circuit pages visually inspected. The pipeline's passing verdict and this independent
finding are recorded separately. The cleanup confirms functioning generation and report
delivery, not that the model detects every obvious component/support error. No further
prompt-tuning, special-case checking, or architectural cycle was started.

## Frozen reliability acceptance (2026-09-30, prompt 37)

**Failed.** The [predeclared gate](reliability-plan.md) required at least 9 of 10 fresh runs
to finish checked with required placements and purchase links, and zero material false
positives under independent original-source audit. All ten attempts were made. One was
`checked`, seven were `incomplete`, and two were `issues_found`. The only checked result
failed that audit, leaving **0 of 10 results satisfying the combined acceptance gate**.
This is not a universal success-rate estimate or proof that none of the other selections
could work. Incomplete evidence is not itself electrical incompatibility.

### Method and every attempt

The five exact requests in the plan were run twice consecutively through real HTTP on
unchanged final runtime code, with no per-request hints, manually repaired results, or
acceptance-only settings. Gemini `gemini-3.5-flash-lite`, `google_genai`, provider-default
thinking, prompt 37 and numeric binding version 1 were fixed throughout. Normal limits
were 480 seconds, 30 model calls, 400,000 input tokens, 64,000 output tokens, 60 supplier
calls, 20 document acquisitions, 120 PDF page inputs, 40 placements and two corrections.
The normal source-file cache was used; no completed design was preloaded.

Every lifecycle below is `finished`. That means bounded execution ended, not that the
BOM passed. Tokens are recorded input/output usage; calls include model attempts, while
corrections count applied corrections, not every proposed or rejected correction.

| Attempt / request / run ID | Compatibility / sourcing | Input / output tokens | Calls / corrections | Seconds |
|---|---|---:|---:|---:|
| 1 / sensor-a / `ac6a1189f74b4ed393b06cac8ec6e149` | checked / available | 350,452 / 33,682 | 19 / 2 | 154.46 |
| 2 / sensor-b / `bd56358bed51476d8dc6fc28123808bc` | incomplete / available | 314,703 / 33,642 | 19 / 2 | 139.46 |
| 3 / pressure-a / `ed2ba8704d1a4b61a997336f0deda2b6` | incomplete / available | 104,681 / 9,058 | 12 / 0 | 53.22 |
| 4 / pressure-b / `45b0110842d546509b29449429bee475` | incomplete / available | 374,322 / 29,301 | 23 / 2 | 159.02 |
| 5 / button-a / `f2b272ead58641aca3a77b4b238d07f2` | incomplete / available | 307,533 / 24,941 | 24 / 2 | 135.11 |
| 6 / button-b / `ad041b0021f240f8a15f95d24a84d67c` | incomplete / available | 339,881 / 32,299 | 22 / 2 | 160.84 |
| 7 / light-a / `0466473f592e41e18f61510534c46e71` | incomplete / partial | 245,445 / 29,862 | 15 / 1 | 121.51 |
| 8 / light-b / `029c8ec7addd49e3a2715d3d5274955d` | issues_found / partial | 371,303 / 24,423 | 23 / 2 | 148.18 |
| 9 / logger-a / `78b6a2b271ff4e6580bb928d4f05c75c` | incomplete / available | 253,293 / 32,093 | 15 / 1 | 158.25 |
| 10 / logger-b / `7969892eb5674a89aa60eed17275f6d5` | issues_found / partial | 380,135 / 30,245 | 25 / 2 | 153.67 |

Totals were **3,041,748 input tokens, 279,546 output tokens, 197 model calls and 1,383.72
seconds of run duration**. Seven runs had available sourcing and three partial sourcing.
Attempts 1–9 selected every placement. Attempt 10 left its controller unselected; its nine
exported purchasing rows do not constitute a complete BOM. Every exported row had a purchase
link. Sourcing availability is a dated observation, separate from compatibility.

There were no provider-quota failures or model-timeout terminal failures in this batch.
Local RPM scheduling waits did occur. One attempt exhausted the document allowance and
another could not reserve enough input tokens for its next review; neither is a Gemini
rate-limit response. All attempts remained within the configured execution bounds.

### Independent audit of the only checked result

Attempt 1 was audited read-only by a separate Codex reviewer, independent of the backend's
production review call. The main agent also inspected the original AP2114 PDF pages visually
and independently recomputed the decisive thermal comparison. Neither audit changed the
saved record, introduced a new operating assumption, or required pins, nets or a schematic.
This is a source-based software evaluation, not hardware testing or professional certification.

The 15 placements / 11 purchasing rows contain the selected ESP32-WROOM-32E-N4, SHT40-AD1B-R2,
AP2114H-3.3TRG1 regulator and ATTEND 217B-CA05 USB-C connector, with the expected regulator
capacitors, controller enable/decoupling support, sensor decoupling, two I2C pullups and two
USB-C CC resistors. Exact catalog identities, purchase links, support values/counts, radio
functions and heater-off sensor/interface operation were substantially coherent.

**The claimed thermal pass is unsupported and material.** The saved source number used as
`theta_ja` is 50.9°C/W, but its own condition says junction-to-case. The
[AP2114 manufacturer datasheet](https://www.diodes.com/assets/Datasheets/AP2114.pdf), original
PDF page 12, identifies that number as **θJC**, not **θJA**. Page 7 lists **128°C/W θJA for
SOT-223 without a heatsink**; page 5 identifies the H variant as SOT-223. The cached original is
`backend/data/documents/doc_d20cd46c5f472fe220f3e1ffb82b2679bc37e3dd145891bfdedf0acb78089d51.pdf`.

The run records 50°C ambient, a 115°C junction target, no average-load restriction, and
0.759188 W calculated loss. The wrong parameter gives a 1.27701 W allowance and a code pass.
Using the documented junction-to-ambient parameter gives only `(115 - 50) / 128 = 0.5078125 W`.
The corresponding screening junction estimate is approximately 147.18°C, above the run's
own target. An earlier correct θJA observation was discarded for a quotation mismatch;
the incorrectly classified θJC replacement survived. Numeric binding faithfully reused the
wrong interpretation, and the model reviewer approved it using nominal-only arithmetic.

This does **not** establish that these parts necessarily overheat under every plausible use.
A different justified sustained-load condition might make the selection feasible. The saved
run did not establish that condition, so inventing it after the fact would repair the result
rather than audit it. The batch fails on unsupported material assurance even if these same
components could work in another configuration.

Other record defects include output bounds omitting applicable load/line effects, a small
output-bound arithmetic error, an inaccurate absolute-maximum-temperature note and package/
I2C-mode wording mistakes. None is needed to establish the decisive rejection. The optional
sensor heater was not required for ordinary temperature/humidity measurement.

### Failure patterns, without repairing the attempts

- **Attempt 2 — incomplete numeric/interface record.** Both corrections completed, but the
  controller-to-sensor I2C direction remained absent and the final thresholds referenced
  nonexistent `D1E2T1`. Valid threshold source numbers were available after a reread. This
  was not token, timeout or source-access exhaustion; physical incompatibility was not established.
- **Attempt 3 — acquisition limitation and unmet form factor.** The TI distributor wrapper
  contained a double-encoded HTTP destination. The local redirect normalizer rejected it
  before fetching, so this is not evidence of a TI outage. The model also selected a
  DFR0654 FireBeetle development/evaluation board despite the explicit no-development-board
  requirement. Missing operating/interface records remained, and correction gave up with
  no applied repair and substantial budget remaining.
- **Attempt 4 — ineffective source/part replacement.** The NXP sensor PDF returned 404.
  Both corrections intended a Bosch replacement, but broad supplier fallback reselected
  MPL3115A2ST1 while retaining an inapplicable Bosch source. Regulator facts and bidirectional
  interface evidence remained incomplete, including thresholds owned by the wrong device.
  Both corrections were consumed; the input budget was not exhausted.
- **Attempt 5 — repeated acquisition failures exhaust 20 downloads.** There were two
  successful acquisitions and 18 failed attempts: Amphenol 403 seven times, ON Semiconductor
  403 seven times and Microchip 403 four times. Repeated MIC5319 replacement queries returned
  the same NCP114 through fallback. Replacement clears the prior component's error history
  before selection, so it is inaccurate to say that selection knowingly ignored a failure
  still present in its context. Unsuccessful URLs are retried rather than cached as failures.
  Recovery/history loss and model repetition jointly consumed the bounded allowance.
- **Attempt 6 — passive LED modeled as an active IC.** The indicator retained `active` kind
  through replacements, creating inappropriate IC supply/logic obligations. Corrections
  chased LED documents rather than fixing the classification, invented active-style limits,
  and cited a controller radio-current fact for the LED. An empty indoor-use mapping and
  missing support review also remained. The existing passive path was not exercised; merely
  changing the classification would not independently validate the rest of this result.
- **Attempt 7 — a real divider error plus representation gaps.** TLV62569 output depends on
  `VFB * (1 + R1/R2)`, but the binder cannot derive resistor-programmed output envelopes.
  It treated the minimum adjustable output range as the delivered rail. Separately, the
  selected 100 kΩ/24.3 kΩ ±1% divider is genuinely wrong for the claimed 3.3 V rail: nominal
  output is 3.06914 V, and the documented 0.588–0.612 V feedback range with resistor corners
  gives 2.95984–3.18140 V, crossing the ESP32's 3.0 V minimum. These calculations use original
  TLV62569 pages 4 and 9, cached as
  `doc_1ba6f55dfe678d06d563acd6632f1f950a497d812270806021097b55cd81d3c4.pdf`.
  OPT3001 calls its active-mode 3.7 µA typical consumption "quiescent current"; extraction
  preserved that condition, but the binder does not accept that role as device load current.
  This particular block is a contract mismatch, not confusion with shutdown consumption.
  Additional invalid/wrong-owner references remained. The second correction repeated the
  same configuration and hit the no-progress stop after one applied correction.
- **Attempt 8 — unsuccessful recovery and an input reservation stop.** The intended
  VEML7030 replacements repeatedly fell back to the undocumented LTR-329ALS selection while
  the retained Vishay URL returned 404. The final review was not sent: 371,303 used plus
  37,210 estimated input tokens exceeds 400,000. The recorded 0.588–0.612 V failure binds
  the regulator's feedback reference as its output, not a verified physical output rail.
  Unsupported divider derivation, wrong-owner current references and missing reverse I2C
  evidence also persist. A larger cap alone has no demonstrated repair benefit here.
- **Attempt 9 — extraction omitted numeric records.** The AP2112 source was acquired, but
  all 13 extracted evidence items had empty `numbers` lists. Assembly and corrections used
  Evidence IDs where SourceNumber IDs were required, without requesting extraction repair.
  Most final unknowns cascade from these missing regulator bindings. The second correction
  was identical except its reason, producing a no-progress stop with budget remaining.
  The LED was correctly classified passive in this run. Review also failed to reconcile
  its own approximately 36 mA resistor calculation with a 10 mA rail allowance; this is not
  proof of LED damage from a catalog test current alone.
- **Attempt 10 — controller still unselected and configuration unresolved.** Repeated
  MDBT50Q-1M7V searches and Nordic-specific fallback did not produce an accepted controller
  selection. The model imposed that family constraint; the user only requested Bluetooth.
  Both corrections repeated the same searches, the second adding a source URL rather than
  considering another family. Selector explanations about stock, documentation and LoRa
  categorization do not prove the fallback RAK4631 hybrid module was electrically unsuitable.
  The other logger attempt selected a documented, stocked ESP32 module, showing a plausible
  alternative family existed, not that it appeared in this run's restricted candidates.
  Both corrections were consumed. The final regulator reread reduced ten observations to
  three, losing previously extracted operating/current/thermal facts. Regulator bindings,
  support evidence and interface evidence remained unresolved. A recorded sensor current
  in Greek `μA` was rejected even though the
  visually equivalent micro-sign `µA` is accepted, another concrete normalization limitation.
  This cannot be counted as a functional Bluetooth logger, irrespective of the nine exported
  purchasing rows or the remaining resource budget.

The attempted recoveries were also independently inspected by separate read-only Codex
reviewers. The adjustable-regulator calculation and active-mode sensor-current terminology
were checked against original manufacturer pages, not just saved model explanations.
No run was repaired or relabeled. Failure causes overlap; this is not an exclusive statistical
attribution of each failure to either the model or infrastructure.

### Integrity, decision and stop condition

All ten terminal SSE snapshots agree with saved JSON, HTTP retrieval, JSON export and every
CSV BOM field. Runtime SHA-256 fingerprints before every attempt and after the batch match.
The same model configuration and resource limits are recorded in all ten runs. Final local
verification passes **97 deterministic tests** and `git diff --check`. These demonstrate
useful implementation properties, not trustworthy source interpretation or BOM correctness.
The isolated evaluation backend on port 3002 was stopped after export verification; the user's
existing backend/MCP services and unrelated frontend work were left untouched.

The full manifest, untouched runs, SSE events, per-call observations and HTTP exports are in
ignored `backend/data/evaluations/reliability-acceptance-20260930-v37/`. `batch.json` contains
all run IDs, exact requests, unresolved findings, budgets, usage and verification results.
Development attempts below remain separate and were not substituted for acceptance failures.

**Decision:** the present model/workflow combination has not demonstrated reliable autonomous
compatibility-checked BOM delivery, even within this small USB sensor/control scope. Earlier
conditionally acceptable examples remain evidence of possibility, not consistency. The evidence
does not support claiming that infrastructure is finished and only model intelligence remains,
nor that removing more gates or merely increasing budgets would solve the problem. Source
meaning and review errors coexist with real representation and recovery limitations. This
batch does not establish that Flash-Lite can never work or that a larger architecture is needed.

Per the user's instruction, implementation is **paused**. No prompt additions, special cases,
model/settings changes, gate relaxation or further fix-and-retest cycle followed this batch.
Only evaluation/status documentation was updated after runtime freeze.

## Source-bound calculation reliability work (2026-09-30, development)

The predeclared [acceptance batch](reliability-plan.md) is ten fresh requests on unchanged final
code, at least nine usable checked results, and no materially false checked output under an
independent original-source audit. Development trials below do not count toward that gate.

Numeric binding version 1 retains extracted number roles, ownership and conditions instead of
letting assembly rewrite their numerical meaning. Code resolves output tolerance, supply-scaled
logic limits, linear input headroom and downstream current, and includes regulator own current
in thermal loss. Public quantity fields remain materialized; legacy saved runs remain readable.
Independent code review found and reproduced a direct-current bypass for linear inputs; those
inputs now always use their actual downstream demand plus own current. Local regression coverage
includes this bypass and real correction-helper flow that adds a missing regulator.

| Development version / request / run | Lifecycle / compatibility / sourcing | Input / output tokens | Calls / corrections | Seconds |
|---|---|---:|---:|---:|
| 32 / sensor / `1b1a1397b9584eda8a7df3bda9dac587` | error / incomplete / available | 48,896 / 15,268 | 7 / 0 | 118.85 |
| 33 / button / `f1486b9962544031bea132b214bdd61c` | error / incomplete / available | 63,695 / 12,438 | 8 / 0 | 36.42 |
| 34 / button / `ca04d688a2b54ef4afcb45d672323ec6` | finished / incomplete / partial | 228,266 / 23,391 | 19 / 2 | 106.05 |
| 34 / sensor / `ea49cc953d884ddba57214abad82c6d7` | finished / incomplete / available | 342,618 / 37,604 | 22 / 2 | 145.80 |
| 35 / sensor / `5a05a3db70014b6ab181db744223c224` | finished / issues_found / available | 269,266 / 31,816 | 16 / 2 | 154.59 |
| 36 / sensor / `89e48a15282746099dee3ea7a3a843b9` | finished / issues_found / available | 255,494 / 33,550 | 15 / 2 | 123.65 |

The sensor run exhausted both 45-second attempts interpreting the SHT4x source. A targeted
diagnostic of those same pages with a 90-second client timeout still failed with a provider
`504 DEADLINE_EXCEEDED`; two attempts took 90.45 seconds total. This does not support increasing
the production timeout. These pages/bytes also succeeded in earlier named runs. No production
timeout, retry allowance or model change was made.

The button run exposed a new provider `400 INVALID_ARGUMENT` at assembly. Targeted replays
isolated the response schema. Making all quantity fields required still failed (0.95 s).
Additionally removing the calculation enum allowed generation (8.60 s), but yielded invalid
calculation names, so that workaround was not retained. Instead, removing only code-produced
`Quantity.basis` and `evidence_ids` from the model schema preserved the calculation enum and
returned a valid proposal (8.41 s, 11,975 input / 2,961 output tokens). This simpler ownership-aligned
contract is prompt 34. Both fields remain in saved/public quantities; extraction still supplies
source-number basis. No generic provider-schema transformer was introduced.

Version 34 reached complete review/correction paths. Its button run could not source a required
capacitor or read the selected regulator's source. Both corrections repeated unsuccessful work;
the catalog also described a 300 mA regulator against the extracted 340 mA radio peak. Two
targeted correction replays with clearer diagnostics still did not resolve both problems. Better
error messages alone are not demonstrated to make repair reliable.

The sensor run exposed two representation issues: a signed negative lower output tolerance and
model-authored calculation labels inconsistent with their correct source-number references.
Version 35 accepts the signed lower tolerance and derives each calculation from its destination
and topology, removing another model choice. Read-only recomputation then reveals a **real thermal
failure**, not an accepted BOM: AP2114H dissipation is about 0.759 W against 0.469 W at the recorded
50°C ambient, 110°C target and 128°C/W package condition. No average-workload restriction was
recorded. The original electrical table also limits initial ±1.5% output accuracy to light load;
the record omitted applicable load/line effects. Independent review did not repair or approve it.
The SHT4x pages that previously timed out succeeded in this run, further weakening the case for
a local PDF defect or a larger client timeout.

Version 35 also reached the real thermal gate: AZ1117C loss was 0.796 W against a recorded
0.500 W allowance, with no adopted average workload. Its reviewer wrongly approved nominal-only
arithmetic and ignored the recorded junction target; code kept the failure. Both corrections
addressed reference bookkeeping first. Two remaining representation problems were isolated:
supporting USB-guide references displaced a valid external-supply assumption, and redundant
output/dropout references on a computed regulator input minimum were rejected instead of using
the actual derived operands. Resolving these does not remove the thermal failure.

Independent local review also found and closed two undercount paths: assumption-only zero own
current despite available regulator evidence, and overwriting a conservative total average-current
estimate with one smaller source number. Source recovery now preserves explicit URL hints and lets
missing-source requests reach the existing bounded alternate-source discovery, including explicitly
requested passive sources. These are local fixes, not evidence of successful autonomous completion.

Version 36 attempted an average-current thermal repair but still ended at 0.479 W against a
0.353 W allowance for its AP2112K. Its first correction cited multiple constituent currents in
a direct operand that supports one numeric source, temporarily making thermal unresolved;
the final correction restored a numeric failure. It also substituted an average-current source
for peak demand. Prompt 37 separates explicitly documented average-current facts from peak/design
demand and accepts qualitative evidence as context for assumed upstream supplies. Source-owned
device ratings remain exact numeric bindings. The multi-reference thermal limitation was recorded,
not expanded into another repair. The user's instruction is to freeze and evaluate, then pause
if the gate is missed. No model, thinking setting, resource limit or orchestration change was made.

Artifacts are in ignored `backend/data/evaluations/reliability-dev-20260930-v32` through `-v36`.
The targeted proposal is diagnostic only, not a repaired or accepted BOM. Failed-call usage
retains reservations where the provider did not return usage. Local verification currently
passes 97 deterministic tests. The unchanged prompt-37 acceptance batch is recorded above;
it failed the declared gate and further implementation is paused.

## Reliability and representation scope (2026-09-30)

This pass removes demonstrated representation blockers without claiming that a source-backed
model review is infallible. It retains Flash-Lite, the explicit Python workflow, two correction
rounds and all resource ceilings from the budget pass. No new service or dependency was added.
The final prompt version is 31.

Implemented changes:

- A source-reviewed single-module capability need not invent a second purchased participant.
  A one-ended I2C bus remains unresolved, as do missing electrical directions and numeric conflicts.
- Passive current-only rail entries need not invent IC operating-voltage intervals. Their
  current stays in the sum, with a current rail/load review of ratings and current limiting.
  Active/module drivers of passive loads need an applicable driver/load review, not passive
  VIH/VIL values. Supplied numerical limits still take the normal checks. Active devices are
  not exempted, and reviewed catalog evidence does not replace active-device documents.
- An empty requirement mapping remains unknown instead of aborting correction. Empty catalog
  searches now report the actual failed query so correction can choose a different part/query.
- Review citations to protected source-support observations resolve one hop to their source
  evidence. Unknown references, empty underlying lists and invalid underlying references remain
  blockers. Editable fulfillment records and numeric operands do not use this normalization.
- Extraction explicitly returns an applicability boolean plus explanation. A live failure exposed
  that a nonempty explanation saying a Bosch document did **not** apply to an NXP sensor had
  previously authorized its facts. Negative/unestablished owners now lose those observations
  and their inapplicable support needs; unrelated invalid references remain visible blockers.
- Catalog-identified USB-C connectors receive the existing manufacturer Type-C guide through
  ordinary acquisition/extraction, preserving their own source lead. No resistor values, parts
  or port roles are inserted in code. This addresses observed missing CC support evidence.
- A model read timeout uses the existing single transient retry, not another retry loop or
  larger allowance. Provider quota failures still stop immediately.

An experimental `manufacturer_guidance` substitute for numerical interface checks was removed.
Its only live use approved logic compatibility from shared supply voltage and protocol names,
without the intended explicit manufacturer basis. It had no independently accepted positive
example; the accepted sensor below uses numerical checks. The experimental field is readable
in old diagnostic snapshots but hidden from new proposals/reports and ignored by checks.

All trials below are fresh natural-language requests with no manually supplied parts/pages,
one board and US/USD sourcing. They use isolated port 3002, leaving the existing UI backend
on 3001 untouched. Runtime artifacts are in the named ignored `backend/data/evaluations/`
directories, with saved runs, complete SSE streams and observation-only call measurements.
They are evaluation data, not live unit tests. Failed attempts remain recorded, not replaced.

| Version / request / run | Lifecycle / compatibility / sourcing | Input / output tokens | Calls / corrections | Seconds |
|---|---|---:|---:|---:|
| 28 / sensor / `75b976393779499da8e60f9737a9c961` | error / incomplete / available | 54,232 / 8,279 | 7 / 0 | 76.69 |
| 29 / sensor / `e92a5685c99f486f850ac23eefc01982` | error / incomplete / available | 48,877 / 13,018 | 7 / 0 | 116.33 |
| 29 / pressure / `524993a8c0994b05ae9e930717635af7` | finished / incomplete / available | 266,347 / 27,901 | 21 / 2 | 184.72 |
| 29 / button / `7161444311314a44aa9733c5440e1f95` | finished / incomplete / partial | 265,088 / 31,225 | 21 / 2 | 182.45 |
| 30 / sensor / `36b821a2f88142259a4b46604338a3e1` | finished / checked / available | 243,761 / 30,969 | 16 / 2 | 133.91 |
| 30 / pressure / `3c4bf6c1a66b4a0180650b9f88587764` | finished / incomplete / partial | 295,893 / 27,702 | 23 / 2 | 128.47 |
| 30 / button / `31cccfe453604507a40b7ef9b907b604` | finished / issues_found / available | 205,244 / 25,890 | 18 / 2 | 107.89 |
| 31 / sensor / `bba2271a22804a02a1e291e5d98b91bf` | error / incomplete / available | 183,245 / 21,747 | 12 / 0 | 163.08 |
| 31 / sensor repeat / `e5aec768a45a42f49c377a633d7d6c27` | finished / checked / available | 207,436 / 25,365 | 15 / 1 | 122.24 |

The queries are the exact sensor, pressure and button requests quoted in the budget section.
The first two source timeouts occurred before assembly. An independent PDF audit found the
same original SHT4x bytes/pages and production page slices used by earlier successful reads;
there was no demonstrated local PDF-generation defect. The second trial exhausted both
45-second attempts. Usage for failed attempts retains reservations, not confirmed provider
billing. Artifact directories are `scope-20260930`, `scope-20260930-final`,
`scope-20260930-verified` for the version-29 pressure/button pair, and `scope-20260930-v30`.
Version 31 artifacts are in `scope-20260930-v31`. Its first trial completed source extraction
and selection but exhausted both model attempts during whole-BOM review. This is a read-timeout
failure, not a completed compatibility verdict or quota-exhaustion response. One bounded fresh
repeat was made to exercise the final correction/review path; both trials remain recorded.

The version-29 pressure run exposed the negative-applicability bug and omitted both USB-C
CC resistors. It was not one cosmetic citation away from approval. The button run exposed the
passive LED supply/threshold representation issues, but also lacked regulator evidence and
excused a 344 mA peak load on a claimed 300 mA regulator. Its incomplete status was warranted.

**Version-30 sensor accepted conditionally after independent original-source inspection.**
All necessary support parts are present, including two CC resistors, separate regulator
input/output capacitors, ESP32 EN support, sensor decoupling and I2C pullups. The selected
parts have feasible supply and bidirectional logic compatibility under the recorded 500 mA
USB source, 250 mA average load and 40°C ambient assumptions, with ordinary heater-off
sensor measurement. It does not use either the experimental module-guidance path or passive
exceptions. It still recomputes as checked with the final version-31 checks.

This is not an error-free engineering report. The regulator review uses light-load output
tolerance and nominal-only thermal arithmetic; independently including documented variation
and quiescent loss still gives about 0.54 W against the recorded 0.56 W allowance. A sink-test
voltage is mislabeled as an ESP32 maximum, but the actual documented limit still satisfies
the sensor at rail corners. EN figure labels are confused, while the purchased 10 kΩ/1 µF
parts match the manufacturer prose. These are nonblocking record-quality defects for this
conditional component selection, not evidence that numerical explanations can be trusted blindly.

The version-30 pressure result remains independently unacceptable. Its visible code blocker
was a support-observation ID used where an evidence ID was expected. Normalizing that citation
does not establish its 150 mA sustained workload: its cited assumption only describes the USB
source, and the documented continuous-TX workload exceeds its chosen thermal target. Its
interface review substitutes shared supply voltage for logic evidence and retains the previous
sensor's name/address. Removing the experimental interface exception restores the missing
direction blocker in a read-only replay. No saved result was relabeled.

The version-30 button BOM omitted its regulator and assigned 4.75–5.25 V to a module rated
for 3–3.6 V; the code correctly retained a failure. Its LED still carried unsupported explicit
IC-style voltage bounds, which the passive exception deliberately does not waive. These are
material/model-record failures, not reasons to suppress applicable checks.

**The final version-31 sensor repeat also has a conditionally acceptable component selection.**
It finished after one correction with 16 placements / 13 purchasing rows. Its own report has
inaccurate 250 mA controller and 300 mA converter peak budgets despite source-observed 379 mA
radio peaks. Correcting the USB peak to approximately 387 mA still fits the recorded 500 mA
source and 1 A regulator. It also uses the 100°C/W copper-assisted thermal figure without
declaring that copper condition. Conservatively using the documented 125°C/W figure, a widened
3.21 V output floor and 6 mA quiescent current gives about 0.44 W against 0.48 W allowance at
the **already recorded** 200 mA average and 50°C ambient bounds. No replacement part, extra
heatsink or new duty schedule is required to establish that feasible conditional selection.
This does not validate unrestricted continuous transmission or the erroneous peak/thermal
records. An explicit average-load bound is an operating assumption; inventing one after a
run or treating an unrelated USB-source assumption as a workload restriction is not equivalent.
The repeat also includes an unnecessary but compatible reset switch. This is a selection-quality
defect, not missing required support or an electrical mismatch.

Final local verification passes all 79 deterministic tests and independent adversarial code
review. Replaying 50 earlier saved/budget runs changes only one formerly single-ended BLE
capability check from unknown to pass. Both historical accepted BOMs keep their outcomes.
All nine terminal SSE snapshots agree with saved records and GET/JSON/CSV projections,
ignoring only the now-hidden experimental interface selector in older public snapshots.
Both version-31 records were also checked over actual HTTP. No original result was repaired
or relabeled. The user's existing UI backend was left running and needs a restart to load
these changes; unrelated frontend work was preserved.
The small live sample demonstrates two accepted unattended sensor BOMs, not consistent success across
the supported product scope. Remaining model selection, source interpretation, workload and
self-review errors are material; loosening more checks would not establish reliability.

## Input budget evaluation (2026-09-30)

Reported UI run `89ef5bbcb03e42149991f3b880285623` stopped before its final review
at 277,443 input tokens, 31,022 output tokens, 19 calls, two corrections and 137.07
seconds. Its 15 placements produced 12 available purchasing rows. The seven current
unknown checks were four requirement-review coverage checks, whole-review coverage,
and two interfaces awaiting source-backed review. They were not seven demonstrated
hardware faults, but the missing review cannot be assumed to pass. The saved record
still needs scrutiny of regulator operating bounds and thermal-workload assumptions.

Reconstructing that review from the unchanged saved design, cached original pages,
and production context builder gives a **44,246-token input reservation**. Only
22,557 remained, so admitting even that first review required a cumulative 321,689.
It included 13 original PDF pages and one HTML page. The obvious duplicate payload
was about 2,972 characters, approximately 991 estimated tokens, far short of the
21,689-token shortfall. Existing code already groups identical candidate sets,
deduplicates pages, omits duplicate extracted PDF text during review, and reuses
unchanged source observations. No context representation was changed.

The default input ceiling is now **400,000**, with every other limit, the model,
prompt version 27, and evidence/compatibility check unchanged. Two reviews of the
target's measured size would require a cumulative 365,935 before extra pages or a
schema retry. The second review is an existing bounded source-follow-up path, not
a new correction round. Earlier prompt-19 and prompt-21 recordings also show this
follow-up review blocked by the old cap. 400,000 is practical headroom for this
observed path, not a calculated optimum or a promise that every run can finish.
Existing runs are not rewritten; refinements continue to inherit their parent's
recorded limits. Fresh generations use the new default after backend restart.

An independent local replay sent the reconstructed context through the real gateway
with a local model fake. At 300,000 the gateway refused before invoking the fake and
left usage unchanged. At 400,000 it admitted the review. Neither replay changed the
compatibility badge or established engineering correctness. All 70 backend tests pass;
the existing atomic token-reservation test now covers input as well as output caps,
and one new local-fake regression covers assembly selection scope and correction retries.

Fresh HTTP/SSE trials use Gemini 3.5 Flash-Lite with provider-default thinking, one
board, US/USD, no parent run, no manually supplied part or source-page selections,
and the same 400,000-token default. A separate loopback evaluation server preserves
the already-running UI backend. Temporary observation-only instrumentation records
per-stage estimates, usage and correction/review outputs without changing requests.
Local artifacts are under `backend/data/evaluations/budget-20260930/`, including
`runs/`, four `*-events.jsonl` streams and `calls.jsonl`; these remain ignored runtime
data, not live unit-test fixtures.

| Request / run | Lifecycle / compatibility / sourcing | Input / output tokens | Calls / corrections | Seconds |
|---|---|---:|---:|---:|
| Exact sensor request / `382c202a876848ccaae7e4100f572605` | error / incomplete / partial | 81,572 / 12,470 | 11 / 0 | 63.21 |
| Wi-Fi pressure sensor / `f769013a1a764cfb87ca5b402b05245e` | finished / incomplete / available | 249,621 / 31,016 | 17 / 2 | 136.64 |
| Bluetooth button remote / `a792223122d34880a1fa47e44ed81355` | finished / incomplete / available | 207,587 / 26,886 | 15 / 2 | 114.00 |
| Exact sensor repeat / `745b2857730a4f0f8b103f25fd9c9c8e` | finished / incomplete / available | 386,977 / 30,026 | 25 / 2 | 156.67 |

The exact request is `A temperature and humidity sensor with Wi-Fi and Bluetooth,
powered by USB-C (5V) for indoor use.` Its first fresh trial selected a different
controller assembly than the reported UI run and stopped when a correction supplied
an empty requirement-to-component mapping. It also lacked usable controller evidence.
This is a separate model-output failure, not input-budget exhaustion. It is retained
as a failed trial, and the exact request was repeated once because the first attempt
did not exercise a full correction cycle.

The pressure request is `A USB-C (5V) powered indoor air pressure sensor with Wi-Fi
for data logging. Use a board-mountable controller module, not a development board.`
Both direct corrections and the final review ran. Four remaining signal checks cite
controller evidence for sensor limits. The first correction improved mapping and
added the missing reverse direction but unnecessarily duplicated per-wire records;
the second still did not supply sensor-owned evidence. A new 3 A USB-source claim
was also not justified by the original source assumption. The final incomplete
status is appropriate. No source rereads or assembly reruns occurred in correction.

The remote request is `A USB-C (5V) powered Bluetooth button remote for indoor use,
with one pushbutton and a status LED.` Both direct corrections and the final review
ran, but LED source acquisition failed and repairs continued to reuse wrong-owner
citations. A one-ended radio capability was unnecessarily modeled as a board
interface; a switch signal bound also lacked an applicable basis. The second repair
was largely ineffective. These are evidence/representation problems, not extra
orchestration rounds or evidence requirements introduced by this budget change.

### Avoidable selection retries and final adjustment

The exact-request repeat exhausted even the 400,000 input allowance before its final
review. Its next review needed a 36,344-token reservation, or 423,321 cumulatively.
The stage trace exposed an unnecessary retry: after an explicit correction failed
to select resistor R3 with both its narrow and broad queries, assembly repeated
both unchanged searches. Assembly cannot replace an existing component specification,
so this was not selection work for a newly proposed part. Those two calls consumed
**39,288 input tokens**, two model calls and two supplier calls. Removing them from
that recorded trajectory would leave room for the review at 384,033 reserved tokens.
This arithmetic is a counterfactual admission check, not a claim that a fresh review
will pass or that subsequent model output would be identical.

The second and only other runtime change is to select **actually new placement IDs**
after assembly. Initial selection and explicit correction still search all pending
placements with the existing narrow/broad attempts. A repeated existing ID in an
assembly proposal does not count as new. No prompt, context compression, orchestration,
retry allowance, source requirement or compatibility check was changed. The regression
failed on the old implementation and passes with this fix, including successful
selection of a new support part and later correction of an existing failed part.

The final fresh sample consists of the exact sensor request and the pressure request,
using both adjustments. Its separate runtime artifacts are under
`backend/data/evaluations/budget-20260930-final/`. The four cap-only diagnostics above
are retained, not replaced by the final sample.

| Request / run | Lifecycle / compatibility / sourcing | Input / output tokens | Calls / corrections | Seconds |
|---|---|---:|---:|---:|
| Exact sensor / `185954cd4b284c61ab383c11a310aba3` | finished / incomplete / available | 326,933 / 32,610 | 20 / 2 | 146.61 |
| Wi-Fi pressure sensor / `c49322e79475467cbca1e887e5750b90` | finished / incomplete / partial | 243,047 / 22,980 | 20 / 2 | 98.04 |

Both final runs completed two corrections and their final review without exhausting
any run budget or encountering provider quota errors. The sensor's final review
started at 297,916 input tokens with a 33,608-token reservation, requiring 331,524
cumulatively. Its preceding assembly would already have needed 301,061 reserved
tokens. This is fresh evidence that 300,000 could block permitted work even after
removing the duplicate selection. The pressure's final review required 247,958
reserved tokens, within either cap. They used 15 placements / 12 purchasing rows
and 12 placements / 8 purchasing rows, respectively.

The sensor's final correction replaced its regulator after a thermal failure.
The replacement NCP1117DT33T5G datasheet returned HTTP 403; no usable replacement
source was found. Old regulator evidence was correctly invalidated rather than
inherited. The final model review returned pass findings, but code checks retained
11 unknowns covering missing regulator/support evidence, electrical and thermal
bases, and invalid review references. This is a material evidence failure, not
an approved BOM awaiting cosmetic cleanup. All parts were already selected before
the last assembly, so the selection change did not cause these gaps.

The pressure trial never selected its BME280 sensor. Both explicit corrections
still attempted narrow and broad catalog searches, but returned no usable candidate.
It retained 11 unknowns, including sensor requirement/supply/interface checks and
missing regulator/support citations. Its repeated source-selection calls were the
existing bounded additional-source attempt following a failed connector download,
not new orchestration or a consequence of the selection fix.

All six terminal SSE snapshots match saved records, GET and JSON exports, with
matching CSV and ordered event sequences. The four diagnostic API checks used the
local Flask test client; both final runs were also verified through actual HTTP.
Independent code review and all 70 deterministic backend tests pass. The existing
UI backend was not restarted; it must restart to load the new code/default. Original
saved results were not repaired or relabeled, and unrelated frontend work was left intact.

**Conclusion:** retain the 400,000 default plus the small duplicate-selection fix.
The final sample validates budget admission through two full correction/review
cycles, not reliable BOM correctness. None of these six trials produced a checked
BOM. Remaining catalog, source-access and model-citation failures warrant separate
work; another budget increase would not resolve them. This small sample does not
establish a success rate or guarantee completion of every supported request.

## BOM-only scope implementation and verification

### Backend cleanup verification (2026-09-14)

The [cleanup review](cleanup-review.md) records the code/state/test changes and the
preserved architecture. Local verification passes: 69 backend tests, three MCP tests,
both TypeScript builds, frontend typecheck, lint/format checks, and saved-result replay.
The prior accepted `149dc533` BOM still produces identical checks and purchasing rows.
**Prompt 27 produced a fresh independently accepted unattended BOM under its saved
operating assumptions.** Earlier failures, including a falsely checked result, remain below;
this is not a measured reliability rate or approval of every model explanation.

Every trial below used only the original sensor query, Gemini 3.5 Flash-Lite with
provider-default thinking, no parent/manual component or page hints, and unchanged limits.

| Prompt / run | Calls; input / output tokens; seconds | Result and reason |
|---|---|---|
| 19 / `6a8325fc8b074137add0be47fa2767c3` | 19; 265645 / 31977; 134.70 | Incomplete/partial: protected source reference unresolved; final review input allowance exhausted. Actual support and USB-current accounting also need repair. |
| 20 / `a0c328a76097449bae4358e50b2226e9` | 15; 179664 / 19815; 102.28 | Error/issues_found/available: two malformed review responses. Exact UMW regulator stability with selected ceramic output support remains unestablished. |
| 21 / `0a11e3c9e0f04a2584c8a1c0a65a2669` | 17; 269250 / 30388; 153.36 | Issues_found/available: model's thermal repair made the inequality worse; final review allowance exhausted. Parts are plausible, but the saved target fails. |
| 22 / `f91b8de5cdbd4546b1264acc79a38e6d` | 12; 135439 / 17522; 86.85 | Error/incomplete/partial: direct configuration rejected because C1 remained unselected. The 300mA regulator was also wrongly approved for an acknowledged 379mA radio peak. |
| 22 repeat / `aa819051ce8d4800b120ebadebba7fed` | 6; 43885 / 9417; 33.53 | Error/incomplete: provider HTTP 429 during extraction; no completed BOM. The four selected primary parts have offers, not a fully sourced finished design. |
| 23 / `8796184336204f5eadc183425f2398e5` | 18; 182342 / 25031; 113.97 | Incomplete/available: unsupported controller input limits remain. Independent review found a plausible integrated board, but its chip datasheet was misused as board-output evidence and an unnecessary separate USB-C entry has only one CC resistor. |
| 23 repeat / `f05aee806a5849009d378ceeb655dee7` | 17; 207534 / 26297; 110.79 | Checked/available, **rejected independently**: a single C1 is assigned to both regulator input and output, and UMW regulator stability with the selected ceramic support is unestablished. This is a model-review false positive. |
| 24 / `94cafa44ca164db68825516680e5a11e` | 18; 249622 / 31476; 131.34 | Incomplete/available: invalid model finding references and an unresolved external-programming interface record remain. Separate regulator capacitors are appropriate, but independent review again finds only one external USB-C termination resistor. |
| 25 / `9942971798e04514be96af41ccd88624` | 17; 268932 / 31279; 122.11 | Issues_found/available: both USB-C terminations and separate regulator capacitors are present, but saved thermal loss exceeds its allowance. One valid source quotation was rejected because the model mistyped its document ID. |
| 26 / `c08ce0ca501347e98b646f2073fa1749` | 17; 245724 / 30683; 117.80 | Incomplete/available: source identity is correct, but model table-text quotations were rejected and corrections left device limits uncited. Independent review still finds unestablished UMW ceramic-output suitability and inaccurate module-support accounting. |
| 27 / `29c85ccd86234aedb40010b7ce754d16` | 14; 190458 / 23118; 104.95 | Checked/available, **accepted independently under saved assumptions**: 15 placements / 12 MPNs, $9.76. Separate support parts, both CC terminations and exact regulator ceramic/thermal suitability verified. Nonblocking model-record errors remain explicitly documented. |

See the [independent original-source audit](cleanup-source-audit.md) for calibrated
part/configuration findings. None of these records was manually repaired. Local SSE
recordings are `data/evaluations/prompt19-cleanup-events.jsonl`, `prompt20-cleanup-events.jsonl`,
`prompt21-cleanup-events.jsonl`, `prompt22-cleanup-events.jsonl`, and
`prompt22-cleanup-repeat-events.jsonl`. Saved/GET/JSON/CSV/SSE purchasing rows, findings and
outcomes agree for these five trials and the accepted baseline.
Both subsequent prompt-23 recordings (`prompt23-cleanup-events.jsonl` and
`prompt23-cleanup-repeat-events.jsonl`) have exact terminal-SSE/saved/GET/JSON equality
and matching CSV purchasing quantities. Their code findings also match `da37c00` exactly;
the false-positive review is not explained by a weakened or changed arithmetic gate.

Broad prompt shortening was backed out: prompt 22 restored the baseline's detailed
stage wording in one module, sharing assembly rules with correction. Concrete cleanup
fixes retained include candidate order-cost consistency, numeric microfarad glyph matching,
actionable redacted schema retry feedback, and keeping semantic review-coverage checks in
one code path instead of rejecting useful partial findings at schema parsing. The terminal
SSE path no longer resaves the same error snapshot and changes its timestamp after emission.

One tiny quota diagnostic after the prompt-22 repeat also returned HTTP 429. The provider named
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, model `gemini-3.5-flash-lite`, quota
value **500**. This is exhausted daily request quota, not just an inferred transient failure.
Calls stopped until the midnight-Pacific daily reset. A tiny same-model diagnostic then
returned HTTP 200 and live verification resumed. Prompt 23 excludes direct configuration
from the correction schema while a selection is missing, routing that demonstrated invalid
response through existing bounded schema recovery. No stronger model, paid fallback or
extra budget was used. At that point fresh positive acceptance remained open; preserving
the historical positive case was not a substitute for that verification. The two prompt-23
post-reset trials finished without quota errors. Model interpretation/review accuracy,
not credentials or current quota availability, remained the limitation. No further instruction was added for the
capacitor double allocation: the existing assembly prompt already forbids that exact behavior.

Prompt 24 makes one navigation-only change: the existing page-preview matcher recognizes
functional-description and input/output-capacitor text. In the UMW source, this surfaces the
explicit output-capacitor requirement instead of only the paragraph's tail. The original page
was already requestable; this improves discoverability, not proof that previewing caused
the missed requirement. No prompt, electrical check, reading budget or retry was expanded.
That trial has exact terminal-SSE/saved/GET/JSON equality (73 ordered events) and 11 matching
CSV purchase rows. Its original snapshot was not changed.

Prompt 25 replaces the existing USB source lead with Espressif's short manufacturer
[USB-C guide](https://docs.espressif.com/projects/esp-iot-solution/en/latest/usb/usb_overview/usb_typec_hardware_guide.html).
The prior forum's singular-resistor discussion was ambiguous about physical quantity.
The replacement explicitly distinguishes device/sink support, resistor values, and default
versus advertised current. Both root and independent review read the complete guide; the
existing downloader exposes its relevant prose. It remains general guidance, not an exact
connector rating. No prescribed part list, automatic electrical rule or additional source
allowance was added. The TI primer was considered but not used because it omits the numeric
termination value.

Prompt 26 removes that unnecessary ID-transcription task: the existing single-source
extraction schema supplies the caller's document ID and hides it from model generation.
An explicitly conflicting ID is still rejected; saved evidence retains the ID and the
existing quote/page/owner checks remain intact. Source-support document IDs likewise stay
caller-owned. A short local omission/conflict/persistence regression covers the behavior.
The broader correction-mode restriction considered during diagnosis was deferred in favor
of removing this demonstrated failure at its origin. No additional retry was introduced.
The live provider accepted the simplified schema, and saved evidence retained correct document
IDs. The prompt-26 terminal stream/saved/GET/JSON snapshots match exactly (69 ordered events;
10 CSV purchase rows). Final read-only comparison of all 42 terminal saved runs produced
identical baseline/current code findings. This does not turn the failed live trial into an
accepted engineering result: the model still omitted relevant source material and misclassified
visual table observations.

Prompt 27 moved existing text-versus-visual quotation instructions into the evidence field
descriptions and removed their duplicate extraction-prompt wording. Regulator reading now
explicitly includes application/component-selection prose about capacitor type and stability,
not just the electrical table and reference circuit. No source is automatically accepted or
read, and no reading/retry budget or electrical check changed.

The fresh run completed checked/available with no rejected observations. Independent source
review accepts its actual selected parts under the saved 150mA sustained load and 50°C ambient:
the exact SOT-223 regulator, ceramic support and source-based thermal estimate are compatible.
This does not endorse the model's inaccurate peak-current number, output-envelope decimals,
duplicate resistor interpretation or contradictory reviewer thermal explanation. Those errors
are retained explicitly in the audit; correcting their explanations requires no different
parts or operating conditions. No saved record was manually repaired.

Final read-only replay of all 43 terminal records gives identical code findings, purchasing
rows, CSV and derived outcomes versus `da37c00`. Prompt 27's 66 ordered SSE events terminate
in a snapshot identical to saved/GET/JSON output, and HTTP CSV matches the exported record
byte-for-byte. The scoped cleanup acceptance is complete. General model reliability is not
qualified by this success, and the earlier false-positive checked result remains a failure.

### Earlier autonomous-completion baseline (2026-09-14)

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

## Historical implementation fixes and then-remaining verification

This section records the earlier prompt-4–6 phase before the BOM-only alignment and
accepted baselines. Its unresolved-goal statements describe that phase, not current
cleanup status; see [backend cleanup verification](#backend-cleanup-verification-2026-09-14).

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
