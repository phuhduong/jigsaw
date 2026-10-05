"""Atomic local run snapshots and BOM projections; no separate purchasing state."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from models import DesignRun, Product, now

_RUN_ID = re.compile(r"^[a-f0-9]{32}$")


class RunStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else Path(__file__).parent / "data" / "runs"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        if not _RUN_ID.fullmatch(run_id):
            raise ValueError("Invalid run ID")
        return self.root / f"{run_id}.json"

    def save(self, run: DesignRun) -> None:
        destination = self._path(run.id)
        run.updated_at = now()
        data = DesignRun.model_validate(run.model_dump()).model_dump_json(indent=2)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.root, prefix=f".{run.id}-", suffix=".tmp", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def load(self, run_id: str) -> DesignRun:
        run = DesignRun.model_validate_json(self._path(run_id).read_text(encoding="utf-8"))
        if run.id != run_id or run.schema_version != 1:
            raise ValueError("Unsupported or mismatched saved run")
        return run

    def interrupt_unfinished(self) -> int:
        count = 0
        for path in self.root.glob("*.json"):
            try:
                run = self.load(path.stem)
                if run.lifecycle == "running":
                    run.lifecycle = "interrupted"
                    run.compatibility = (
                        "issues_found"
                        if any(
                            f.revision == run.revision and f.blocks_review
                            for f in run.findings
                        )
                        else None
                    )
                    run.review_completed = False
                    run.terminal_reason = "The backend restarted before this run finished."
                    self.save(run)
                    count += 1
            except (ValueError, OSError):
                logging.getLogger(__name__).exception("Could not inspect saved run %s", path.name)
        return count


def _http_url(value: str | None) -> str | None:
    try:
        parsed = urlparse(value or "")
    except ValueError:
        return None
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _is_custom_reel(offer) -> bool:
    return bool(offer and "digi-reel" in (offer.packaging or "").casefold())


def _order_quantity(required, moq, multiple):
    quantity = max(required, moq or 1)
    if multiple:
        quantity = (quantity + multiple - 1) // multiple * multiple
    return quantity


def bom_rows(run: DesignRun) -> list[dict]:
    groups = {}
    for component in run.components:
        if component.product is None or not component.product.mpn.strip() or not component.product.manufacturer.strip():
            continue
        product = component.product
        key = (product.manufacturer.strip().casefold(), product.mpn.strip().casefold(), product.package or "")
        groups.setdefault(key, []).append(component)
    rows = []
    for placements in groups.values():
        product = placements[0].product
        demand = len(placements) * run.options.board_quantity
        offers = {
            offer.sku: offer
            for placement in placements
            for offer in placement.product.offers
            if offer.region == run.options.region and offer.currency == run.options.currency
        }
        options = []
        for offer in offers.values():
            quantity = _order_quantity(demand, offer.moq, offer.order_multiple)
            tiers = [tier for tier in offer.price_breaks if tier.quantity <= quantity]
            price = max(tiers, key=lambda tier: tier.quantity).unit_price if tiers else None
            url = _http_url(offer.url) or _http_url(product.product_url)
            available = bool(url and price is not None and offer.stock is not None and offer.stock >= quantity)
            options.append(
                {
                    "available": available,
                    "total": price * quantity if price is not None else float("inf"),
                    "offer": offer,
                    "quantity": quantity,
                    "price": price,
                    "url": url,
                }
            )
        # Custom reeling may add an unquoted setup fee. Ordinary Tape & Reel is
        # not custom reeling; retain the existing total-price ranking otherwise.
        offer, quantity, price, url = None, demand, None, _http_url(product.product_url)
        availability = "unknown"
        if options:
            chosen = min(
                options,
                key=lambda choice: (
                    not choice["available"],
                    choice["available"] and _is_custom_reel(choice["offer"]),
                    choice["total"],
                    choice["offer"].sku,
                ),
            )
            offer = chosen["offer"]
            quantity, price, url = chosen["quantity"], chosen["price"], chosen["url"]
            if chosen["available"]:
                availability = "available"
            elif offer.stock is not None and offer.stock < quantity:
                availability = "out_of_stock"
        notes = (
            ["Order multiple not provided; confirm at checkout."] if not offer or offer.order_multiple is None else []
        )
        if _is_custom_reel(offer):
            notes.append("Quoted component prices exclude any custom-reeling/setup fee; confirm the total at checkout.")
        rows.append(
            {
                "reference_ids": [component.id for component in placements],
                "purposes": [component.purpose for component in placements],
                "manufacturer": product.manufacturer,
                "mpn": product.mpn,
                "package": product.package,
                "installed_quantity": len(placements),
                "board_quantity": run.options.board_quantity,
                "required_quantity": demand,
                "order_quantity": quantity,
                "unit_price": price,
                "extended_price": round(price * quantity, 6) if price is not None else None,
                "currency": run.options.currency,
                "supplier_sku": offer.sku if offer else None,
                "purchase_url": url,
                "datasheet_url": _http_url(product.datasheet_url),
                "stock": offer.stock if offer else None,
                "moq": offer.moq if offer else None,
                "order_multiple": offer.order_multiple if offer else None,
                "ordering_note": " ".join(notes),
                "retrieved_at": offer.retrieved_at if offer else product.retrieved_at,
                "availability": availability,
                "review_status": run.compatibility,
            }
        )
    return rows


def run_snapshot(run: DesignRun) -> dict:
    return {**run.model_dump(mode="json"), "bom": bom_rows(run)}


def export_json(run: DesignRun) -> str:
    return json.dumps(run_snapshot(run), indent=2, ensure_ascii=False)


def export_csv(run: DesignRun) -> str:
    columns = [
        "reference_ids",
        "purposes",
        "manufacturer",
        "mpn",
        "package",
        "installed_quantity",
        "board_quantity",
        "required_quantity",
        "order_quantity",
        "unit_price",
        "extended_price",
        "currency",
        "supplier_sku",
        "purchase_url",
        "datasheet_url",
        "stock",
        "moq",
        "order_multiple",
        "ordering_note",
        "retrieved_at",
        "availability",
        "review_status",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in bom_rows(run):
        escaped = {}
        for key, value in row.items():
            if isinstance(value, list):
                value = "; ".join(value)
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            escaped[key] = value
        writer.writerow(escaped)
    return output.getvalue()


def product_context(product, quantity=1):
    """Keep catalog engineering fields, not every packaging price tier, in model prompts."""
    if isinstance(product, Product):
        product = product.model_dump()
    result = {
        k: product.get(k)
        for k in (
            "manufacturer",
            "mpn",
            "package",
            "description",
            "parameters",
            "datasheet_url",
            "product_url",
            "retrieved_at",
        )
    }
    result["parameters"] = [
        item
        for item in result.get("parameters") or []
        if item.get("value") is not None and str(item["value"]).strip().lower() not in {"", "-", "n/a"}
    ]
    result["offers"] = []
    for offer in product.get("offers", []):
        order = _order_quantity(quantity, offer.get("moq"), offer.get("order_multiple"))
        tiers = [p for p in offer.get("price_breaks", []) if p["quantity"] <= order]
        price = max(tiers, key=lambda p: p["quantity"])["unit_price"] if tiers else None
        result["offers"].append(
            {
                "sku": offer["sku"],
                "stock": offer.get("stock"),
                "moq": offer.get("moq"),
                "order_multiple": offer.get("order_multiple"),
                "currency": offer.get("currency"),
                "packaging": offer.get("packaging"),
                "order_quantity": order,
                "unit_price": price,
                "extended_price": round(price * order, 6) if price is not None else None,
            }
        )
    return result


def design_context(run):
    """A projection for reasoning, never another authoritative design state."""
    result = run.model_dump(
        include={
            "original_request",
            "modification",
            "revision",
            "summary",
            "requirements",
            "assumptions",
            "components",
            "evidence",
            "evidence_errors",
            "rails",
            "interfaces",
            "signal_checks",
            "regulator_checks",
            "configuration_notes",
            "findings",
            "pending_questions",
        }
    )
    # Successful checks repeat facts already present below. Keep actionable gaps
    # in reasoning context; the full saved report still retains every finding.
    result["findings"] = [
        finding
        for finding in result["findings"]
        if finding["revision"] == run.revision
        and finding["kind"] == "check"
        and finding["status"] in {"fail", "unknown"}
    ]
    for component in result["components"]:
        component.pop("selection_reason", None)
        for key in ("selection_error", "document_errors"):
            if not component.get(key):
                component.pop(key, None)
        if component["product"]:
            component["product"] = product_context(component["product"], run.options.board_quantity)
            # Selected-offer totals already appear in purchasing_bom. Candidate
            # selection still receives offers through product_context directly.
            component["product"].pop("offers", None)
            component["product"].pop("retrieved_at", None)
    result["purchasing_options"] = run.options.model_dump()
    result["purchasing_bom"] = [
        {
            key: row[key]
            for key in (
                "reference_ids",
                "required_quantity",
                "order_quantity",
                "unit_price",
                "extended_price",
                "currency",
                "availability",
            )
        }
        for row in bom_rows(run)
    ]
    return result
