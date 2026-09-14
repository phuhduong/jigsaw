# Prompt 14: fresh sensor BOM audit

Independent source audit, 2026-09-14 UTC. [Run dfc40e2ded4544d6b73967bdf33d5a45](../data/runs/dfc40e2ded4544d6b73967bdf33d5a45.json) used the original request with no parent or manually supplied parts/pages. [Events](../data/evaluations/prompt14-fresh-events.jsonl) preserve the automatic workflow.

**Outcome: not an accepted automatic checked result.** Saved status is `finished / incomplete / available`; whole-BOM review completed, but three receiver-voltage checks remain unknown. The run used 22 model calls, 287,075 input tokens and 147.74 seconds before exhausting its input budget. No run data was edited for this audit.

## Actual parts and support

15 placements / 12 manufacturer-MPN groups, **$9.63** single-board cut-tape subtotal in saved DigiKey offers from 2026-09-14 04:49-04:50 UTC. An independent catalog cross-check found MOQ 1 and sufficient stock for every group. Price excludes PCB, assembly, tools/source/cable, enclosure, tax and shipping.

Core parts are ESP32-WROOM-32E-N4, SHT40-AD1B-R2, GCT USB4125-GF-A, and **Diodes AZ1117CH-3.3TRG1, SOT-223**. The six-contact connector is appropriate for power-only USB-C; it is not a USB data interface. The actual regulator differs from the search hint and was audited against its own manufacturer document.

The BOM includes module 22 uF/100 nF bypass, 10 kohm/1 uF enable delay, sensor 100 nF bypass, two 3.9 kohm +/-1% I2C pull-ups, 10 uF regulator input and 22 uF output capacitors, and two 5.1 kohm +/-5% CC pull-downs. No necessary purchased support omission or intrinsically incompatible part was identified. Unlike some other 1117 devices, this exact regulator explicitly supports low-ESR ceramic output capacitors: minimum 10 uF, ESR below 20 ohms, with 22 uF in its example circuit. Exact bias/temperature behavior remains implementation verification, not a nominal-capacitance guarantee.

Both I2C driving directions have correct device ownership and comfortable static logic margins. The 3.9 kohm pull-ups clear the sensor's resistance condition. A single sensor at 0x44 creates no address conflict; a compact, appropriately loaded bus offers a feasible configuration. Off-board programming does not require a complete pin/header plan in this BOM audit.

## Unresolved claims and configuration

1. **Receiver ranges were overwritten with source ranges.** U3's input limits are uncited 4.75-5.25 V USB values. U1/U2's receiving limits are the regulator's 3.235-3.365 V output limits, citing regulator evidence rather than their own 3.0-3.6 V and 1.08-3.6 V ranges. Code correctly rejects these records. The selected devices are not thereby physically incompatible.
2. **Thermal assumptions are unreconciled.** The saved assumption calculates `(125-55)/125 = 0.56 W` for a 55 C ambient and 125 C/W no-heatsink package condition, but the numeric allowance is 0.84 W. At the recorded 300 mA mean load, worst-envelope loss is `(5.25-3.235) x 0.3 = 0.6045 W`, before regulator ground-current loss. Thus the stated no-heatsink case does not pass its own thermal screen. The review mentions an alternative 0.7 W copper-cooled case: the manufacturer documents 100 C/W with a specified 100 mm2 copper/2 oz/two-layer/via setup, which could make the parts feasible. That alternative must be adopted consistently rather than leaving three different allowances in the report. A finished PCB or new heatsink component is not required to state a source-conditioned cooling assumption.
3. **Regulator output accuracy needs its operating conditions.** Page 7's output/line limits assume at least 1.5 V input-output differential and a stated test load. At the minimum USB input, the saved output maximum leaves less than that differential. The 1.3 V maximum SOT-223 dropout at 0.8 A supports plausible headroom, but does not by itself establish the report's exact narrow output envelope at every proposed load. A justified wider estimate or suitable operating constraint is needed; this is not proof that the part cannot power the device.
4. **Minor catalog substitution:** C4 is a 100 nF, 100 V X8L capacitor despite the X7R search hint. No source-backed incompatibility with its sensor-bypass role was found. It should be described as the actual selected part.

The automatic parts selection is reasonable, but the saved operating/evidence record is not yet consistent enough to accept as checked. No physical hardware failure was observed or claimed. Reconciled load/cooling and voltage-envelope assumptions may resolve this without replacing components.

## Primary source basis

- [Diodes AZ1117C, September 2022 rev5-2](https://www.diodes.com/assets/Datasheets/AZ1117C.pdf): original physical p3 ceramic support/application; p4 recommended conditions and package/copper-dependent thermal resistance; p7 exact 3.3 V, dropout, load/line and quiescent-current conditions. These pages were visually inspected.
- [GCT USB4125/4130/4135 specification revA3](https://gct.co/files/specs/usb4125-spec.pdf): physical p2 identifies the power-only family, 3 A collective VBUS rating and 48 V DC rating.
- [Espressif WROOM-32E/32UE v2.1](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf): pp28-29 operating/logic/current limits and p39 external support; same original source as the preceding independent audit.
- [Sensirion SHT4x v7.3](https://sensirion.com/media/documents/33FD6951/6A7C10A0/HT_DS_Datasheet_SHT4x_V7.3.pdf): p3 application, p9 electrical/current conditions, pp21-22 selected address variant. Supplier identities, values and offers remain available in the linked saved run.
