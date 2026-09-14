# Prompt 17: fresh sensor BOM audit

Independent audit of [run bbafb862ecf647ebab38dbc8cd126b5b](../data/runs/bbafb862ecf647ebab38dbc8cd126b5b.json), 2026-09-14 UTC. The [event record](../data/evaluations/prompt17-fresh-events.jsonl) shows an original-query run without manual parts/pages or runtime reviewer feedback. No saved run or production code was edited for this audit.

**Outcome: not accepted.** Final status is `finished / issues_found / available`, with `review_completed=false` and an input-budget stop: 22 model calls, 282,119 input tokens, 29,224 output tokens, 139.22 seconds. This assessment permits minor reporting errors where the same parts and saved operating configuration have adequate source-supported margin. The defects below include actual selected-part mismatches, not a demand for exhaustive proof.

## Final parts and sourcing

Core parts are ESP32-WROOM-32E-N4, SHT40-AD1B-R2, Amphenol 10164359-00011LF and **TI TLV75533PDBVR**. The earlier 200 mA TPS730 choice was automatically replaced and is not counted as a remaining defect. The final regulator is a 500 mA, fixed 3.3 V SOT-23-5 device. The six-contact USB-C connector is power-only, which serves this request and its off-board-programming assumption.

Independent catalog checking found **15 placements / 12 manufacturer-MPN groups, $9.18** in saved single-board cut-tape offers, all with MOQ 1 and sufficient stock. This is a parts-only snapshot, not a price including PCB, assembly, external equipment, enclosure, tax or shipping. Exact purchase links and timestamped offers remain in the run.

## Actual remaining defects

- **Regulator input capacitor is ten times too small for the specified support.** D6S1 says C5 is 1 uF, but actual TDK **CGA3E2X7R1E104K080AA** is **0.1 uF +/-10%, 25 V X7R**. TI physical p4 specifies 1 uF input capacitance; p15 explicitly calls for 1 uF or greater. No other capacitor is assigned to that input. The BOM must change to satisfy this requirement; relabeling the existing part cannot fix it.
- **I2C pull-ups violate the documented minimum after tolerance.** R3/R4 are Panasonic **ERJ-3GEYJ391V**, 390 ohms +/-5%, permitting 370.5 ohms. Sensirion p9 requires at least 390 ohms at this supply and conditions its 0.4 V output-low limit on greater than 390 ohms. Static threshold arithmetic cannot independently establish the cited low-state claim outside that condition. This does not prove every built board fails, but a compliant selected value/tolerance is needed.
- **The saved thermal screen fails its own chosen target.** For the final DBV package, TI p5 gives the recorded JEDEC theta_JA of 231.1 C/W. The run's 50 C ambient, 115 C target and 150 mA average load yield `0.3024 W` estimated loss versus `(115-50)/231.1 = 0.2813 W` allowance. Code correctly reports failure. The estimate is about 120 C junction temperature, below the device's 125 C recommended maximum, so this is not evidence of damage or certain shutdown. Accepting the saved 115 C target would nevertheless require a changed cooling/workload/part assumption; the audit does not silently make that change.

C3 is also **0.1 uF** (KYOCERA AVX KGM15AR71C104KT), while D1S2 claims the selected EN network uses 1 uF. With 10 kohms it has a nominal 1 ms, rather than 10 ms, time constant. That does not alone prove a boot failure: the manufacturer recommends a usual setting and allows timing adjustment. It is still a real selected-value/report mismatch, not the claimed 1 uF implementation.

## Nonblocking observations

The final regulator's documented 1.45-5.5 V input range and low dropout leave ample headroom from the declared 4.75-5.25 V USB source. The reported 215 mV dropout applies through 85 C; the full-temperature DBV maximum is 238 mV, which still leaves ample margin without changing the saved supply. Likewise, the approximate output-envelope wording is not itself the rejection reason: reasonable regulation variation leaves substantial margin to the module's 3.0-3.6 V and sensor's 1.08-3.6 V supply ranges.

The 350 mA MCU current record understates its cited 379 mA WiFi-mode peak, but the actual 500 mA regulator/source still have useful capacity margin for the heater-off sensor case. That reporting error is not by itself evidence of an undersized final regulator. C4's 100 V X8L dielectric differs from the search hint, but its 100 nF bypass value is correct and no functional incompatibility was identified. Required module bypass, USB CC resistors and regulator output capacitance are present. No onboard programmer, exact pin allocation or finished PCB qualification is required for this assessment.

No hardware was built or tested. The final BOM cannot be accepted unchanged because of the input-capacitor and pull-up selections; this conclusion does not depend on enforcing perfect prose or exact decimal envelopes. The automatic workflow also did not reach checked status or complete final review.

## Primary source basis

- [TI TLV755P revD](https://www.ti.com/lit/ds/symlink/tlv755p.pdf): physical pp4-6 operating/capacitor limits, exact package thermal values and conditioned dropout; p15 capacitor guidance. Pages 4 and 5 were visually inspected.
- [Sensirion SHT4x v7.3](https://sensirion.com/media/documents/33FD6951/6A7C10A0/HT_DS_Datasheet_SHT4x_V7.3.pdf): p9 electrical and pull-up conditions, visually inspected; p3 typical support.
- [Espressif WROOM-32E/32UE v2.1](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf): pp28-29 operating/logic/current conditions and p39 recommended external support, previously visually checked for this exact module.
- [TI TPS730 revK](https://www.ti.com/lit/ds/symlink/tps730.pdf): pp4-5 were inspected only to verify the discarded 200 mA candidate. Its ratings were not transferred to the final TLV755.
