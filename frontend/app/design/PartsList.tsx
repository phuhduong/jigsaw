import { ArrowUpRight, CircleAlert } from "lucide-react";
import { getSafeUrl, type DesignSnapshot } from "../services/api/designRunApi";
import { getComponentRole, getComponentTitle } from "./componentPresentation";
import PartIllustration from "./PartIllustration";
import {
  formatMoney,
  getCompatibilityFailures,
  getSubjectComponentIds,
  isSelectedProduct,
} from "./reportHelpers";
import "./report.css";

export default function PartsList({
  snapshot,
  onSelect,
  selectedId,
}: {
  snapshot: DesignSnapshot;
  onSelect: (id: string) => void;
  selectedId?: string | null;
}) {
  const totalsByCurrency = new Map<string, number>();
  for (const row of snapshot.bom) {
    if (row.extended_price !== null)
      totalsByCurrency.set(
        row.currency,
        (totalsByCurrency.get(row.currency) ?? 0) + row.extended_price,
      );
  }
  const hasUnpricedRows = snapshot.bom.some(
    (row) => row.extended_price === null,
  );
  const unselectedComponents = snapshot.components.filter(
    (component) => !isSelectedProduct(component.product),
  );
  const isRunning = snapshot.lifecycle === "running";
  const failedComponentIds = new Set(
    getCompatibilityFailures(snapshot).flatMap((finding) =>
      finding.subject_ids.flatMap((id) => getSubjectComponentIds(snapshot, id)),
    ),
  );
  return (
    <section className="parts-panel" aria-label="Parts list">
      {snapshot.options.board_quantity > 1 && (
        <p className="bom-build-quantity">
          For {snapshot.options.board_quantity.toLocaleString()} boards
        </p>
      )}
      {snapshot.bom.length > 0 || unselectedComponents.length > 0 ? (
        <div
          className="bom-table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Parts table"
        >
          <table className="bom-table" role="table">
            <caption className="sr-only">
              Parts for {snapshot.options.board_quantity}{" "}
              {snapshot.options.board_quantity === 1 ? "board" : "boards"}.
              Prices cover the order quantity.
            </caption>
            <thead role="rowgroup">
              <tr role="row">
                <th scope="col" role="columnheader">
                  Part
                </th>
                <th scope="col" role="columnheader">
                  Qty
                </th>
                <th scope="col" role="columnheader">
                  Price
                </th>
                <th scope="col" role="columnheader">
                  Supplier
                </th>
              </tr>
            </thead>
            <tbody role="rowgroup">
              {snapshot.bom.map((row) => {
                const placements = row.reference_ids
                  .map((id) =>
                    snapshot.components.find((part) => part.id === id),
                  )
                  .filter((part) => part !== undefined);
                const primaryComponent = placements[0];
                const title =
                  [...new Set(placements.map(getComponentTitle))].join(" / ") ||
                  row.mpn;
                const role = primaryComponent
                  ? getComponentRole(primaryComponent)
                  : "other";
                const illustrationTitle = primaryComponent
                  ? getComponentTitle(primaryComponent)
                  : "";
                const purchaseUrl = getSafeUrl(row.purchase_url);
                const primaryId = primaryComponent?.id;
                const hasIssue = row.reference_ids.some((id) =>
                  failedComponentIds.has(id),
                );
                const isSelected = Boolean(
                  selectedId && row.reference_ids.includes(selectedId),
                );
                return (
                  <tr
                    role="row"
                    key={`${row.manufacturer}:${row.mpn}:${row.package}`}
                    className={isSelected ? "bom-row-selected" : ""}
                  >
                    <td role="cell" className="bom-part-cell">
                      <button
                        className="report-part-button"
                        onClick={() => primaryId && onSelect(primaryId)}
                        disabled={!primaryId}
                        aria-current={isSelected ? "true" : undefined}
                      >
                        <span className={`bom-thumbnail bom-thumbnail-${role}`}>
                          <PartIllustration
                            role={role}
                            wireless={
                              illustrationTitle === "Wireless controller"
                            }
                            usb={illustrationTitle.startsWith("USB-C")}
                          />
                        </span>
                        <span className="bom-part-text">
                          <span className="bom-part-title">
                            {title}
                            {hasIssue && (
                              <span className="bom-issue">
                                <CircleAlert size={14} aria-hidden="true" />
                                <span className="sr-only">
                                  Compatibility issue
                                </span>
                              </span>
                            )}
                          </span>
                          <span className="bom-identity">{row.mpn}</span>
                        </span>
                      </button>
                      {row.ordering_note && (
                        <p className="bom-ordering-note">{row.ordering_note}</p>
                      )}
                    </td>
                    <td role="cell" className="bom-quantity">
                      <span className="bom-mobile-label" aria-hidden="true">
                        Qty
                      </span>
                      {row.order_quantity}
                      {row.order_quantity > row.required_quantity && (
                        <span className="bom-cell-note">
                          {row.required_quantity} needed
                        </span>
                      )}
                    </td>
                    <td role="cell" className="bom-money">
                      <span className="bom-mobile-label" aria-hidden="true">
                        Price
                      </span>
                      {row.extended_price === null ? (
                        <span className="text-muted">Not quoted</span>
                      ) : (
                        formatMoney(row.extended_price, row.currency)
                      )}
                    </td>
                    <td role="cell" className="bom-purchase-cell">
                      {purchaseUrl ? (
                        <a
                          className="bom-buy-link"
                          href={purchaseUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View supplier{" "}
                          <ArrowUpRight size={16} aria-hidden="true" />
                        </a>
                      ) : (
                        <span className="text-muted">No supplier link</span>
                      )}
                      {row.availability === "out_of_stock" && (
                        <span className="bom-stock stock-exception">
                          {row.stock === null
                            ? "Unavailable"
                            : row.stock === 0
                              ? "Out of stock"
                              : `Only ${row.stock} available`}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {unselectedComponents.map((part) => {
                const title = getComponentTitle(part);
                const role = getComponentRole(part);
                return (
                  <tr
                    role="row"
                    key={part.id}
                    className={`bom-row-missing${isRunning ? " bom-row-pending" : ""}${selectedId === part.id ? " bom-row-selected" : ""}`}
                  >
                    <td role="cell" className="bom-part-cell">
                      <button
                        className="report-part-button"
                        onClick={() => onSelect(part.id)}
                        aria-current={
                          selectedId === part.id ? "true" : undefined
                        }
                      >
                        <span className={`bom-thumbnail bom-thumbnail-${role}`}>
                          <PartIllustration
                            role={role}
                            wireless={title === "Wireless controller"}
                            usb={title.startsWith("USB-C")}
                          />
                        </span>
                        <span className="bom-part-text">
                          <span className="bom-part-title">{title}</span>
                          <span className="bom-missing-label">
                            {isRunning ? "Selecting…" : "Part needed"}
                          </span>
                        </span>
                      </button>
                    </td>
                    <td role="cell" className="bom-missing-message" colSpan={3}>
                      {!isRunning && "No suitable part selected"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="report-empty">No parts have been selected yet.</p>
      )}
      {snapshot.bom.length > 0 && (
        <footer className="bom-footer">
          <span>
            {hasUnpricedRows || unselectedComponents.length > 0
              ? "Partial parts subtotal"
              : "Parts subtotal"}
          </span>
          <div>
            {[...totalsByCurrency].map(([currency, total]) => (
              <strong key={currency}>{formatMoney(total, currency)}</strong>
            ))}
            {totalsByCurrency.size === 0 && <strong>Not quoted</strong>}
          </div>
          <p className="bom-total-note">
            Shipping, tax, and unquoted fees are excluded.
          </p>
        </footer>
      )}
    </section>
  );
}
