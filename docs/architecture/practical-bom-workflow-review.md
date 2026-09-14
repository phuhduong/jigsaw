# Jigsaw implementation design: independent review record

Date: 2026-09-13  
Reviewed document: [autonomous BOM selection and compatibility review](practical-bom-workflow.md)  
Disposition: ready for implementation; no unresolved material architecture findings

## What was reviewed

The requested product accepts a high-level embedded-device description, autonomously selects real components and their support parts, checks their proposed use together with manufacturer evidence, and returns a purchasing BOM. The design retains LangChain for model portability and the existing application stack, with a fixed Python workflow and bounded corrections.

This record covers architecture and implementation readiness. It does not claim the application has been built, that live model/provider experiments passed, or that an electrical engineer certified a circuit. The independent reviewers were separate AI agents, with separate review tasks and no access to each other's draft-review findings. The author reconciled their findings, performed additional source checks, and revised the document. Independence of these reviews is useful for finding omissions; it is not independent physical evidence or a guarantee against correlated model errors.

## Review process

1. The author re-inspected the backend, Pydantic models, prompts, supplier mapping, frontend state/events, and existing proposal. The earlier audit's controlled probes had reproduced failure and state-loss behavior; those are repository findings, not tests of the proposed new workflow.
2. Three reviewers independently inspected the repository and proposed minimal requirements before the new draft was written: implementation feasibility, engineering/evidence adequacy, and simplicity/scope.
3. Each reviewer read the complete first draft and attempted to find contradictions, false successful outcomes, omitted capability work, or unnecessary machinery. They were explicitly asked to avoid importing the prior compiler's stronger proof contract.
4. The author applied the material contract clarifications and accepted simplifications. No framework, database, worker service, or generalized electrical subsystem was added.
5. All three reviewers re-read the revised design and returned ready-for-implementation dispositions. The author added a concrete empty-design test detail and checked links and source preservation before delivery.

| Independent reviewer | Adversarial focus | Final disposition |
|---|---|---|
| `implementation_review` | Whether the actual repository can implement the state, supplier, API, provider, runtime and correction contracts without another redesign. | Ready. No remaining material contradictions or unaddressed findings. |
| `engineering_review` | Missing support, wrong supply, changed configuration, omitted user requirements, unreadable circuit figures, stale findings, and all-unknown output. | Ready. No remaining material engineering/evidence architecture findings. |
| `simplicity_review` | Hidden platforms, migration work, over-strong claims, unbounded operation, and smaller viable alternatives. | Ready. No remaining material contradiction or new complexity creep. |

## Findings and resolution

The first review found no high-severity reason to replace the architecture. Medium findings were implementation-contract gaps that could cause incorrect results or runtime failures; they were resolved before final acceptance.

| Finding | Severity | Resolution in the final design |
|---|---|---|
| One passing finding per review area could conceal an omitted requested function or unresolved component slot. | Medium | Require current coverage for every explicit requirement and unresolved selection/support slot, plus comparison against original user clauses. Add empty-design/all-not-applicable adversarial cases. |
| Code could not distinguish a blocking pre-layout gap from ordinary layout guidance using the proposed record. | Medium | Add `kind` distinguishing `check` from `guidance`; explicit requirements, missing selections/connections, required support and applicable code failures cannot be downgraded. Define aggregate precedence. |
| Reused extraction could preserve a configuration-specific conclusion after a design change. | Medium | Preserve source conditions; re-evaluate applicability and support conclusions on every engineering revision. Cache identical extraction inputs within a run only; defer cross-run extraction caching. |
| A process-local admission lock would not enforce one active run under multiple backend processes. | Medium | Specify one threaded backend process, debug/reloader off, loopback defaults and configured frontend origin. Multi-worker/public serving is a later deployment decision. |
| Exceptions or generator closure could leave admission held or a run falsely active. | Medium | Save an initial snapshot; release admission in `finally`; save terminal/interrupted state where possible; handle `GeneratorExit` and storage failure explicitly. |
| Per-call timeouts could overrun the run deadline or reset within MCP initialization/authentication/retry. | Medium | Each logical operation uses the remaining run time and a shared operation deadline. Reconcile both sides of MCP, emit progress before attempts, and end with a retryable partial result when backoff exceeds serving limits. |
| USB supply assumptions could confuse a charger rating or CC termination with an established operating-current budget. | Medium | Tie budget to the selected source/attachment mode and documented detection/negotiation or explicit source contract. Leave an unsupported budget unresolved. No USB rules platform added. |
| Clarification answers lacked a concrete route/question contract. | Low | Record stable pending question IDs; `/api/refine` accepts exactly one modification or an answers mapping and starts a new run. Reject a running base and unknown questions. |
| Purchasing options and terminal/error snapshots were underspecified. | Low | Define board quantity, region/currency, inheritance, exact retrieval/export routes, saved terminal snapshots, and EOF/disconnect behavior. |
| Total token allowance did not ensure a review payload fit the individual model context. | Low | Add per-request context allowance including PDF input and output reservation; retain source locators and explicitly report required unread material. |
| “Unknown” could let an evaluation evade a material defect, and repeating every test as a full live run would waste resources. | Low | Sufficient-evidence faults need the specific supported conflict or repair. Insufficient-evidence cases expect unknown. Separate fixed-snapshot review, selection/correction, and deterministic transport/state tests. |

Two further simplifications were accepted: hide the existing inferred PCB view during initial implementation instead of requiring a graph rewrite, and make persistent cross-run extraction caching optional future optimization. Reusing current offers needs a refresh only when they are actually stale. One provider passing the required fixtures is enough to start; LangChain portability does not require simultaneous launch support for several providers.

## Alternatives challenged

| Alternative | Why it was not selected |
|---|---|
| Prompt-only repair | Leaves absent manufacturer evidence, support selection, connection state and reliable outcome handling unresolved. |
| Open-ended outer agent loop | Adds uncertain completion/repair behavior without removing the need for a canonical design, evidence records, and checks. Bounded evidence requests within a fixed stage preserve useful autonomy. |
| Previous deterministic compiler | Its exact-part admission, exhaustive rules, qualification records and substantial application infrastructure follow from a much stronger promise than the user wants. |
| Remove LangChain | Existing use is lightweight model invocation; provider portability is a user priority. No repository defect requires its removal. |
| Replace Flask or immediately port DigiKey MCP | Adds migration work before addressing the observed engineering-information failures. Keeping the integrations does not prevent repairing their contracts. |
| Add a worker, SQLite, or external queue immediately | The first local/private milestone explicitly accepts interruption and one active run. One process and atomic JSON snapshots meet that requirement. Surviving disconnects would be a concrete future reason to revisit execution. |

## Grounding and source checks

The repository's main problems are directly visible in [pipeline.py](../../backend/pipeline.py), [validation_agent.py](../../backend/agents/validation_agent.py), [component_retriever.py](../../backend/agents/component_retriever.py), [models.py](../../backend/models.py), [the DigiKey mapper](../../mcp-server/src/client.ts), and [frontend design state](../../frontend/app/design/index.tsx). These include per-part summary-only approval, uninvoked cross-check prompt, rejected-result fallback, retry state loss, discarded refinement verdicts, category collisions, lossy electrical/sourcing fields, and unconditional frontend compatibility claims.

Primary documentation supports the selected integration approach: LangChain permits standalone model calls and standardized model/message interfaces; document and structured-output support still depend on provider capability. [Models](https://docs.langchain.com/oss/python/langchain/models), [document messages](https://docs.langchain.com/oss/python/langchain/messages). DigiKey exposes search and detailed product retrieval, supporting a narrow supplier adapter. [ProductSearch API](https://developer.digikey.com/products/product-information-v4/productsearch).

The [Sensirion SHT4x datasheet](https://sensirion.com/resource/datasheet/sht4x), version 7.3, demonstrates why circuit figures must be supplied to the model rather than relying solely on extracted text. The [Espressif module datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) distinguishes module-internal circuitry from external peripheral circuitry and provides a concrete variant/applicability case. These are targeted evaluation sources, not evidence that the new software has already processed them correctly.

An initially suggested [Microchip reference page](https://onlinedocs.microchip.com/oxy/GUID-D5B5915F-6907-409C-A6D9-F79690ACDCA3-en-US-1/GUID-C41250F6-354D-4AF8-B073-3BEA77A0FF54.html) explicitly marks its section unfinished and not for use. The author caught that warning during source verification; the reviewer retracted the recommendation and it was excluded as fixture authority. This illustrates why manufacturer provenance alone does not settle document applicability.

The author also checked the documented PDF extraction and page-selection capabilities of `pypdf`. Extraction supplies text and locators; it does not establish schematic interpretation. [Text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), [page selection](https://pypdf.readthedocs.io/en/stable/user/merging-pdfs.html).

## What remains to learn through implementation

- Whether the selected model extracts and interprets actual tables, footnotes and schematic figures well enough for useful results.
- Whether full-design review catches omitted support and incompatible selections, including on held-out requests.
- Whether source discovery and candidate sourcing succeed across common parts without another search service.
- Whether the example fits the configured model's quota, latency and token allowance.

The design assigns these questions to early milestones and concrete tests. They do not justify another speculative architecture. The first successful live BOM and evaluation results are still required before claiming the application achieves the product promise.

Only the new design document and this review record were authored. The application code and existing architecture proposal were preserved.
