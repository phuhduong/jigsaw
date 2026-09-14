import { Package, Download, ExternalLink } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { exportUrl, safeUrl } from "../services/api/designRunApi";
import type { DesignSnapshot } from "../services/api/designRunApi";

export default function PartsList({ snapshot }: { snapshot: DesignSnapshot | null }) {
  const rows = snapshot?.bom ?? [];
  const totals = new Map<string, number>();
  for (const row of rows) {
    if (row.extended_price !== null) totals.set(row.currency, (totals.get(row.currency) ?? 0) + row.extended_price);
  }
  const unpriced = rows.filter(row => row.extended_price === null).length;
  const unresolved = snapshot?.components.filter(component => !component.product).length ?? 0;
  return (
    <section className="h-full flex flex-col">
      <div className="p-6 border-b border-zinc-800">
        <h2 className="text-lg flex items-center gap-2"><Package className="w-5 h-5 text-emerald-400" /> Bill of materials</h2>
        <p className="text-sm text-zinc-400 mt-2">{snapshot?.lifecycle === "running" ? "Provisional selections · review in progress" : "Parts, quantities, and purchasing links"}</p>
        {snapshot && <p className="text-xs text-zinc-500 mt-2">Sourcing: {snapshot.sourcing}</p>}
      </div>
      <div className="flex-1 p-6 space-y-4">
        {rows.length === 0 && <p className="text-sm text-zinc-500 py-8 text-center">No parts selected yet.</p>}
        {rows.map(row => (
          <Card key={`${row.manufacturer}:${row.mpn}:${row.package}`} className="bg-zinc-900/50 border-zinc-800 p-4">
            <div className="flex justify-between gap-3">
              <div className="min-w-0"><h3 className="font-medium break-words">{row.mpn}</h3><p className="text-xs text-zinc-500 mt-1">{row.manufacturer}</p></div>
              <div className="text-sm text-emerald-400 whitespace-nowrap">{row.unit_price === null ? "Price unknown" : `${row.currency} ${row.unit_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`}</div>
            </div>
            <p className="text-xs text-zinc-400 mt-3">{row.reference_ids.join(", ")} · {row.package || "Package not specified"}</p>
            <p className="text-sm text-zinc-400 mt-2">{[...new Set(row.purposes)].join("; ")}</p>
            <p className="text-xs text-zinc-500 mt-3">{row.installed_quantity} per board · {row.board_quantity} board(s) · order {row.order_quantity}</p>
            <p className={`text-xs mt-2 ${row.availability === "available" ? "text-emerald-400" : "text-amber-400"}`}>{row.availability.replaceAll("_", " ")}</p>
            {row.ordering_note && <p className="text-xs text-zinc-500 mt-2">{row.ordering_note}</p>}
            <div className="flex gap-4 mt-4 pt-3 border-t border-zinc-800 text-xs text-emerald-400">
              {safeUrl(row.purchase_url) && <a href={safeUrl(row.purchase_url)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1"><ExternalLink className="w-3 h-3" /> Buy part</a>}
              {safeUrl(row.datasheet_url) && <a href={safeUrl(row.datasheet_url)} target="_blank" rel="noopener noreferrer">Datasheet</a>}
            </div>
          </Card>
        ))}
        {unresolved > 0 && <p className="text-sm text-amber-400">{unresolved} required selection(s) remain unresolved.</p>}
      </div>
      {snapshot && <div className="p-6 border-t border-zinc-800 space-y-3">
        {rows.length > 0 && <>
          <p className="text-sm text-zinc-400">{unpriced || unresolved ? "Known-price subtotal" : "Parts subtotal"}</p>
          {[...totals].map(([currency, total]) => <p key={currency} className="text-xl text-emerald-400">{currency} {total.toFixed(2)}</p>)}
          {unpriced > 0 && <p className="text-xs text-amber-400">{unpriced} row(s) have unknown pricing.</p>}
          <p className="text-xs text-zinc-500">Shipping and tax excluded. Stock and prices may change.</p>
        </>}
        <div className="flex gap-2">
          <Button asChild className="bg-emerald-600 hover:bg-emerald-500 text-white"><a href={exportUrl(snapshot.id, "csv")}><Download className="w-4 h-4" /> CSV</a></Button>
          <Button asChild variant="outline" className="border-zinc-700"><a href={exportUrl(snapshot.id, "json")}>Full JSON report</a></Button>
        </div>
        <p className="text-xs text-zinc-500">Exports retain the saved review status. The JSON report includes unresolved issues.</p>
      </div>}
    </section>
  );
}
