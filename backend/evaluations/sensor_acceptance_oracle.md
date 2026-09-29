# Small source-grounded acceptance oracle

Prepared independently on 2026-09-13 from manufacturer text and visual inspection of the cited circuit/table pages. This is a manual evaluation reference, not application rules, a live unit test, or an assertion that the current generated board is correct. Do not give the expected findings to the model being evaluated.

Historical pre-BOM-only evaluation material: source facts remain useful, but its wiring-level
cases and original evaluation gates are not current completion requirements. See the
[implemented scope](../../docs/architecture/practical-bom-workflow.md#6-implementation-and-evaluation)
and [dated run results](results.md) for current verification status.

All page numbers below are **one-based physical pages of the original PDF**, not positions in a supplied slice. Pin numbers and reference labels belong to the named source, not automatically to Jigsaw's component IDs. Record the fetched revision/hash when running these cases; reassess changed source revisions rather than silently reusing this oracle.

## Sources and key observations

### C6: Espressif ESP32-C6-MINI-1 / MINI-1U v1.5

[Manufacturer datasheet](https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf), 53 pages.

| Physical pages | Expected observations |
|---|---|
| 2-4 | Wi-Fi and Bluetooth LE; the N4 variant has 4 MB flash and a PCB antenna. MINI-1U instead needs an external antenna. |
| 10-11, 26 | Supply pin 3; EN pin 8. Recommended supply 3.0-3.6 V; recommended external supply capacity at least 0.5 A. Capacity is not consumption. |
| 26-27 | Input VIH >=0.75*VDD, VIL <=0.25*VDD. Output VOH/VOL conditions include high-impedance measurement. Wi-Fi peaks include 382 mA at 802.11b/20.5 dBm, measured at 3.3 V/25 C; not a universal guaranteed maximum. |
| 13, 40 | Download mode: GPIO8 high, GPIO9 low. UART download is supported; UART source pins are TXD0=31, RXD0=30. |
| 40, Figure 9-1 | External supply circuit: 22 uF bulk plus 0.1 uF bypass. EN network is R1/C3 (TBD); accompanying prose commonly recommends 10 kohm/1 uF. R8=10 kohm belongs to GPIO8. C4=0.1 uF is across reset switch SW1 and connects to EN through R2=0 ohm: it is electrically EN-to-ground in that reset branch, not the separately labeled C3 or a stated replacement for its recommended value. Optional unpopulated crystal components are not mandatory additions. |

Do not infer Bluetooth Classic support from an unqualified Bluetooth label. Espressif explicitly identifies original ESP32 support for BR/EDR separately in [ESP32-WROOM-32E v2.1, physical page 2](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf).

### C3: focused schematic-reading comparison, v2.2

[ESP32-C3-MINI-1 / MINI-1U manufacturer datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf), 48 pages. The following observations were visually checked on physical page 34, Figure 9-1 and its accompanying prose. Use the original page as a frozen source-reading fixture, without supplying these expected answers to the evaluated model. This is not a passing full-device fixture.

| Source feature | Expected observation |
|---|---|
| Supply bypass | C1=10 uF and C2=0.1 uF connect VDD33 / module 3V3 pin 3 to GND. Do not import the C6's 22 uF label. |
| EN delay | R1 (TBD) connects VDD33 to EN pin 8; C3 (TBD) connects EN to GND. Prose recommends usually 10 kohm and 1 uF, subject to power-up timing. R9 is not the EN pull-up. |
| Reset branch | C4=0.1 uF is across SW1 and reaches EN through R2=0 ohm. It is electrically EN-to-ground, but the drawing does not identify it as a replacement for C3 / the prose's recommended delay capacitor. |
| R8 | 10 kohm from VDD33 to GPIO8, module pin 22; **not GPIO9**. |
| R9 | 10 kohm from VDD33 to GPIO2, module pin 5; **not EN**. |
| Boot connector | GPIO9, module pin 23, connects to JP2 pin 1; JP2 pin 2 is GND. Do not move R8 onto this net. |
| Other depicted pins | TXD0=31, RXD0=30; GPIO19 / USB D+=27, GPIO18 / USB D-=26; JTAG GPIO4-7 use module pins 18-21 respectively. The optional NC crystal network does not mandate external crystal parts. |

A comparison fails semantic accuracy if it assigns a support part to the wrong net, even with a correct page/figure citation or a correct EN recommendation elsewhere in the response. Evaluate capacitor connectivity separately from its intended role; do not penalize the true statement that C4 reaches EN through the zero-ohm resistor.

### SHT: Sensirion SHT4x v7.3, June 2026

[Manufacturer datasheet](https://sensirion.com/media/documents/33FD6951/6A7C10A0/HT_DS_Datasheet_SHT4x_V7.3.pdf), 25 pages.

| Physical pages | Expected observations |
|---|---|
| 3, Figure 1; 11 | Sensor bypass: 100 nF VDD-to-ground. Two bus pull-ups; example values 10 kohm, not universally mandatory values. |
| 9, Table 4 | Supply 1.08-3.6 V. Heater-off measurement current: 320 uA typical, 500 uA maximum. The strongest heater mode instead reaches 100 mA maximum. |
| 9, Table 4 | VIH >=0.7*VDD; VIL <=0.3*VDD. At VDD>2 V and pull-up>390 ohm, VOL <=0.4 V. Fast-mode bus capacitance must satisfy Cb <300 ns/(0.8473*Rp); 4.7 kohm implies approximately 75 pF. |
| 17 | SDA=1, SCL=2, VDD=3, VSS=4. |
| 21-22, Tables 11-12 | SHT40-AD1B-R2 address 0x44; SHT40-BD1B-R2 address 0x45. These are different orderable variants, not a software-selectable address change. |

### LDO: Diodes AP2112, DS39724 rev. 2-2, June 2017

[Manufacturer datasheet](https://www.diodes.com/assets/Datasheets/AP2112.pdf), 18 pages; use the AP2112K-3.3TRG1 / SOT25 variant.

| Physical pages | Expected observations |
|---|---|
| 2, application circuit and pin table | Input/output ceramic capacitors: 1 uF each; X5R/X7R recommended. SOT25 VIN=1, GND=2, EN=3, VOUT=5. Define the EN connection; floating is not a valid always-on plan. |
| 3 | Recommended VIN 2.5-6.0 V, not the 6.5 V absolute maximum. SOT25 theta-JA figure is 184 C/W without heatsink; physical implementation still matters. |
| 8, AP2112-3.3 table | 3.3 V nominal; initial 98.5%-101.5% output limits apply at 1-30 mA. 600 mA capability and load/line regulation have stated conditions. Do not claim initial tolerance alone covers every load/temperature. |
| 8 | Dropout maximum 200 mV at 300 mA and 400 mV at 600 mA. EN high threshold 1.5 V; internal EN pull-down approximately 3 Mohm. No-load IQ maximum 80 uA is not a guaranteed loaded ground-current bound. |

An estimated LDO heat budget must specify ambient/thermal assumptions and be compared with actual proposed dissipation; a USB-source assumption is not a thermal justification. An alternative regulator is an acceptable correction.

### USB connector and power-only operation

[GCT USB4105 drawing rev. B4, physical page 1](https://gct.co/files/drawings/usb4105.pdf) identifies USB4105-GF-A ordering, CC1=A5, CC2=B5, VBUS=A4/A9/B4/B9 and GND=A1/A12/B1/B12. Collective VBUS rating is 5 A. The [product specification, physical page 2](https://gct.co/files/specs/usb4105-spec.pdf) supplies ratings but does not replace the pin drawing.

[USB-IF release 2.5 archive](https://usb.org/sites/default/files/USB%20Type-C%202.5%20Release%20202603.zip), file `USB Type-C Spec R2.5 - March 2026.pdf`, physical pages 201 and 226: a power-only PSD may consume up to 500 mA with USB2 inrush requirements; current-state monitoring is needed when consuming above default current. PSD excludes USB/Alternate Mode communications. The same clauses are available in the directly fetchable [released R2.4 PDF](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/USB-Type_2D00_C-Spec-R2.4-_2D00_-October-2024.pdf), at the same pages. A [TI engineer's implementation discussion](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/799330/tusb320-usb-type-c-minimum-system-for-power-sink-only-and-no-data) supports the resistor-only default-current case.

For this simple case, independent 5.1 kohm CC pull-downs and an explicit power-only C-to-C source assumption can avoid a controller. Still account for attachment/inrush and downstream capacitor charging; connector current rating does not establish available source current. A later USB programming/data feature must reconsider the power-only assumption. Do not require USB PD reflexively.

## Positive case P0: the public sensor request

Request: "Make me a temperature and humidity sensor with WiFi and Bluetooth powered by USB-C for consumer use."

Current candidate identities: ESP32-C6-MINI-1-N4, SHT40-AD1B-R2, USB4105-GF-A and AP2112K-3.3TRG1. These are candidates, **not a frozen passing BOM**. Another source-backed selection is acceptable. BLE is a disclosed reasonable default unless Classic is explicitly requested.

Before scoring this case as successfully completed, inspect:

- Exact functions/variants and purchase identities; all necessary support placements and quantities selected.
- Regulated supply domains, realistic stated-mode load budget, regulator EN, dropout and justified thermal allowance. Manufacturer limits and declared estimates stay distinct.
- Correct module bulk/bypass, sensor bypass, regulator input/output support and shared bus pull-ups, each with its actual endpoints and source.
- Chosen available GPIOs, I2C address and electrical/rate assumptions; no assignment hidden behind "both support I2C."
- A workable boot/reset/programming route. External UART tools and named test pads are acceptable; an additional USB bridge is not obligatory.
- A justified USB attachment/source configuration and startup plan. Antenna clearance, capacitor placement and keeping the sensor away from heat remain ordinary layout guidance.
- Original physical page accuracy, parameter-relevant citations and a completed whole-design review. A correct number cited to the wrong table/page is not a valid evidence result.

Accept a positive outcome only after concrete conflicts and necessary gaps are resolved. A truthful `incomplete` result is preferable to a false pass, but does **not** count as completion of the positive milestone. Do not label any saved live run a gold baseline without this inspection.

## Four material adversarial mutations

Apply each independently to a separately inspected clean baseline. Preserve unrelated functions, evidence and valid connections. For reviewer-only evaluation, give original source pages and the mutated design but no expected answer. A defect is detected only when the relevant problem or a source-backed repair is returned; unrelated `unknown` does not count.

| Case | Mutation | Required finding or repair |
|---|---|---|
| M1: wrong supply | Bypass/remove regulation and connect the module and sensor supplies directly to a stated 5 V USB rail. Update connections consistently; retain their documented receiver ranges. | Power `fail`: source exceeds receiving operating ranges. Restore suitable regulation; do not widen device limits, remove functions or cite absolute maxima. Sources: C6 p26; SHT p9. |
| M2: omitted decoupling | Remove the sensor's local bypass capacitor **and its generated support-need entry**, with no equivalent placement left. Remove dangling references so this is not merely an integrity test. | Support `fail`: independently discover missing local bypass from the circuit/communication guidance. Restore a sourced placement and connection. A generic layout reminder or checking only the supplied support list is insufficient. Sources: SHT p3/p11. |
| M3: Classic versus LE | Explicitly require Bluetooth Classic BR/EDR in both original request and requirement record, while keeping C6 as the only radio candidate. | Requirement `fail`: selected radio does not meet Classic. Select a documented Classic-capable alternative and re-review affected power/pins/support; do not reinterpret Classic as BLE. Sources: C6 p2; original ESP32 p2. |
| M4: same address | Require two independently readable sensors; put two SHT40-AD1B-R2 placements on one I2C bus at 0x44. Give each its own bypass and load entry so only the addressing conflict is introduced. | Signals `fail`: shared-address devices cannot provide independent addressed readings as configured. A documented alternate-address variant, separate bus or properly supported mux is acceptable. Do not delete the second sensor or relabel an unchanged AD1B device to another address. Source: SHT p21/p22. |

Calibration, not a fifth electrical mutation: withhold the needed application-circuit page and any substitute evidence. `unknown`/`incomplete` with a specific page/source request is correct; inventing support values or passing anyway is not. This does not satisfy the positive completion case.

## Held-out case H1: SPI pressure logger

Freeze the implementation/prompts before running: "Make a USB-C-powered WiFi barometric-pressure logger for indoor use. Use a BMP280 over four-wire SPI. No humidity sensor or display."

This introduces a different manufacturer, sensing function, two supply domains and explicit SPI rather than another SHT variant. Existing controller/power choices may be reused only after checking their applicability. Do not tune the prompt against the expected facts before the first held-out run.

[Bosch BMP280 datasheet rev. 1.26, October 2021](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf), 49 pages:

| Physical pages | Expected observations |
|---|---|
| 7, Table 2 | VDD 1.71-3.6 V; VDDIO 1.2-3.6 V. Both need explicit supply connections. Pressure-measurement peak current reaches 1120 uA; low-rate average current is not the peak budget. |
| 29-31, 34 | Four-wire SPI, explicit CSB and clock/data assignments, supported mode/rate and electrical conditions. SPI clock maximum 10 MHz; a modest slower chosen rate is acceptable. No I2C address is required for this configuration. |
| 34, Table 29 | GND=1/7; CSB=2; SDI=3; SCK=4; SDO=5; VDDIO=6; VDD=8. |
| 35, Figure 15 | Separate supply decoupling positions C1/C2, recommended 100 nF each, with shared ground. Do not import SHT I2C pull-ups as SPI requirements. |

A useful result must preserve the pressure/SPI request and source its actual support. Missing required facts produce a specific unresolved result, not a fabricated pass. Report its first-run outcome whether successful or not.

## Execution record and readiness

Run the same frozen P0/M1-M4 reviewer fixtures three times each; do not retune between trials and count only the target detection/repair. Record run ID, model/prompt revision, target finding, false alarms, unresolved necessary gaps, valid original-page references, elapsed time and usage. Record H1 separately. A markdown row per trial is sufficient; no service or test harness is required.

Status at creation: **not executed as a frozen acceptance suite**. Existing live run `4d570535dd0e4aa4b0a88033d1fec013` is diagnostic only: it ended incomplete at 21 model calls, 295,964 input tokens, 29,706 output tokens and 132.73 seconds. Inspection found slice-index citations, wrong C6 reset-circuit interpretation, omitted module bulk decoupling, an unspecified regulator enable, missing programming access and unsupported/reused numeric evidence. It is not the positive baseline.

Do not claim release readiness unless the positive case completes, each material mutation is specifically detected/repaired across three frozen trials, and the held-out outcome is reported. These cases are a small development acceptance bar, not a statistical safety guarantee or exhaustive electronics certification.
