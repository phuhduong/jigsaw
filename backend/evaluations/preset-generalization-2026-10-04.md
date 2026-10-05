# Preset generalization evaluation — 2026-10-04

**Completed outcome:** eight fresh runs, three plausible component sets with no independently identified compatibility error, two correctly reported failures, and three false acceptances. The exact battery preset failed both attempts; the display preset produced one incompatible and one plausible but partially sourced result. The familiar wireless control also falsely passed. The frontend therefore retains only the existing wireless example, without labeling it validated; the battery and display presets remain removed. Free-text requests remain available. This sample establishes neither broad reliability nor a production success rate.

Raw snapshots, caches, and evaluation artifacts stay in ignored `backend/data/` directories. The localhost links below require those local records; this document preserves the audit summary in source control.

## Declaration before execution

Declared at `2026-10-05T02:31:18.708186+00:00` against current prompt `41`, commit `f5c46bd1fc3afb2b2acc697763a1a5dffe6fddb4`, with the existing uncommitted runtime files frozen by SHA-256 in `../data/evaluations/preset-generalization-20261004-v41/manifest.json`. This declaration predates every model call in this batch. No production runtime or prompt changes are part of this evaluation.

The fixed sequence is one wireless control, two exact battery preset attempts, two exact light/display preset attempts, then three previously unused requests. Each attempt is a fresh request with no component hints, page hints, manual repairs, clarification answers, replacement trials, or result-dependent changes. Normal workflow correction remains enabled under unchanged limits. Original source-cache reuse is permitted; saved design reuse is not. Purchasing options are one board, US, USD.

The isolated API runs at `127.0.0.1:3002` with its own saved-run directory and the normal `backend/data/documents` cache. Historical `backend/data/runs` records are untouched by evaluation startup. All SSE events, GET snapshots, JSON/CSV exports, run records, transport outcomes, and consistency checks are preserved in `backend/data/evaluations/preset-generalization-20261004-v41/`.

Model configuration:
- `MODEL`: `gemini-3.5-flash-lite`
- `MODEL_PROVIDER`: `google_genai`
- `MODEL_THINKING_LEVEL`: `provider_default`
- `MODEL_PDF_INPUT`: `true`
- `MODEL_RPM`: `15`
- `MODEL_TPM`: `250000`
- `MODEL_CONTEXT_TOKENS`: `1048576`
- `MCP_SERVER_URL`: `http://localhost:8080`
- `LANGCHAIN_TRACING_V2`: `false`

Per-run resource limits:

```json
{
  "seconds": 480,
  "model_calls": 30,
  "input_tokens": 400000,
  "output_tokens": 64000,
  "supplier_calls": 60,
  "documents": 20,
  "pdf_pages": 120,
  "functional_blocks": 8,
  "bom_rows": 40,
  "correction_rounds": 2
}
```

## Fixed requests

### W1 — Wireless sensor

> A temperature and humidity sensor with Wi-Fi and Bluetooth, powered by USB-C (5V) for indoor use.

### B1 — Battery data logger

> A battery-powered temperature data logger that takes a reading every minute and stores it locally for later retrieval.

### B2 — Battery data logger

> A battery-powered temperature data logger that takes a reading every minute and stores it locally for later retrieval.

### L1 — Light monitor

> A USB-powered ambient light monitor with a small display showing the current light level.

### L2 — Light monitor

> A USB-powered ambient light monitor with a small display showing the current light level.

### H1 — Tilt alarm

> A USB-C (5V)-powered tilt alarm that sounds a buzzer when a stationary object tilts more than 20 degrees. No wireless connection.

### H2 — Motor controller

> A 12V DC-powered controller for a small brushed DC motor rated for 12V, 300mA running current and 1A stall current, with a pushbutton to start and stop it. Use board-mountable parts.

### H3 — Two identical I2C sensors

> A USB-C (5V)-powered indoor monitor that reads two identical I2C temperature sensors at separate locations and reports both readings over Bluetooth LE. Use board-mountable parts.

## Assessment policy

Completion and the backend badge are recorded separately from independent engineering assessment. Assess requested functionality, common supply configuration, current capability, logic levels, interface/resource feasibility, selected-part suitability, necessary functional blocks, and material operating assumptions using manufacturer sources. Missing ordinary support-passive SKUs, evidence gaps, and reporting defects alone do not fail functional compatibility under current AGENTS.md. An independently identified material error in a backend-passing run is a false acceptance.

All attempts count, including quota, timeout, source/supplier failures, no verdicts, and needs-input outcomes. If the provider reports account quota exhaustion, stop further attempts rather than issue predictably doomed calls; pending attempts remain explicitly pending until there is evidence quota has recovered. No automatic paid fallback or configuration change. This small batch characterizes the selected requests; it does not estimate general production reliability.

## Execution results

All eight attempts completed in the declared order. The backend returned six passing compatibility verdicts and two failed verdicts; these are backend outcomes, not independent acceptance. No run stopped on quota or resource limits. A transient provider failure during H1 used the existing single retry allowance. No additional requests, manual corrections, or replacement attempts were submitted.

| Attempt | Run ID | Backend verdict | Sourcing | Seconds | Model calls | Input tokens | Output tokens | Corrections |
|---|---|---|---|---:|---:|---:|---:|---:|
| W1 | `1d13ffe6a1e74eccabe331001ff74bb4` | Checks passed | available | 111.25 | 17 | 160,661 | 21,316 | 1 |
| B1 | `a9cce01cea4145b38779c9ddec844148` | Checks passed | partial | 59.7 | 12 | 109,828 | 15,081 | 1 |
| B2 | `eecc3c74b6774049ab63c00db8a8df3e` | Checks failed | available | 83.63 | 19 | 186,900 | 20,953 | 2 |
| L1 | `4ac0202b80f3418eb6220e2a45859513` | Checks passed | partial | 50.96 | 14 | 86,758 | 8,343 | 1 |
| L2 | `d0fda3e95a11469eaf8ae75f7b50652c` | Checks passed | partial | 62.36 | 12 | 69,739 | 7,981 | 1 |
| H1 | `33265966bfd940c6ac63a76bd1cdb0c7` | Checks failed | partial | 191.82 | 22 | 197,661 | 20,016 | 2 |
| H2 | `e5ced2c6aa754affbc2558e9bf1db8c2` | Checks passed | available | 42.8 | 9 | 62,210 | 7,112 | 0 |
| H3 | `8d024b7dda4f4a8890f56f076c115fd3` | Checks passed | available | 59.35 | 10 | 82,841 | 13,436 | 0 |

Total measured usage: **115 model calls, 956,598 input tokens, 114,238 output tokens, and 661.87 seconds** of summed backend execution. Supplier calls: 106; document operations: 49; PDF page inputs: 115; correction rounds: 8. Input/output reservations for failed model attempts may be included in these recorded counters.

For every attempt, SSE sequence and run IDs were consistent; the terminal stream snapshot, GET snapshot, saved record, and full JSON export agreed exactly (the GET/export projection adds `bom` to the raw saved record). Every CSV cell matched the saved BOM projection, including grouped references, quantities, prices, and URLs. Every frozen runtime hash remained unchanged before/after each run and at final verification. Results and checks are in each attempt’s `result.json`; aggregate execution metrics are in `execution-summary.json`.

Independent engineering audits are separate from these transport and runtime checks. Their final findings are added below by the reviewers.

The eight final raw records were then copied byte-for-byte into the primary `backend/data/runs/` store using exclusive creation; no historical path was overwritten. All eight GET responses from port 3001 exactly matched the evaluation snapshots. They can be reopened at `http://localhost:5173/design?run=<run-id>`. Copy hashes and GET checks are recorded in `main-store-copies.json`. The isolated port-3002 process was stopped after verification; the main frontend, primary backend, and MCP service remain available.

## Independent engineering assessment

Reviewers examined the actual final selections and configurations using original manufacturer documents, including visual inspection of relevant PDF tables. No saved output was repaired or regraded. Source gaps, missing ordinary passive procurement, and incomplete numerical reporting alone did not fail a case. Sourcing remains a separate column in the execution table. The assessments below are independent conclusions, not checks performed by the production backend.

| Attempt and saved UI | Independent result | Evidence that determines the assessment |
|---|---|---|
| [W1 wireless](http://localhost:5173/design?run=1d13ffe6a1e74eccabe331001ff74bb4) | **False acceptance** | Replacement TPS62125 supports only 200 mA at the chosen USB input, below the recorded ESP32 requirement. |
| [B1 battery](http://localhost:5173/design?run=a9cce01cea4145b38779c9ddec844148) | **False acceptance** | Direct battery supply falls below the MCU's minimum; selected 12 mm holder does not fit the selected 20 mm cell. |
| [B2 battery](http://localhost:5173/design?run=eecc3c74b6774049ab63c00db8a8df3e) | Correctly rejected; unsuitable result | The final review identifies the same direct-battery voltage-range problem, but the bounded correction does not resolve it. |
| [L1 display](http://localhost:5173/design?run=4ac0202b80f3418eb6220e2a45859513) | **False acceptance** | A replacement bare 3.3 V MCU module retains the former board's 5 V supply arrangement without a regulator; sensor address is stale too. |
| [L2 display](http://localhost:5173/design?run=d0fda3e95a11469eaf8ae75f7b50652c) | No identified incompatibility; limited confidence | Actual controller and sensor assemblies integrate the assumed conversion/translation. Sourcing is partial and the generated evidence is weak. |
| [H1 tilt alarm](http://localhost:5173/design?run=33265966bfd940c6ac63a76bd1cdb0c7) | Correctly rejected; unsuitable result | Buzzer remains unselected. Independent review also finds a SPI-only sensor incorrectly configured as I2C. |
| [H2 motor](http://localhost:5173/design?run=e5ced2c6aa754affbc2558e9bf1db8c2) | No identified incompatibility; operating guidance incomplete | Nano assembly accepts 12 V; actual motor driver supports the motor domain and controller logic. Sustained-stall thermal behavior and external supply capability are not established. |
| [H3 dual sensor](http://localhost:5173/design?run=8d024b7dda4f4a8890f56f076c115fd3) | No identified incompatibility | Fixed 3.3 V converter, BLE controller, and two sensors form a feasible arrangement; the exact sensor variant supports the two saved addresses. |

### Material findings and source basis

**W1:** The [TPS62125 datasheet](https://www.ti.com/lit/ds/symlink/tps62125.pdf), physical p. 4, limits output to 200 mA below 6 V input; the 300 mA rating requires at least 6 V. The saved USB input is 4.75-5.25 V. The [ESP32-WROOM datasheet](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf), pp. 28-29, distinguishes a recommended 500 mA supply capability from measured Wi-Fi peaks of 211-379 mA. The saved configuration provides no restricted workload or substantiated transient arrangement that makes the selected converter adequate, and records a 500 mA controller budget itself. The reviewer nevertheless approves the converter. The current-check operands are unbound, which leaves code unable to resolve the comparison; the independent failure comes from original device limits, not the presence of unknowns.

**B1/B2:** The [ESP32-C3-MINI datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf), p. 21, requires at least 3.0 V. B1 records operation down to 2.5 V and B2 down to 2.0 V with direct coin-cell supply. B2's MCP9808 also needs at least 2.7 V. B1 additionally selects Keystone 3000, a 12 mm cell holder, alongside a CR2032 20 mm cell. The [Keystone K75 catalog](https://www.keyelco.com/userAssets/file/K75p11.pdf) identifies the 12 mm 3000 and 20 mm 3002 separately; the reviewer mentions an alternative holder that was never selected. These are actual selected-part/configuration errors. Battery pulse buffering is separately unestablished, not assumed impossible and not counted as another proven failure. Local timing/storage/retrieval functions are plausible in the selected MCUs, but that does not repair power or holder selection.

**L1:** The same C3 source limits the bare module to 3.0-3.6 V. It replaces a Pico assembly but remains on a 4.75-5.25 V rail with no selected regulator. Notes still refer to the old Pico. The selected Adafruit MAX44009 breakout also retains address 0x23 from a different sensor; [its actual module guide](https://learn.adafruit.com/adafruit-max44009-lux-light-sensor/pinouts) specifies 0x4A/0x4B. A small address correction could fix communication, but was not made to the saved configuration.

**L2:** [Seeed's XIAO RP2040 documentation](https://wiki.seeedstudio.com/XIAO-RP2040/) and original schematic establish onboard 5 V-to-3.3 V conversion. The [complete ST VD6283TX-SATEL board](https://www.st.com/resource/en/data_brief/vd6283tx-satel.pdf) includes regulation and level shifting; it is not the bare low-voltage sensor. The [WPI438 manual](https://cdn.velleman.eu/downloads/25/wpi438a4v01.pdf), p. 3, supports the intended 3.3 V display operation. The sensor's 7-bit address 0x20 does not conflict with the display's 0x3C. No definite conflict was found, but the run read zero PDF pages and did not establish its spare-current or thermal claims. The selected XIAO had no stock, and the display had no offer. This is a plausible functional selection with limited evidence and partial sourcing, not a validated preset.

**H1:** The absent buzzer is enough to leave the requested alarm incomplete. In addition, the selected part is LIS3DHHTR (LIS3DHH), not LIS3DHTR (LIS3DH). [ST's LIS3DHH datasheet](https://www.st.com/content/ccc/resource/technical/document/datasheet/group3/08/30/e3/69/0e/cc/42/1f/DM00358264/files/DM00358264.pdf/jcr%3Acontent/translations/en.DM00358264.pdf) identifies a SPI interface; the saved I2C configuration at 0x53 is incompatible with that exact part. The overall failed verdict is correct, although its passing signals review misses this additional error.

**H2:** The [Nano ESP32 datasheet](https://docs.arduino.cc/resources/datasheets/ABX00083-datasheet.pdf), pp. 13-15, confirms integrated conversion from 6-21 V VIN and 3.3 V logic; Arduino's [exact ABX00092 page](https://store.arduino.cc/products/nano-esp32) establishes the selected variant. [Allegro A3909](https://www.allegromicro.com/~/media/Files/Datasheets/A3909-Datasheet.ashx), pp. 1-5, supports 4-18 V operation, operation up to 1 A per phase, compatible logic thresholds, and start/stop control. Ordinary 300 mA running is plausible. Its 1 A limit is not an unconditional continuous-stall guarantee: package cooling and protection behavior remain material implementation considerations absent from the generic notes. The report also misuses inlet-contact rating as adapter capacity. No definite incompatible part or missing function was found; those incomplete assurances are not endorsed.

**H3:** The [TMP1075 datasheet](https://www.ti.com/lit/ds/symlink/tmp1075.pdf), p. 14, Table 7-3 for the actual N variant, supports the saved 0x48/0x49 addresses using A0 low/high. The [MIC23050 datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/mic23050.pdf) ordering information identifies SYML as fixed 3.3 V; its input/current capability fits the selected controller and sensors. Two physical sensor instances and an order quantity of two are preserved. Wrong-variant sensor-current prose, unbound quantities, and incomplete support notes remain diagnostics; they do not establish a functional error in this arrangement.

Detailed independent notes and cached-source identities are retained in `backend/data/evaluations/preset-generalization-20261004-v41/{control,battery,display,tilt,motor,dual-sensor}-audit.md`. They record the inspected pages, unverified claims, and sourcing limits without altering the final snapshots.

## Disposition and frontend verification

The two extra presets were removed, leaving the wireless example and unrestricted free-text entry. This does not assert that wireless generation is reliably correct: W1 demonstrates otherwise. No evidence/unknown banners or additional diagnostic UI were added. Browser verification confirmed the remaining preset fills its original query, disappears after entry, and returns when cleared. A fresh reload shows the single example. A newly evaluated motor result reopened successfully through the main saved-run UI. All 26 frontend tests, typecheck, production build, and `git diff --check` passed; the existing Browserslist data-age warning remains.

The result supports targeted future investigation of power-stage suitability and stale configuration after component replacement. It does not justify another abstraction layer, a broad part whitelist, model changes, or promoting more presets. This declared evaluation ends here: no backend tuning, hidden retries, manual acceptance repairs, or second evaluation cycle followed. The current batch provides three plausible examples and five unsuitable final configurations, including three false acceptances, under the current functional-component scope. Those observed counts must not be presented as a general success rate.
