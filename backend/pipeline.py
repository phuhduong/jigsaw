"""Explicit, bounded requirements -> parts -> evidence -> review -> correction workflow."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Literal

from checks import refresh_checks
from documents import DocumentError
from llm import Budget, BudgetExceeded, ModelGateway
from models import (
    OperatingConfiguration,
    Component,
    Correction,
    DesignRun,
    Evidence,
    EvidencePacket,
    Finding,
    PageSelection,
    Product,
    ReadingPlan,
    now,
)
from prompts import CONFIGURE, CORRECT, EXTRACT, READ, USB_C_GUIDE_URL
from pydantic import Field, create_model
from pydantic.json_schema import SkipJsonSchema
from run_store import design_context
from stages import (
    find_capacitance_mismatch,
    plan_requirements,
    review_bom,
    select_candidates,
)
from tools import SupplierClient, SupplierError


def compact_inventory(inventory, max_chars=10000):
    pages = []
    for page in inventory["pages"]:
        lines = [" ".join(line.split()) for line in page["text"].splitlines() if line.strip()]
        contents = any(re.fullmatch(r"(?:table of )?contents", line, re.I) for line in lines[:12])
        headings = [
            line
            for line in lines
            if len(line) <= 140
            and re.search(
                r"operating conditions|electrical|current consumption|pin description|pin assignment|boot|reset|"
                r"application|schematic|power supply|DC characteristics|ordering|pinout|"
                r"function(?:al)?\s+description|(?:input|output)\s+capacit(?:or|ance)",
                line,
                re.I,
            )
        ]
        # Dotted TOC leaders can otherwise hide the last chapters of large manuals.
        if contents:
            preview = re.sub(r"(?:\.\s*){3,}", " ... ", " / ".join(lines))[: max_chars // 2]
            score = 100
        else:
            preview = " / ".join(dict.fromkeys(headings[:4] + lines[:2]))[:280]
            score = 20 + min(len(headings), 5) if headings else 0
            if page["page_number"] == 1:
                score = 90
        pages.append((score, {"page": page["page_number"], "sections": preview, "text_status": page["text_status"]}))
    result = {
        "document_id": inventory["document_id"],
        "url": inventory["url"],
        "title": inventory["title"],
        "page_count": inventory["page_count"],
        "pages": [],
        "links": inventory["links"][:12],
        "navigation_note": "Navigation only, not read evidence. Omitted page cards remain requestable by original physical page number; contents may use printed page numbers.",
    }
    remaining = max_chars - len(json.dumps(result, ensure_ascii=False))
    for _, card in sorted(pages, key=lambda item: -item[0]):
        size = len(json.dumps(card, ensure_ascii=False)) + 2
        if size <= remaining:
            result["pages"].append(card)
            remaining -= size
    result["pages"].sort(key=lambda page: page["page"])
    result["omitted_page_cards"] = len(pages) - len(result["pages"])
    return result


def merge_page_selections(selections):
    """Keep each original source page once, in first-document order."""
    merged = {}
    for selection in selections:
        previous = merged.get(selection.document_id)
        if previous is None:
            merged[selection.document_id] = selection.model_copy(deep=True)
        else:
            previous.pages.extend(selection.pages)
            if selection.reason and selection.reason != previous.reason:
                previous.reason += "; " + selection.reason
    for selection in merged.values():
        selection.pages = sorted(set(selection.pages))
    return list(merged.values())


class Workflow:
    def __init__(self, documents, supplier=None, gateway=None):
        self.documents = documents
        self.supplier = supplier or SupplierClient()
        self.gateway = gateway or ModelGateway()

    def _build_source_inventories(self, run, document_ids=None, max_chars=10000):
        current = {key for component in run.components for key in component.document_ids}
        if document_ids is not None:
            current &= document_ids
        documents = [d for d in run.documents if d["document_id"] in current]
        allowance = min(max_chars, 30000 // max(1, len(documents)))
        return [compact_inventory(self.documents.inventory(d["document_id"]), allowance) for d in documents]

    def _snapshot(self, run):
        run.updated_at = now()
        refresh_checks(run)
        return {"type": "snapshot", "stage": run.stage}

    @staticmethod
    def _assert_unique_ids(items, name):
        ids = [x.id for x in items]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate {name} IDs in proposed design")

    @staticmethod
    def _invalidate_parts(run, identifiers):
        """Even same-document replacements must not inherit another variant's facts."""
        if not identifiers:
            return
        for field, owners_field in (
            ("evidence", "component_ids"),
            ("evidence_errors", "subject_ids"),
        ):
            kept = []
            for item in getattr(run, field):
                owners = [key for key in getattr(item, owners_field) if key not in identifiers]
                if owners:
                    kept.append(item.model_copy(update={owners_field: owners}))
            setattr(run, field, kept)
        run.invalidate_configuration()

    def _select_components(self, run, budget, component_ids=None):
        run.stage = "select"
        pending = [
            c
            for c in run.components
            if c.product is None and (component_ids is None or c.id in component_ids)
        ]
        cache = {}
        for attempt in range(2):
            if not pending:
                return
            candidates = {}
            for component in pending:
                query = component.search_query if attempt == 0 else (component.broad_query or component.name)
                if not query:
                    candidates[component.id] = []
                    continue
                yield {"type": "progress", "stage": "select", "message": f"Searching for {component.name}: {query}"}
                try:
                    if query not in cache:
                        budget.consume(supplier_calls=1)
                        cache[query] = self.supplier.search(
                            query,
                            region=run.options.region,
                            currency=run.options.currency,
                            timeout=min(20, budget.remaining()),
                            limit=3,
                        )
                    if not cache[query]:
                        component.selection_error = f"No catalog results for {query!r}; try a different part or query"
                    candidates[component.id] = []
                    for candidate in cache[query]:
                        mismatch = find_capacitance_mismatch(component, candidate)
                        if mismatch:
                            component.selection_error = mismatch
                        else:
                            candidates[component.id].append(candidate)
                except SupplierError as error:
                    candidates[component.id] = []
                    component.selection_error = str(error)
            if not any(candidates.values()):
                continue
            picks = yield from select_candidates(self.gateway, budget, run, candidates)
            picked = {p.component_id: p for p in picks.picks}
            for component in pending:
                pick = picked.get(component.id)
                results = candidates[component.id]
                if pick is None or not 0 <= pick.chosen_index < len(results):
                    component.selection_error = pick.reason if pick else "No candidate selected"
                    continue
                candidate = results[pick.chosen_index]
                try:
                    key = candidate["manufacturer"], candidate["mpn"]
                    detail_key = ("detail", *key)
                    if detail_key not in cache:
                        yield {"type": "progress", "stage": "select", "message": f"Confirming {candidate['mpn']}"}
                        budget.consume(supplier_calls=1)
                        offers = candidate.get("offers") or []
                        lookup = offers[0]["sku"] if offers else candidate["mpn"]
                        cache[detail_key] = self.supplier.get_product(
                            lookup,
                            region=run.options.region,
                            currency=run.options.currency,
                            timeout=min(20, budget.remaining()),
                        )
                    product = Product.model_validate(cache[detail_key])
                    if (product.manufacturer, product.mpn) != key:
                        raise SupplierError("Product details did not match the selected manufacturer and MPN")
                    if mismatch := find_capacitance_mismatch(component, product.model_dump()):
                        raise SupplierError(mismatch)
                    component.product = product
                    component.name = product.mpn
                    # Source leads remain untrusted hints until extraction verifies
                    # their applicability to the actual selected catalog variant.
                    component.selection_reason = pick.reason
                    component.selection_error = None
                except (SupplierError, ValueError) as error:
                    component.selection_error = str(error)
            pending = [c for c in pending if c.product is None]
            yield self._snapshot(run)
        for component in pending:
            component.selection_error = component.selection_error or "No suitable catalog candidate found"

    def _fetch_documents(self, run, budget, requested_component_ids=()):
        existing = {url: d for d in run.documents for url in [d["url"], d.get("requested_url", "")]}
        for component in run.components:
            if not component.product or component.kind == "passive" and component.id not in requested_component_ids:
                continue
            urls = [component.product.datasheet_url, *component.document_urls]
            if not any(urls) and component.product.product_url:
                urls = [component.product.product_url]
            if component.kind == "connector" and any(
                str(parameter.get("name", "")).strip().casefold() == "connector type"
                and re.search(r"USB[- ](?:TYPE[- ])?C\b", str(parameter.get("value", "")), re.I)
                for parameter in component.product.parameters
            ):
                urls.append(USB_C_GUIDE_URL)
            component.document_errors = []
            for url in dict.fromkeys(u for u in urls if u):
                # Catalog often returns an HTTP locator for an HTTPS manufacturer site.
                if url.startswith("http://"):
                    url = "https://" + url[7:]
                if url not in existing:
                    yield {
                        "type": "progress",
                        "stage": "evidence",
                        "message": f"Reading manufacturer source for {component.name}",
                    }
                try:
                    if url not in existing:
                        budget.consume(documents=1)
                        metadata = self.documents.fetch(url, timeout=min(20, budget.remaining()))
                        metadata["pages_read"] = []
                        if metadata["document_id"] not in {d["document_id"] for d in run.documents}:
                            run.documents.append(metadata)
                        existing[url] = next(d for d in run.documents if d["document_id"] == metadata["document_id"])
                    document_id = existing[url]["document_id"]
                    if document_id not in component.document_ids:
                        component.document_ids.append(document_id)
                except DocumentError as error:
                    component.document_errors.append(f"{url}: {error}")
            if not component.document_ids:
                component.document_errors.append("No usable manufacturer source was found")

    def _build_source_blocks(self, run, selections, *, include_pdf_text=True):
        blocks, pdf_pages = [], 0
        metadata = {d["document_id"]: d for d in run.documents}
        for selection in selections:
            if selection.document_id not in metadata:
                raise DocumentError("Model requested an unknown document")
            document = metadata[selection.document_id]
            pages = sorted(set(selection.pages))
            if not pages:
                continue
            blocks.extend(self.documents.pages(selection.document_id, pages, include_pdf_text=include_pdf_text))
            if document["media_type"] == "application/pdf":
                pdf_pages += len(pages)
        return blocks, pdf_pages

    @staticmethod
    def _mark_pages_read(run, selections):
        metadata = {d["document_id"]: d for d in run.documents}
        for selection in selections:
            document = metadata[selection.document_id]
            document["pages_read"] = sorted(set(document.get("pages_read", []) + selection.pages))

    def _fetch_requests(self, run, budget, requests):
        if len(requests) > 2:
            raise BudgetExceeded("At most two additional documents may be requested per evidence round")
        components = {c.id: c for c in run.components}
        for request in requests:
            if request.component_id not in components:
                raise DocumentError("Document request names an unknown component")
            component = components[request.component_id]
            if request.url not in component.document_urls:
                component.document_urls.append(request.url)
        yield from self._fetch_documents(run, budget, {request.component_id for request in requests})

    def _plan_source_reads(self, run, budget, instructions="", document_ids=None):
        for attempt in range(2):
            current_documents = {key for component in run.components for key in component.document_ids}
            if document_ids is not None:
                current_documents &= document_ids
            inventories = self._build_source_inventories(run, current_documents)
            result = yield from self.gateway.call(
                budget,
                "choose evidence pages",
                ReadingPlan,
                READ,
                {
                    "components": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "mpn": c.product.mpn if c.product else None,
                            "purpose": c.purpose,
                            "catalog_parameters": c.product.parameters if c.product else [],
                            "document_ids": c.document_ids,
                            "document_errors": c.document_errors,
                        }
                        for c in run.components
                    ],
                    "request": run.original_request,
                    "latest_modification": run.modification,
                    "documents": inventories,
                    "reading_scope": "Choose pages from these inventories; previously read unchanged sources remain in the evidence ledger.",
                    "existing_observations": run.evidence,
                    "source_reading_issues": run.evidence_errors,
                    "issues_to_resolve": [
                        {"subject_ids": f.subject_ids, "explanation": f.explanation, "remedy": f.remedy}
                        for f in run.findings
                        if f.kind == "check" and f.status in {"fail", "unknown"}
                    ],
                    "correction_instructions": instructions,
                    "additional_document_round_remaining": attempt == 0,
                },
                max_output=1600,
            )
            if not result.document_requests or attempt:
                break
            yield from self._fetch_requests(run, budget, result.document_requests)
            if document_ids is not None:
                requested_owners = {request.component_id for request in result.document_requests}
                document_ids = document_ids | {
                    key for c in run.components if c.id in requested_owners for key in c.document_ids
                }
        requested = list(result.selections)
        if document_ids is not None and any(s.document_id not in current_documents for s in requested):
            raise DocumentError("Reading plan selected a document outside the requested source scope")
        requested.extend(
            PageSelection(
                document_id=d["document_id"],
                pages=list(range(1, d["page_count"] + 1)),
                reason="Complete short manufacturer source",
            )
            for d in run.documents
            if d["document_id"] in current_documents
            and 0 < d["page_count"] <= 3
            and (
                not set(range(1, d["page_count"] + 1)) <= set(d.get("pages_interpreted", []))
                or any(
                    c.product
                    and d["document_id"] in c.document_ids
                    and not any(e.document_id == d["document_id"] and c.id in e.component_ids for e in run.evidence)
                    for c in run.components
                )
            )
        )
        selections = merge_page_selections(requested)
        if sum(len(selection.pages) for selection in selections) > 24:
            raise BudgetExceeded("Initial reading plan exceeds 24 pages")
        return selections

    def _filter_evidence(self, run, items, component_ids, document_id=None):
        metadata = {d["document_id"]: d for d in run.documents}
        verified, issues = [], []
        for evidence in items:
            document = metadata.get(evidence.document_id)
            valid = (
                document
                and evidence.page in document.get("pages_read", [])
                and bool(evidence.fact.strip())
                and bool(evidence.quote.strip())
            )
            valid = valid and (document_id is None or evidence.document_id == document_id)
            valid = valid and bool(evidence.component_ids) and set(evidence.component_ids) <= component_ids
            if valid and evidence.kind == "text":
                valid = self.documents.quote_matches(evidence.document_id, evidence.page, evidence.quote)
            if valid and evidence.kind == "figure":
                valid = document["media_type"] == "application/pdf" and self.gateway.pdf_supported
            if valid:
                verified.append(evidence)
            else:
                issues.append(
                    Finding(
                        id=f"invalid:{evidence.id}",
                        revision=run.revision,
                        area="evidence",
                        method="code",
                        kind="guidance",
                        status="unknown",
                        subject_ids=evidence.component_ids,
                        document_id=document_id or evidence.document_id,
                        explanation=f"Evidence {evidence.id} did not match {evidence.document_id} page {evidence.page}. Proposed quote: {evidence.quote!r}. Fact: {evidence.fact}",
                        remedy="Observation discarded. Read the correct source only if this fact is needed for a BOM compatibility claim.",
                    )
                )
        return verified, issues

    def _apply_configuration(self, run, proposal):
        self._assert_unique_ids(proposal.additional_components, "additional component")
        known = {c.id for c in run.components}
        for spec in proposal.additional_components:
            if spec.id not in known:
                run.components.append(Component(**spec.model_dump()))
                known.add(spec.id)
        if len(run.components) > run.limits.bom_rows:
            raise BudgetExceeded("Design exceeds the supported BOM size")
        for field in (
            "rails",
            "interfaces",
            "signal_checks",
            "regulator_checks",
            "assumptions",
            "configuration_notes",
        ):
            setattr(run, field, getattr(proposal, field))
        run.invalidate_review()

    def _extract_evidence(self, run, budget, selections, instructions):
        """Only source extraction writes observations; configuration references them."""
        # Packet replacement reassigns source-number IDs; prior operands must not rebind.
        if selections:
            run.invalidate_configuration()
        else:
            run.invalidate_review()
        selected = {c.id: c for c in run.components if c.product}

        def current_ids(document_id, identifiers):
            return [
                key
                for key in identifiers
                if key in selected
                and (
                    document_id is None or selected[key].kind == "passive" or document_id in selected[key].document_ids
                )
            ]

        # A replacement must not inherit the old variant's facts. Shared documents
        # still support unchanged placements, and unvisited sources retain their gaps.
        run.evidence = [
            item.model_copy(update={"component_ids": owners})
            for item in run.evidence
            if (owners := current_ids(item.document_id, item.component_ids))
        ]
        run.evidence_errors = [
            item.model_copy(update={"subject_ids": owners})
            for item in run.evidence_errors
            if (owners := current_ids(item.document_id, item.subject_ids))
        ]
        document_numbers = {d["document_id"]: index for index, d in enumerate(run.documents, 1)}
        for selection in selections:
            index = document_numbers[selection.document_id]
            owners = [c for c in run.components if c.product and selection.document_id in c.document_ids]
            if not owners:
                continue
            blocks, page_count = self._build_source_blocks(run, [selection])
            page_type = Literal[tuple(sorted(set(selection.pages)))]
            observation = create_model(
                "SourceObservation",
                __base__=Evidence,
                document_id=(SkipJsonSchema[Literal[selection.document_id]], selection.document_id),
                page=(
                    page_type,
                    Field(description="Original physical page, from the attached file name and text label"),
                ),
            )
            packet_schema = create_model("SourcePacket", __base__=EvidencePacket, evidence=(list[observation], ...))
            packet = yield from self.gateway.call(
                budget,
                f"interpret {','.join(c.id for c in owners)}",
                packet_schema,
                EXTRACT,
                {
                    "components": [
                        {
                            "id": c.id,
                            "manufacturer": c.product.manufacturer,
                            "mpn": c.product.mpn,
                            "package": c.product.package,
                            "purpose": c.purpose,
                        }
                        for c in owners
                    ],
                    "needed_facts": selection.reason,
                    "correction_instructions": instructions,
                    "device_request": run.original_request,
                    "latest_modification": run.modification,
                    "operating_assumptions": run.assumptions,
                    "previous_observations": [e for e in run.evidence if e.document_id == selection.document_id],
                    "id_prefix": f"D{index}E",
                    "original_physical_pages": selection.pages,
                },
                blocks,
                max_output=5500,
                pdf_pages=page_count,
            )
            self._mark_pages_read(run, [selection])
            for index_in_packet, item in enumerate(packet.evidence, 1):
                item.id = f"D{index}E{index_in_packet}"
                for number, operand in enumerate(item.numbers, 1):
                    operand.id = f"{item.id}N{number}"
            owner_ids = {c.id for c in owners}
            applicable = {
                key for key, match in packet.applicability.items() if match.applies and match.reason.strip()
            } & owner_ids
            valid, rejected = self._filter_evidence(run, packet.evidence, applicable, selection.document_id)
            metadata = next(d for d in run.documents if d["document_id"] == selection.document_id)
            metadata["applicability"] = {
                key: match.reason for key, match in packet.applicability.items() if key in owner_ids
            }
            errors = [error for error in run.evidence_errors if error.document_id != selection.document_id]
            errors.extend(rejected)
            errors.extend(
                Finding(
                    id=f"source_gap:D{index}:{number}",
                    revision=run.revision,
                    area="evidence",
                    method="code",
                    kind="guidance",
                    status="unknown",
                    subject_ids=[c.id for c in owners],
                    document_id=selection.document_id,
                    explanation=f"Not established by this source: {missing}",
                    remedy="Reviewer must determine whether other evidence/configuration resolves this reading gap",
                )
                for number, missing in enumerate(packet.missing_facts, 1)
            )
            run.evidence = [e for e in run.evidence if e.document_id != selection.document_id] + valid
            metadata["pages_interpreted"] = sorted(set(selection.pages))
            run.evidence_errors = errors
            yield self._snapshot(run)

    def _configure_bom(self, run, budget, instructions=""):
        run.stage = "evidence"
        proposal = yield from self.gateway.call(
            budget,
            "configure operating compatibility",
            OperatingConfiguration,
            CONFIGURE,
            {"design": design_context(run), "correction_instructions": instructions},
            max_output=7000,
        )
        known = {c.id for c in run.components}
        self._apply_configuration(run, proposal)
        # Existing selection failures await an explicit correction, not another configuration pass.
        added = {c.id for c in run.components} - known
        yield from self._select_components(run, budget, component_ids=added)
        run.stage = "evidence"
        yield self._snapshot(run)
        return added

    def _source_and_configure(self, run, budget, instructions="", source_component_ids=None):
        run.stage = "evidence"
        # Repeat only when configuration adds a functional component needing its own source.
        selections = [
            PageSelection(
                document_id=key,
                pages=sorted({e.page for e in run.evidence if e.document_id == key}),
                reason="Retained source observations",
            )
            for key in sorted({e.document_id for e in run.evidence})
        ]
        inspected_parts = {
            c.id for c in run.components if source_component_ids is not None and c.id not in source_component_ids
        }
        for dependency_pass in range(3):
            yield from self._fetch_documents(run, budget, source_component_ids or ())
            if not dependency_pass:
                new_documents = (
                    None
                    if source_component_ids is None
                    else {key for c in run.components if c.id in source_component_ids for key in c.document_ids}
                )
            else:
                new_documents = {key for c in run.components if c.id not in inspected_parts for key in c.document_ids}
            missing_source = any(
                c.product
                and c.id not in inspected_parts
                and not c.document_ids
                and (c.kind != "passive" or c.id in (source_component_ids or ()))
                for c in run.components
            )
            reading = []
            if missing_source or (run.documents and new_documents != set()):
                reading = yield from self._plan_source_reads(run, budget, instructions, new_documents)
            # A shared family source is replaced as one packet; keep the pages
            # supporting its already selected owners when adding another owner.
            for selection in reading:
                earlier = [e.page for e in run.evidence if e.document_id == selection.document_id]
                earlier.extend(
                    page for old in selections if old.document_id == selection.document_id for page in old.pages
                )
                selection.pages = sorted(set(selection.pages + earlier))
            yield from self._extract_evidence(run, budget, reading, instructions)
            read_documents = {selection.document_id for selection in reading}
            inspected_parts.update(c.id for c in run.components if c.product and set(c.document_ids) & read_documents)
            selections = merge_page_selections([*selections, *reading])
            yield from self._configure_bom(run, budget, instructions)
            unread = [
                c
                for c in run.components
                if c.product and c.kind != "passive" and not c.document_ids and not c.document_errors
            ]
            if not unread:
                return selections
        return selections

    def _review_bom(self, run, budget, selections, prior_requirements=None):
        run.stage = "review"
        run.invalidate_review()
        refresh_checks(run)
        observations = [
            PageSelection(document_id=evidence.document_id, pages=[evidence.page], reason="Current evidence")
            for evidence in run.evidence
        ]
        selections = merge_page_selections([*selections, *observations])
        for extra_round in range(2):
            blocks, count = self._build_source_blocks(run, selections, include_pdf_text=False)
            inventory = self._build_source_inventories(run, max_chars=3000)
            review = yield from review_bom(self.gateway, budget, run, blocks, count, inventory, prior_requirements)
            self._mark_pages_read(run, selections)
            if (review.additional_pages or review.document_requests) and extra_round == 0:
                if review.document_requests:
                    yield from self._fetch_requests(run, budget, review.document_requests)
                    discovered = yield from self._plan_source_reads(run, budget)
                    selections = selections + discovered
                selections = merge_page_selections([*selections, *review.additional_pages])
                continue
            number_refs = {number.id: item.id for item in run.evidence for number in item.numbers}
            for finding in review.findings:
                finding.revision = run.revision
                finding.method = "model_review"
                # Numerical observations cite their parent evidence; invalid references remain visible.
                finding.evidence_ids = list(
                    dict.fromkeys(number_refs.get(key, key) for key in finding.evidence_ids)
                )
            run.findings = review.findings
            # Exhausting source follow-up does not erase a performed review.
            run.review_completed = True
            break
        yield self._snapshot(run)
        return selections

    def _apply_correction(self, run, correction):
        if correction.configuration is not None and any(c.product is None for c in run.components):
            raise ValueError("Direct configuration requires every component to be selected")
        by_id = {c.id: c for c in run.components}
        for identifier in correction.remove_component_ids:
            by_id.pop(identifier, None)
        for spec in correction.replace_components:
            if spec.id not in by_id:
                raise ValueError("Correction tried to replace an unknown placement")
            by_id[spec.id] = Component(**spec.model_dump())
        for spec in correction.add_components:
            if spec.id in by_id:
                raise ValueError("Correction reused an existing placement ID")
            by_id[spec.id] = Component(**spec.model_dump())
        requirements = {requirement.id: requirement for requirement in run.requirements}
        for identifier, component_ids in correction.requirement_components.items():
            if identifier not in requirements or not set(component_ids) <= by_id.keys():
                raise ValueError("Requirement mapping must name an existing requirement and current component IDs")
        if not set(correction.reread_component_ids) <= by_id.keys():
            raise ValueError("Source reread must name current component IDs")
        components = list(by_id.values())
        changed = (
            run.components != components
            or any(requirements[key].component_ids != ids for key, ids in correction.requirement_components.items())
            or bool(correction.configuration_instructions.strip())
            or bool(correction.reread_component_ids)
            or correction.configuration is not None
        )
        removed = set(correction.remove_component_ids) & {c.id for c in run.components}
        run.components = components
        self._invalidate_parts(run, removed | {spec.id for spec in correction.replace_components})
        for identifier, component_ids in correction.requirement_components.items():
            requirements[identifier].component_ids = list(component_ids)
        if changed:
            run.revision += 1
            run.invalidate_review()
        if correction.configuration is not None:
            self._apply_configuration(run, correction.configuration)
        return changed

    def _refresh_offers(self, run, budget):
        """Refresh inherited prices before planning or reviewing price constraints."""
        cache = {}
        for component in run.components:
            product = component.product
            if not product:
                continue
            try:
                retrieved_at = datetime.fromisoformat(product.retrieved_at)
                age = (
                    (datetime.now(timezone.utc) - retrieved_at).total_seconds()
                    if retrieved_at.tzinfo is not None
                    else float("inf")
                )
            except ValueError:
                age = float("inf")
            if age + budget.remaining() <= 900:
                continue
            key = (product.manufacturer, product.mpn)
            try:
                if key not in cache:
                    yield {"type": "progress", "stage": "sourcing", "message": f"Refreshing offer for {product.mpn}"}
                    budget.consume(supplier_calls=1)
                    refreshed = Product.model_validate(
                        self.supplier.get_product(
                            product.offers[0].sku if product.offers else product.mpn,
                            region=run.options.region,
                            currency=run.options.currency,
                            timeout=min(20, budget.remaining()),
                        )
                    )
                    if (refreshed.manufacturer, refreshed.mpn) != key:
                        raise SupplierError("Refreshed offer identity differs")
                    cache[key] = refreshed
                product.offers, product.retrieved_at = cache[key].offers, cache[key].retrieved_at
            except (SupplierError, ValueError):
                product.offers = []

    def _apply_plan(self, run, plan):
        self._assert_unique_ids(plan.components, "component")
        self._assert_unique_ids(plan.requirements, "requirement")
        if sum(c.kind != "passive" and not c.support_for for c in plan.components) > run.limits.functional_blocks:
            raise BudgetExceeded("Request exceeds the initial functional-block scope")
        if len(plan.components) > run.limits.bom_rows:
            raise BudgetExceeded("Request exceeds the supported BOM size")
        old = {c.id: c for c in run.components}
        changed_ids = set(old) - {spec.id for spec in plan.components}
        run.components = []
        for spec in plan.components:
            retained = old.get(spec.id)
            if retained and (retained.search_query, retained.purpose) == (spec.search_query, spec.purpose):
                component = retained.model_copy(update=spec.model_dump())
            else:
                component = Component(**spec.model_dump())
                changed_ids.add(spec.id)
            run.components.append(component)
        self._invalidate_parts(run, changed_ids)
        run.summary, run.requirements, run.assumptions = plan.summary, plan.requirements, plan.assumptions
        run.configuration_notes, run.pending_questions = plan.configuration_notes, plan.pending_questions
        run.invalidate_review()

    def _complete_correction(self, run, budget, correction, selections):
        """Reread only when parts or material evidence changed; otherwise reuse sources."""
        parts_changed = bool(
            correction.replace_components or correction.add_components or correction.remove_component_ids
        )
        instructions = correction.configuration_instructions
        if parts_changed or correction.reread_component_ids:
            return (
                yield from self._source_and_configure(
                    run,
                    budget,
                    instructions,
                    source_component_ids=None if parts_changed else set(correction.reread_component_ids),
                )
            )
        if instructions.strip():
            added = yield from self._configure_bom(run, budget, instructions)
            if any(
                c.id in added and c.product and c.kind != "passive"
                for c in run.components
            ):
                return (yield from self._source_and_configure(run, budget, instructions))
        return selections

    def execute(self, run: DesignRun):
        run.numeric_binding_version = 1
        # New runs use source evidence and notes rather than support inventories.
        run.source_support_needs = []
        run.support_needs = []
        budget = Budget(run)
        prior_requirements = [requirement.model_dump() for requirement in run.requirements] if run.parent_run_id else []
        try:
            run.model = getattr(getattr(self.gateway, "model", None), "model", None) or os.getenv(
                "MODEL", "gemini-3.5-flash-lite"
            )
            run.model_configuration = {
                "provider": os.getenv("MODEL_PROVIDER", "google_genai"),
                "thinking_level": os.getenv("MODEL_THINKING_LEVEL", "provider_default"),
            }
            if run.parent_run_id:
                yield from self._refresh_offers(run, budget)
            run.stage = "plan"
            plan = yield from plan_requirements(self.gateway, budget, run)
            self._apply_plan(run, plan)
            yield self._snapshot(run)
            if run.pending_questions:
                run.lifecycle, run.terminal_reason = "needs_input", "A material requirement needs clarification"
                return
            if not run.components or not run.requirements:
                run.terminal_reason = "No supported device requirements or component plan"
                return
            yield from self._select_components(run, budget)
            selections = yield from self._source_and_configure(run, budget)
            last_correction = None
            while True:
                yield self._snapshot(run)
                selections = yield from self._review_bom(run, budget, selections, prior_requirements)
                if run.compatibility != "issues_found":
                    break
                if run.usage.correction_rounds >= run.limits.correction_rounds:
                    break
                correction_schema = Correction
                if any(component.product is None for component in run.components):
                    correction_schema = create_model(
                        "SelectionCorrection",
                        __base__=Correction,
                        configuration=(
                            type(None),
                            Field(
                                default=None,
                                description=(
                                    "Must be null while any placement is unselected. Repair missing selections "
                                    "through the existing part changes and configuration_instructions."
                                ),
                            ),
                        ),
                    )
                correction = yield from self.gateway.call(
                    budget, "correct", correction_schema, CORRECT, {"design": design_context(run)}, max_output=7000
                )
                yield {
                    "type": "progress",
                    "stage": "correct",
                    "message": correction.reason,
                    "correction": correction.model_dump(mode="json"),
                }
                signature = correction.model_dump_json(exclude={"reason"})
                if signature == last_correction or not self._apply_correction(run, correction):
                    run.terminal_reason = "No further supported correction was found"
                    break
                last_correction = signature
                budget.consume(correction_rounds=1)
                yield self._snapshot(run)
                yield from self._select_components(run, budget)
                if correction.configuration is not None:
                    continue
                selections = yield from self._complete_correction(run, budget, correction, selections)
            # New and refreshed offers remain within the 15-minute policy during an eight-minute run.
            if not run.terminal_reason:
                run.terminal_reason = {
                    "checked": "Checks passed",
                    "issues_found": "Checks failed; correction allowance reached",
                    None: "No review findings were returned",
                }[run.compatibility]
        except BudgetExceeded as error:
            run.terminal_reason = str(error)
        except GeneratorExit:
            run.lifecycle, run.terminal_reason = "interrupted", "Client disconnected; no further operations started"
            run.review_completed = False
            raise
        except Exception as error:
            run.lifecycle = "error"
            run.terminal_reason = f"{type(error).__name__}: {str(error)[:500]}"
        finally:
            if run.lifecycle == "running":
                run.lifecycle = "finished"
            budget.run.usage.elapsed_seconds = round(time.monotonic() - budget.started, 2)
            run.updated_at = now()
            refresh_checks(run)
        yield {
            "type": "error" if run.lifecycle == "error" else "complete",
            "stage": "complete",
            "message": run.terminal_reason,
        }
