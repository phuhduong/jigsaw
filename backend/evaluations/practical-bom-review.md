# Practical BOM acceptance pass

Completed 2026-09-30 after the user accepted a bounded reassessment of what makes a useful
BOM for this free side project. This is not another architecture or model-selection exercise.

## Working objective and stop condition

Review all ten frozen prompt-37 BOMs for actual component suitability, make only small
changes justified by those observations, then run three fresh requests on unchanged final
code. Keep Flash-Lite, resource limits, the API and the product scope unchanged. Preserve
all attempts and the original saved results. Stop after the fresh sample and its review;
do not automatically start another optimization cycle.

The practical question is whether the selected parts can reasonably fulfill the requested
functions together, with necessary support components and purchase links, under ordinary
disclosed operating conditions. An imperfect explanation or bookkeeping record does not
by itself make the component list unsuitable. A material unknown remains visible, and an
actually missing function or incompatible part still needs a repair. No schematic, pin plan,
exhaustive operating-mode proof or flawless numerical narrative is required.

Report practical suitability separately from the pipeline's existing compatibility status.
Do not relabel an old run, manually repair an evaluation BOM, or treat an independently
identified operating caveat as something the pipeline already established.

## Fresh sample declared before execution

One new run for each request, in this order, with no supplied parts or source hints:

1. A temperature and humidity sensor with Wi-Fi and Bluetooth, powered by USB-C (5V) for indoor use.
2. A USB-C (5V) powered Bluetooth button remote for indoor use, with one pushbutton and a status LED.
3. A USB-C powered indoor ambient-light sensor that reports readings over Wi-Fi. Use board-mountable parts, not a development board.

Record run IDs, practical suitability and caveats, pipeline status, sourcing, tokens, calls,
corrections, duration and saved/streamed/export consistency. This small sample does not
estimate a general success rate.

## Review and changes

The earlier strict evaluation remains intact in [results.md](results.md). Independent
read-only reviewers examined the actual selections, original cached manufacturer pages,
ordinary-use support and purchasing records. No historical snapshot was changed.

### Existing ten BOMs

| Attempt / run prefix | Practical suitability | What actually matters |
|---|---|---|
| 1 / `ac6a1189` / temperature-humidity | Usable candidate, no part changes | ESP32/SHT40/AP2114 and support are coherent for intermittent telemetry, heater off. The saved thermal approval is wrong. A disclosed 200 mA sustained average at 50°C gives about 102°C junction with the correct thermal parameter; this practical caveat was not established by the pipeline. |
| 2 / `bd56358b` / temperature-humidity | Usable candidate, no part changes | Its already recorded 100 mA duty-cycled average and 40°C ambient fit the AP2112. Support is complete. Invalid numeric IDs and the absent reverse I2C record do not make the selected parts incompatible; original thresholds support both directions. |
| 3 / `ed2ba870` / pressure | Substantially incomplete for the request | The selected controller is a prohibited development board. Its separate TPS62162 buck has no inductor or input/output capacitors in the BOM. |
| 4 / `45b01108` / pressure | Targeted support repair and source check needed | Controller and MIC23050 power stage are coherent. No sensor-bus pullups or established alternative pullup arrangement are present. Add suitable pullups and verify exact MPL3115 sensor support against its missing manufacturer source; two resistors alone are not a certified complete repair. |
| 5 / `f2b272ea` / button | Targeted power-support repair and source check needed | The regulator has no 5 V input bypass capacitor. Its NCP114 source was unavailable. Add the required input capacitor and verify output-capacitor suitability. A 300 mA regulator is not automatically too small for ordinary lower-power BLE, but does not cover every radio mode. |
| 6 / `ad041b0` / button | Usable candidate, no part changes | AP2112, ESP32-C3, switch, 330 Ω LED resistor, regulator/module capacitors and USB-C support make a sensible duty-cycled BLE button. LED-as-active-IC and invented logic thresholds are report defects. A 100 mA average at 50°C gives about 87°C junction; continuous maximum-power transmission is not covered. |
| 7 / `0466473` / light | Targeted component-value repair needed | Change the upper feedback resistor from 100 kΩ to 110 kΩ ±1%, retaining 24.3 kΩ below. Existing divider gives 2.960–3.181 V, crossing the controller's 3.0 V minimum. The suggested change gives approximately 3.197–3.438 V. Sensor active-current naming is a report issue. |
| 8 / `029c8ec7` / light | Targeted part/support repairs and source check needed | Change upper feedback resistor from 330 kΩ ±5% to 365 kΩ ±1%, retaining 80.6 kΩ below; existing lower corner is about 2.852 V. No I2C pullup provision is established, and the LTR-329 source remains unavailable. |
| 9 / `78b6a2b` / logger | Targeted component-value repair needed | Change LED resistor from 33 Ω to 330 Ω, reducing estimated indicator current from 36 mA to 3.6 mA. Existing 4.7 kΩ ALERT resistor can instead serve SCL when ALERT is unused. Wrong SWD wording is a report error; off-board UART/JTAG is available. |
| 10 / `7969892e` / logger | Missing requested functional block | No Bluetooth controller was selected. Numeric-unit and source-record issues do not explain away that omission. The blue LED plus 330 Ω can be a reasonable dim indicator despite inaccurate current prose. |

Thus **three are useful candidates without component changes, five need targeted physical
part/support repairs, and two are substantially incomplete/noncompliant**. This is an
assessment of these ten outputs, not a success-rate estimate. Practical acceptance of 1
and 6 adds explicit ordinary-use caveats rather than endorsing their saved thermal reports.
The five repair candidates were not manually fixed or counted as successful generated BOMs.

Sourcing is separate. Both light BOMs' regulators had zero stock in their saved snapshots.
The second logger also had unavailable regulator, sensor and capacitor lines. A usable
electrical selection is not necessarily immediately purchasable.

### Bounded implementation changes

- Accept Greek `μA` as equivalent to `µA` and `uA` in numeric binding and checks.
- Accept a source's `quiescent_current` terminology for a non-converter device's operating
  current, retaining its source conditions. OPT3001 and TMP117 use this term for active
  measurement/conversion. A converter's own current still cannot replace downstream input
  demand, including when its regulator record is missing.
- Resolve a single mistyped numeric reference, or an Evidence ID, to an existing voltage
  limit only when selected owner, parameter, min/max bound and units identify exactly one
  source number. Preserve ambiguity, absent data, duplicated IDs and known wrong-role/owner
  reference failures. Store the canonical source number; do not infer facts from model literals.
  This fixes attempt 2's threshold references in a read-only replay but does not manufacture
  its missing opposite-direction assessment or relabel the result.
- Decode the observed double-encoded TI distributor locator and fetch its manufacturer
  `/lit/` destination over HTTPS. Existing public-address, credential and redirect checks remain.

No prompts, outcome labels, model, budget, API or orchestration changed. The run version is
38 to identify the changed runtime. All 102 short deterministic tests pass. These changes
do not implement a general divider solver, synthesize missing support, guess missing source
facts, or convert unresolved material questions into passes.

### Fresh results

All three declared requests were run once on frozen version 38. The model, prompts and normal
limits remained unchanged. All finished execution, selected every proposed placement and
provided purchase links for every exported row. Every result received a separate read-only
original-source practical review. No failed attempt was replaced or manually repaired.

| Request / run ID | Pipeline compatibility / sourcing | Practical assessment | Input / output tokens | Calls / corrections | Seconds |
|---|---|---|---:|---:|---:|
| Sensor / `77dde35dbf1f422e95ec12d3074b9c42` | incomplete / available | Targeted power-stage repair needed | 220,272 / 25,315 | 15 / 2 | 109.42 |
| Button / `59cb28b3588e484ba1684ddc58c65b40` | incomplete / available | Targeted power-stage and resistor repair needed | 168,623 / 21,832 | 13 / 2 | 88.64 |
| Light / `296fb5ca92ec4c7cb233f922e4f8d13c` | issues_found / partial | Two feedback resistors missing; regulator unavailable | 340,238 / 32,579 | 20 / 2 | 148.58 |

Totals: **729,133 input tokens, 79,726 output tokens, 48 model calls and 346.64 seconds**
of run duration. Each run used its two ordinary correction rounds. There were no model-call
errors, provider-quota failures or run-budget stops. Local quota scheduling waits occurred.

**Sensor:** The 12 placements include the ESP32-WROOM-32E-N4, SHT40, USB-C connector and
ordinary module/sensor/USB support. There is no regulator. The model incorrectly treats the
ESP32 module as containing 5 V-to-3.3 V conversion, supplies it from USB, and recasts its
external-supply recommendation as output capacity. The original module datasheet page 28
specifies 3.0–3.6 V operation and a 3.6 V absolute maximum. Add a suitable 3.3 V regulator
with its required capacitors; an intermittent-workload caveat cannot replace voltage conversion.
Both corrections repeated the false integrated-regulator premise. Other selected functions
and supporting parts are reasonable. This is a localized actual omission, not proof that
the entire selection is useless, but it is not ready unchanged.

**Button:** ESP32-C3-MINI-1-N4 likewise requires a 3.0–3.6 V supply (manufacturer page 21).
No 5 V-to-3.3 V regulator is purchased, despite the model's invented internal-LDO record.
Additionally, the 330 Ω search selected `RC0603FR-0733RL`, whose catalog value is **33 Ω**.
With the selected LED's approximately 2 V forward voltage this implies roughly 39 mA,
not the report's 20 mA budget. A conventional 330 Ω indicator resistor gives about 4 mA.
Add the regulator and required support, and correct that resistor. Switch, module decoupling,
enable RC and USB-C terminations are otherwise plausible. This is not a reason to require a
schematic or an exhaustive GPIO assignment plan.

**Light:** The actual AP63200WU-7 is adjustable, but the BOM has no feedback-divider resistors.
The manufacturer document and the run's own refreshed source requirement identify the missing
network. The source table's 196 kΩ/62 kΩ pair, with ±1% resistors, would establish approximately
3.329 V nominal and 3.246–3.414 V including feedback/reference and resistor corners. Those
parts were not added during this audit. The existing controller, VEML7700, regulator, inductor,
bootstrap/bulk/bypass capacitors, enable RC, I2C pullups and USB-C terminations are otherwise
reasonable. The saved regulator has zero stock. The binder's 0.792–0.808 V finding comes from
the feedback reference, not a measured output rail. An optional sensor supply filter and
stale support references also create report-level blockers, but clearing those would not
purchase the missing divider. No exact output is established until that network is provided.

Original cached manufacturer sources used for the decisive practical comparisons include:

- ESP32-WROOM-32E/32UE, pages 28, 29 and 39:
  `doc_4c7a345d1c1bfec34c38665639e39a7f43b79a35a12f6adcc2c7c0f83850f8b8.pdf`.
- ESP32-C3-MINI-1/1U, operating limits page 21 and ordinary support guidance:
  `doc_de7361381348d82a1abd337f10170be7a420675987568f71fe3c5b100deed270.pdf`.
- AP63200/AP63201/AP63203/AP63205, exact variant and feedback setting:
  `doc_ef99daa3789d835bc025dfcb4c605c5c2e6d3e7223e86d40b33e6b497ea5a722.pdf`.

## Verification and disposition

All 102 deterministic backend tests pass, and `git diff --check` is clean. Runtime SHA-256
fingerprints match before and after every fresh attempt. Terminal SSE, saved JSON, HTTP
retrieval, JSON export and every CSV BOM field agree for all three. The observation-only
artifacts are in ignored `backend/data/evaluations/practical-acceptance-20260930-v38/`.
The isolated port-3002 test backend was stopped; existing user services and unrelated frontend
changes were left untouched. Existing processes need a restart to load the edited Python code.

This pass changes the assessment from "no accepted strict reports" to a more informative
picture of actual BOM quality. Some incomplete historical results are useful without part
changes. Others, including all three fresh results, need a limited but real component/support
repair. None of the fresh three is accepted unchanged under the practical standard; this is
not a demand for perfect prose or a complete schematic. The fresh sample does not establish
improvement or regression versus the earlier stochastic runs.

The bounded pass is complete. No further runtime fixes, prompt additions, model changes,
gate relabeling or additional live attempts followed the fresh sample. The specific omissions
are recorded above rather than turned into another automatic repair cycle or product pivot.
