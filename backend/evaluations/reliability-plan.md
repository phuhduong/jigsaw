# Reliability acceptance batch

Declared before fresh testing of numeric bindings on 2026-09-30. Development replays and
smoke runs are diagnostic, not acceptance successes. The model remains Gemini 3.5 Flash Lite.

Run each request below twice from a new run, in listed order, on unchanged final code and
configuration. No per-request hints, manual repairs, overrides or acceptance-only budgets.
Use the real HTTP workflow, supplier and manufacturer sources. Record all attempts, including
rate limits, timeouts and unavailable sources. Existing source-file caching is normal runtime
behavior; do not preload a completed design or a curated answer.

1. A temperature and humidity sensor with Wi-Fi and Bluetooth, powered by USB-C (5V) for indoor use.
2. A USB-C (5V) powered indoor air pressure sensor with Wi-Fi for data logging. Use a board-mountable controller module, not a development board.
3. A USB-C (5V) powered Bluetooth button remote for indoor use, with one pushbutton and a status LED.
4. A USB-C powered indoor ambient-light sensor that reports readings over Wi-Fi. Use board-mountable parts, not a development board.
5. A USB-C powered Bluetooth indoor temperature logger with a status LED. Use board-mountable parts, not a development board.

## Finish condition

At least 9 of 10 runs finish `checked`, with every required BOM placement selected and a usable
purchase link. Report sourcing separately; missing stock/pricing is not electrical failure.
All checked outputs receive a source-based audit independent of the production reviewer.
None may contain a material incompatibility, missing necessary support, unsupported numerical
calculation, or unfulfilled requested function. The audit must not repair the design to pass it.
Disclosed, reasonable feasible operating assumptions are acceptable; invented device ratings
and silently weakened user requirements are not.

For every attempt report request, run ID, lifecycle, compatibility, sourcing, input/output tokens,
model calls, corrections and duration. Confirm saved report, terminal stream and exports agree.
Any material false positive fails the batch regardless of the completion percentage. If code
changes after a failure, identify that batch as diagnostic and rerun the complete batch on the
new final revision. Do not count a mixture of successful runs from different revisions.

For the final prompt-37 evaluation, the user's stop condition is authoritative: finish the
targeted fixes, freeze the runtime, then attempt each listed query twice consecutively
(1a, 1b, 2a, 2b, through 5b). Audit every checked output. If the batch misses this gate,
pause and report the failure patterns without starting another repair or evaluation cycle.

This is a practical regression gate for small low-voltage USB sensor/control devices, not a
statistical guarantee for every embedded-system request. Record limitations and all failures.
It introduces no production orchestration or live unit tests.
