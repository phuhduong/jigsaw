"""Atomic local run snapshots and BOM projections; no separate purchasing state."""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from models import DesignRun, now

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
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root,
                                             prefix=f".{run.id}-", suffix=".tmp", delete=False) as handle:
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
                    run.compatibility = "issues_found" if any(
                        f.revision == run.revision and f.kind == "check" and f.status == "fail"
                        for f in run.findings) else "incomplete"
                    run.review_completed = False
                    run.terminal_reason = "The backend restarted before this run finished."
                    self.save(run)
                    count += 1
            except (ValueError, OSError):
                logging.getLogger(__name__).exception("Could not inspect saved run %s", path.name)
        return count


def _url(value: str | None) -> str | None:
    parsed = urlparse(value or "")
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _custom_reel(offer) -> bool:
    return bool(offer and "digi-reel" in (offer.packaging or "").casefold())


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
        offers = {offer.sku: offer for placement in placements for offer in placement.product.offers
                  if offer.region == run.options.region and offer.currency == run.options.currency}
        options = []
        for offer in offers.values():
            quantity = max(demand, offer.moq or 1)
            if offer.order_multiple is not None:
                quantity = math.ceil(quantity / offer.order_multiple) * offer.order_multiple
            tiers = [tier for tier in offer.price_breaks if tier.quantity <= quantity]
            price = max(tiers, key=lambda tier: tier.quantity).unit_price if tiers else None
            url = _url(offer.url) or _url(product.product_url)
            available = bool(url and price is not None and offer.stock is not None and offer.stock >= quantity)
            options.append((available, price * quantity if price is not None else float("inf"), offer, quantity, price, url))
        # Custom reeling may add an unquoted setup fee. Ordinary Tape & Reel is
        # not custom reeling; retain the existing total-price ranking otherwise.
        chosen = min(options, key=lambda item: (not item[0], item[0] and _custom_reel(item[2]), item[1], item[2].sku)) if options else None
        offer, quantity, price, url = chosen[2:] if chosen else (None, demand, None, _url(product.product_url))
        availability = "available" if chosen and chosen[0] else "out_of_stock" if offer and offer.stock is not None and offer.stock < quantity else "unknown"
        notes = ["Order multiple not provided; confirm at checkout."] if not offer or offer.order_multiple is None else []
        if _custom_reel(offer):
            notes.append("Quoted component prices exclude any custom-reeling/setup fee; confirm the total at checkout.")
        rows.append({
            "reference_ids": [component.id for component in placements],
            "purposes": [component.purpose for component in placements],
            "manufacturer": product.manufacturer, "mpn": product.mpn, "package": product.package,
            "installed_quantity": len(placements), "board_quantity": run.options.board_quantity,
            "required_quantity": demand, "order_quantity": quantity,
            "unit_price": price, "extended_price": round(price * quantity, 6) if price is not None else None,
            "currency": run.options.currency, "supplier_sku": offer.sku if offer else None,
            "purchase_url": url, "datasheet_url": _url(product.datasheet_url),
            "stock": offer.stock if offer else None, "moq": offer.moq if offer else None,
            "order_multiple": offer.order_multiple if offer else None,
            "ordering_note": " ".join(notes),
            "retrieved_at": offer.retrieved_at if offer else product.retrieved_at,
            "availability": availability, "review_status": run.compatibility,
        })
    return rows


def export_json(run: DesignRun) -> str:
    return json.dumps({**run.model_dump(mode="json"), "bom": bom_rows(run)}, indent=2, ensure_ascii=False)


def export_csv(run: DesignRun) -> str:
    columns = ["reference_ids", "purposes", "manufacturer", "mpn", "package", "installed_quantity",
               "board_quantity", "required_quantity", "order_quantity", "unit_price", "extended_price",
               "currency", "supplier_sku", "purchase_url", "datasheet_url", "stock", "moq",
               "order_multiple", "ordering_note", "retrieved_at", "availability", "review_status"]
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
