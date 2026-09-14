# Sensor BOM: independent source audit

Audited 2026-09-14 UTC. Saved run: [848be681f949489282a1db8ff2219c0d](../data/runs/848be681f949489282a1db8ff2219c0d.json), a **guided refinement** of [7c9effbcc2724951a5c22062aca532d8](../data/runs/7c9effbcc2724951a5c22062aca532d8.json), not an unaided generation.

Follow-up [eba1d0a3e6634fedb1654f255e54b62f](../data/runs/eba1d0a3e6634fedb1654f255e54b62f.json)
retained all 15 selected manufacturer/MPN identities and refreshed their offers at
2026-09-14 03:23 UTC. All remained available; the corrected cut-tape subtotal was
still $11.08. Saved state and both HTTP export formats were verified against that
run. It also remains automatically `incomplete`; the parts-level assessment below
applies unchanged.

**Independent BOM compatibility assessment: PASS under the assumptions below.** Source inspection and explicit calculations found no remaining material incompatible purchased part or missing necessary external support component. This assesses a feasible pre-layout BOM, not a schematic, finished PCB, certification or tested hardware.

**Automated result remains incomplete.** The saved run finished with sourcing available but exhausted its input budget before completing its current review. This audit does not change that JSON status, establish general backend readiness, or claim that the pipeline's evidence ledger is correct.

## Operating assumptions

- Indoor ambient 0-40 C; temperature/humidity sensing with the SHT40 heater disabled; Wi-Fi and Bluetooth LE.
- Known USB-C power-only source providing nominal 5 V, assumed 4.75-5.25 V at the device and a 500 mA default-current contract. The two CC resistors identify a sink; they do not negotiate USB PD or authorize arbitrary charger-nameplate current.
- Estimated regulated supply envelope 3.2-3.4 V. MCU design-load estimate 400 mA, sensor measurement maximum 0.5 mA, and upstream estimate 410 mA including overhead. The MCU estimate exceeds the documented 379 mA radio peak condition; it is not a guaranteed maximum for every firmware workload. The module's recommended 500 mA supply capability is not its consumption.
- Standard-mode 100 kHz I2C with two 10 kohm pull-ups on a compact board. Off-board programming uses a fixture/test-pad arrangement; a permanently fitted programming header or bridge is not required by this BOM.
- Thermal screening uses the actual AP2114D TO-252/DPAK package, its indicative 90 C/W junction-to-ambient figure, a chosen 125 C junction target, and 40 C maximum ambient. Final PCB heat flow, capacitor behavior, transients and signal integrity remain implementation verification, not guarantees made here.

## Purchase list

15 component placements, grouped into 12 unique manufacturer part numbers. Prices and stock are the saved DigiKey **2026-09-14 03:11 UTC** snapshots, not a future availability promise. Each listed cut-tape offer allowed quantity-one orders and had sufficient stock. Links open the product; choose cut tape rather than a full reel or Digi-Reel service.

| IDs | Manufacturer / buy link | Qty | Role and selected specification | USD each | USD line | Snapshot stock |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| U1 | Espressif [ESP32-WROOM-32E-N4](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-WROOM-32E-N4/11613125) | 1 | MCU, Wi-Fi/BLE, integrated flash/crystal/PCB antenna | 4.99 | 4.99 | 8,583 |
| U2 | Sensirion [SHT40-AD1B-R2](https://www.digikey.com/en/products/detail/sensirion-ag/SHT40-AD1B-R2/13532084) | 1 | Digital temperature/humidity sensor, I2C | 1.88 | 1.88 | 27,681 |
| U3 | Diodes [AP2114D-3.3TRG1](https://www.digikey.com/en/products/detail/diodes-incorporated/AP2114D-3-3TRG1/4770626) | 1 | Fixed 3.3 V, 1 A regulator; TO-252/DPAK, not H/SOT-223 | 1.53 | 1.53 | 6,761 |
| J1 | Amphenol [10155435-00011LF](https://www.digikey.com/en/products/detail/amphenol-cs-fci/10155435-00011LF/11602060) | 1 | USB-C receptacle; supplier-labeled 5 V and 3 A/5 A ratings | 0.85 | 0.85 | 18,970 |
| C1 | TDK [C1608X5R1V475M080AC](https://www.digikey.com/en/products/detail/tdk/C1608X5R1V475M080AC/3648579) | 1 | Regulator input: 4.7 uF, 35 V, X5R, +/-20%, 0603 | 0.44 | 0.44 | 120,666 |
| C2 | Taiyo Yuden [LMK107BJ475KA-T](https://www.digikey.com/en/products/detail/taiyo-yuden/LMK107BJ475KA-T/1004029) | 1 | Regulator output: 4.7 uF, 10 V, X5R, +/-10%, 0603 | 0.16 | 0.16 | 157,723 |
| C3 | Samsung [CL21A226KPCLRNC](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21A226KPCLRNC/5961270) | 1 | MCU bulk supply: 22 uF, 10 V, X5R, +/-10%, 0805 | 0.39 | 0.39 | 117,285 |
| C4, C6 | Wurth [885012206095](https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/885012206095/5453868) | 2 | Separate MCU/sensor bypass: 0.1 uF, 50 V, X7R, +/-10%, 0603 | 0.10 | 0.20 | 668,801 |
| C5 | TDK [C1608X7R1C105K080AC](https://www.digikey.com/en/products/detail/tdk/C1608X7R1C105K080AC/634395) | 1 | MCU enable delay: 1 uF, 16 V, X7R, +/-10%, 0603 | 0.12 | 0.12 | 1,538,976 |
| R1 | YAGEO [RC0603JR-0710KL](https://www.digikey.com/en/products/detail/yageo/RC0603JR-0710KL/726700) | 1 | MCU enable bias: 10 kohm, +/-5%, 0.1 W, 0603 | 0.10 | 0.10 | 2,604,016 |
| R2, R3 | Panasonic [ERJ-3EKF1002V](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-3EKF1002V/196066) | 2 | Shared I2C pull-ups: 10 kohm, +/-1%, 0.1 W, 0603 | 0.10 | 0.20 | 2,918,667 |
| R4, R5 | Panasonic [ERJ-3EKF5101V](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-3EKF5101V/1746427) | 2 | USB-C CC pull-downs: 5.1 kohm, +/-1%, 0.1 W, 0603 | 0.11 | 0.22 | 185,704 |
| | **Parts total for one board** | **15** | **Excludes PCB, assembly, programmer, cable/source, enclosure, tax and shipping** | | **11.08** | |

For R4/R5, use cut-tape SKU P5.10KHCT-ND at $0.11 each. The saved $0.10 Digi-Reel unit price produces an apparent $11.06 total but omits its service fee; it is not the recommended one-board checkout basis.

## Compatibility and support findings

**Power: pass under the declared estimates.** USB 4.75-5.25 V fits the regulator's 2.5-6.0 V recommended input range. The estimated 3.2-3.4 V output fits the WROOM's 3.0-3.6 V and SHT40's 1.08-3.6 V operating ranges. Regulated load is 400.5 mA versus the regulator's 1 A capability; the separate upstream budget is 410 mA versus the assumed USB limit of 500 mA. The regulator's 1 A rating does not imply that the USB source supplies 1 A.

The output envelope is a design estimate, not an unconditional datasheet tolerance: AP2114 initial accuracy is +/-1.5% at the stated light-load test condition; load regulation is up to 1%/A and line regulation up to 0.1%/V. At roughly 0.4 A, combining those initial/load/line contributions gives approximately 3.234-3.366 V before additional operating margin. The wider 3.2-3.4 V estimate retains margin and remains conditional on the stated use. Dropout screening passes: 4.75 V >= 3.4 V + 0.75 V.

**Thermal screening: pass as an estimate.** Main regulator loss is (5.25 - 3.2) x 0.4005 = 0.821 W. The chosen 0.9 W allowance is below (125 - 40)/90 = 0.944 W and leaves modest overhead margin. This uses the DPAK value, not the SOT-223 value, and is not a measured junction temperature or a promise about arbitrary PCB copper/layout.

**I2C feasibility: pass in both directions.** Using the declared supply envelope and source VDD-scaled limits:

| Direction | Pulled-up high versus receiver threshold | Driver low versus receiver acceptance |
| --- | --- | --- |
| WROOM to SHT40 | 3.2 V > 0.7 x 3.4 = 2.38 V | 0.1 x 3.4 = 0.34 V < 0.3 x 3.2 = 0.96 V |
| SHT40 to WROOM, including SDA responses | 3.2 V > 0.75 x 3.4 = 2.55 V | SHT40 0.4 V < 0.25 x 3.2 = 0.80 V |

The SHT40 low-output condition applies above 2 V with pull-ups greater than 390 ohms. The selected 10 kohm +/-1% parts remain at least 9.9 kohm, unlike the previous 390 ohm +/-5% choice. The MCU provides I2C resources and the single sensor's 0x44 address creates no bus-address conflict. No level shifter or fixed GPIO allocation is needed to establish feasibility; later routing must preserve the compact-board/100 kHz assumption.

**External support: covered.** The BOM includes separate regulator input/output capacitors, MCU bulk/high-frequency bypass, its recommended enable resistor/capacitor, sensor bypass, two shared I2C pull-ups, and two USB-C CC pull-downs. WROOM-internal flash, crystal, RF circuitry and PCB antenna are not purchased twice. The selected fixed AP2114D has no separate external EN terminal requiring an additional enable part. Programming can use an external fixture without adding a permanent connector to this BOM.

## Source basis and limits

Page numbers below are original physical PDF pages, not sliced-attachment ordinals.

- [Espressif WROOM-32E/32UE datasheet v2.1](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf): pp2, 28-29 for function, operating/DC limits and the 379 mA RF peak condition; p37 for module-internal circuitry; p39 for external 22 uF/0.1 uF and recommended 10 kohm/1 uF support. The 379 mA value is a stated RF condition at 3.3 V and 25 C, not a universal workload bound.
- [Sensirion SHT4x datasheet v7.3](https://sensirion.com/media/documents/33FD6951/6A7C10A0/HT_DS_Datasheet_SHT4x_V7.3.pdf): p3 typical 100 nF/two-pull-up application; p9 supply, heater-off measurement current, proportional input thresholds and conditional output-low limits; pp21-22 variant/address information.
- [Diodes AP2114 datasheet, January 2013 rev2.2](https://www.diodes.com/assets/Datasheets/AP2114.pdf): p3 package applicability; p7 recommended input range and package-specific thermal resistance; p12 exact 3.3 V accuracy, current, load/line and dropout conditions; p25 fixed-output 4.7 uF input/output application.
- [TI manufacturer-hosted power-only USB-C guidance](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/799330/tusb320-usb-type-c-minimum-system-for-power-sink-only-and-no-data): Rd/default-current configuration guidance, not exact Amphenol ratings. Exact connector/passive identities, packages, values, ratings and offers use the labeled supplier records linked in the table.

The first saved automated record contains stale ESP32-S3 prose and incomplete/misreferenced input-voltage and bidirectional-signal checks. The follow-up repairs the module description and regulator input range, but still attributes sensor output-low evidence to the MCU driver and omits the reverse-direction signal check. Its final review did not fit the remaining input budget. Its retained generic connector-brochure 100 V observation is not an exact-part rating; this audit uses the actual supplier ratings instead. These are unfinished assessment records, not additional component incompatibilities identified by this audit. No saved-run status or evidence was manually rewritten; neither run is a completed unattended backend success.
