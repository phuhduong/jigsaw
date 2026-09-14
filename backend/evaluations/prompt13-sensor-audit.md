# Prompt 13: fresh sensor BOM source audit

Audited 2026-09-14 UTC. [Saved run 144d0c45a45847eb88939e1bd4f0b6cc](../data/runs/144d0c45a45847eb88939e1bd4f0b6cc.json) used the original sensor sentence, no parent run, and no manually supplied parts or source pages. Model: `gemini-3.5-flash-lite`, provider-default thinking. [Saved events](../data/evaluations/prompt13-fresh-events.jsonl) record the autonomous workflow.

**Disposition: the selected parts form a feasible conditional pre-layout BOM, but this is not a completed automated checked result.** The run ended `finished / incomplete / available` after 128.47 seconds, 21 model calls, 288,149 input tokens and two correction rounds. Its whole-BOM review completed; the remaining code unknown is the I2C interface's empty evidence-reference list. This audit neither changes that status nor endorses every generated claim.

## Parts and sourcing

15 placements, 11 manufacturer/MPN groups. An independent catalog-only cross-check found a **$9.61** quantity-one cut-tape subtotal, with sufficient stock and MOQ 1 for every group. These are saved DigiKey offers from 2026-09-14 04:42-04:43 UTC, not future availability guarantees. Excludes PCB, assembly, enclosure, programmer, cable/source, tax and shipping.

| Placements | Manufacturer / buy link | Qty | Function and actual specification | USD line |
| --- | --- | ---: | --- | ---: |
| U1 | Espressif [ESP32-WROOM-32E-N4](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-WROOM-32E-N4/11613125) | 1 | Wi-Fi/Bluetooth MCU module, integrated flash/crystal/PCB antenna | 4.99 |
| U2 | Sensirion [SHT40-AD1B-R2](https://www.digikey.com/en/products/detail/sensirion-ag/SHT40-AD1B-R2/13532084) | 1 | Temperature/humidity sensor, I2C address 0x44 | 1.88 |
| J1 | Amphenol [10155435-00011LF](https://www.digikey.com/en/products/detail/amphenol-cs-fci/10155435-00011LF/11602060) | 1 | USB-C receptacle; supplier-labeled 5 V and 3 A/5 A | 0.85 |
| U3 | Diodes [AP2112K-3.3TRG1](https://www.digikey.com/en/products/detail/diodes-incorporated/AP2112K-3-3TRG1/4470746) | 1 | Fixed 3.3 V, 600 mA LDO, SOT-25 | 0.28 |
| C1 | Samsung [CL21A226KPCLRNC](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21A226KPCLRNC/5961270) | 1 | Module bulk: 22 uF, 10 V, X5R, +/-10% | 0.39 |
| C2 | KYOCERA AVX [KGM15AR71C104KT](https://www.digikey.com/en/products/detail/kyocera-avx/KGM15AR71C104KT/563349) | 1 | Module bypass: 100 nF, 16 V, X7R, +/-10% | 0.10 |
| C3 | Samsung [CL10A105KO8NNNC](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL10A105KO8NNNC/3886692) | 1 | Module enable delay: 1 uF, 16 V, X5R, +/-10% | 0.11 |
| C4 | Samsung [CL10E104KC8VPNC](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL10E104KC8VPNC/20498486) | 1 | Sensor bypass: 100 nF, 100 V, X8L, +/-10% | 0.27 |
| C5, C6 | Murata [GRM188R61A105KA61D](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R61A105KA61D/587071) | 2 | Separate LDO input/output: 1 uF, 10 V, X5R, +/-10% | 0.24 |
| R1, R2, R3 | Panasonic [ERJ-3EKF1002V](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-3EKF1002V/196066) | 3 | Enable bias and two I2C pull-ups: 10 kohm, +/-1%, 0.1 W | 0.30 |
| R4, R5 | Panasonic [ERJ-3GEYJ512V](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-3GEYJ512V/135918) | 2 | USB-C CC pull-downs: 5.1 kohm, +/-5%, 0.1 W | 0.20 |

No missing necessary purchased support or inherently incompatible selected part was identified for the configuration below. Module-internal circuitry is not purchased twice. Off-board UART programming is feasible without requiring a permanent programming header or bridge. Numbered pins and a complete reset/programming wiring plan are outside this audit.

## Feasible operating conditions and source checks

- **Power:** known power-only USB-C source, nominal 5 V with the recorded 4.75-5.25 V envelope and 500 mA capacity; 400 mA peak upstream design budget. Two CC pull-downs identify the sink but do not negotiate higher current.
- **Sensor heater off:** the source maximum measurement current is 0.5 mA without heating. The saved 1 mA estimate is adequate for that use, not for all heater modes.
- **Regulation:** 2.5-6 V recommended LDO input range and 600 mA output capability accommodate the chosen supply and approximately 380 mA peak load. The 0.4 V maximum dropout at 600 mA leaves ample headroom. A conservative estimated 3.2-3.4 V output envelope, allowing initial/load/line contributions and margin, fits the module's 3.0-3.6 V and sensor's 1.08-3.6 V ranges.
- **Thermal:** retain the run's separate 200 mA sustained-output workload constraint and maximum 40 C ambient, without treating peak delivery as continuous dissipation. With SOT-25's indicative 184 C/W and a chosen 125 C junction target, allowance is (125-40)/184 = 0.462 W. At the wider voltage envelope, estimated loss is (5.25-3.2) x 0.2 = 0.410 W. This is a plausible periodic-sensor configuration, not permission for arbitrary continuous high-duty transmission. Firmware workload and later thermal/transient implementation checks must preserve the stated constraint.
- **I2C:** use a compact board at standard-mode 100 kHz; both driving directions have ample static logic margin. At the wider supply envelope: module VOL <=0.34 V is below sensor VIL=0.96 V; sensor VOL <=0.4 V is below module VIL=0.80 V. A 3.2 V pulled-up high exceeds both worst receiver thresholds, 2.38 V and 2.55 V. The 10 kohm +/-1% pull-ups remain above the sensor's >390 ohm low-output condition. A single 0x44 sensor creates no address conflict. Faster operation requires an appropriate capacitance/rise-time assumption, not merely the label "fast mode."
- **Support:** external module 22 uF/100 nF and 10 kohm/1 uF delay, sensor 100 nF, two bus pull-ups, two CC pull-downs, and separate LDO input/output capacitors are present. LDO capacitors use the recommended X5R class. Exact capacitor bias/temperature behavior remains implementation verification; this audit does not invent a guaranteed effective-capacitance floor from nominal values alone.

## Remaining report defects

1. `INT_I2C.evidence_ids` is empty, so the backend correctly leaves interface compatibility unresolved despite the reviewer passing it. Both numeric driving-direction records are now present and use the correct device owners.
2. `ASM5` incorrectly says heater modes fit under 1 mA. The strongest documented heater mode reaches 100 mA. Explicit heater-off operation is a necessary clarification to retain the stated load model; no replacement sensor is needed.
3. The saved 3.2505-3.3495 V output bounds use initial accuracy measured at light load, while the load/line-regulation facts are also available. They do not establish that narrow envelope at every proposed load. The wider conditional estimate above still supports these selected parts.
4. The review calls all capacitors X5R/X7R, but C4 is X8L. Its nominal value and voltage rating suit the sensor-bypass role; no source-backed functional incompatibility was identified. The blanket description is nevertheless false.

These distinctions matter: this fresh run produced a usable-looking parts selection without manual part hints, but its generated report is not yet a clean, independently accepted `checked` outcome. No hardware was built or tested, and no PCB qualification or certification is claimed.

## Manufacturer source basis

Physical page numbers refer to original PDFs, not attachment ordinals. The relevant original table/application pages were inspected, including visual module-boundary review.

- [Espressif WROOM-32E/32UE v2.1](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf): pp2/19 for functions/I2C; pp28-29 for operating, logic and RF current limits; p37 internal module circuitry; p39 external support and UART programming. The 379 mA peak and 239 mA average belong to the stated 802.11b TX condition at 3.3 V/25 C; they are not universal firmware bounds.
- [Sensirion SHT4x v7.3](https://sensirion.com/media/documents/33FD6951/6A7C10A0/HT_DS_Datasheet_SHT4x_V7.3.pdf): p3 application, p9 supply/current/logic/pull-up conditions, pp21-22 exact address variant.
- [Diodes AP2112 rev2-2](https://www.diodes.com/assets/Datasheets/AP2112.pdf): p2 separate input/output support and X5R/X7R recommendation; p3 recommended input and SOT-25 thermal resistance; p8 exact 3.3 V output, load/line, current and dropout conditions.
- [TI manufacturer-hosted power-only USB-C guidance](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/799330/tusb320-usb-type-c-minimum-system-for-power-sink-only-and-no-data): default-current/Rd configuration, not exact connector ratings. Connector and passive identities/ratings/offers use the labeled supplier records linked above.
