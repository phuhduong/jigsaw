import { useId } from "react";
import { ChevronDown, ExternalLink, X } from "lucide-react";
import { getSafeUrl, type DesignSnapshot } from "../services/api/designRunApi";
import { CompatibilityIssue } from "./ReviewPanel";
import { getComponentRole, getComponentTitle } from "./componentPresentation";
import PartIllustration from "./PartIllustration";
import {
  formatMoney,
  getCurrentFindings,
  getSubjectComponentIds,
  isBlockingFinding,
  isSelectedProduct,
} from "./reportHelpers";
import "./report.css";

export default function ComponentDetail({
  snapshot,
  componentId,
  onClose,
  onSelect,
}: {
  snapshot: DesignSnapshot;
  componentId: string;
  onClose?: () => void;
  onSelect?: (id: string) => void;
}) {
  const headingId = useId();
  const component = snapshot.components.find((item) => item.id === componentId);
  if (!component) return null;
  const product = component.product;
  const row = snapshot.bom.find((item) =>
    item.reference_ids.includes(componentId),
  );
  const isRunning = snapshot.lifecycle === "running";
  const failures = isRunning
    ? []
    : getCurrentFindings(snapshot).filter(
        (finding) =>
          isBlockingFinding(finding) &&
          finding.subject_ids.some((id) =>
            getSubjectComponentIds(snapshot, id).includes(componentId),
          ),
      );
  const purchaseUrl = getSafeUrl(row?.purchase_url || product?.product_url);
  const datasheetUrl = getSafeUrl(product?.datasheet_url || row?.datasheet_url);
  const title = getComponentTitle(component);
  const role = getComponentRole(component);
  const hasSelectedProduct = isSelectedProduct(product);

  return (
    <aside
      className={`component-detail component-detail-${role}`}
      aria-labelledby={headingId}
    >
      <header className="component-title-row">
        <h2 id={headingId}>{title}</h2>
        {onClose && (
          <button
            className="button button-quiet button-small inspector-close"
            onClick={onClose}
            aria-label="Close component details"
          >
            <X size={18} aria-hidden="true" />
          </button>
        )}
      </header>
      <div className="component-identity">
        <span className="component-illustration">
          <PartIllustration
            role={role}
            wireless={title === "Wireless controller"}
            usb={title.startsWith("USB-C")}
          />
        </span>
        <div>
          {product?.mpn.trim() ? (
            <p className="component-mpn">{product.mpn}</p>
          ) : (
            <p
              className={isRunning ? "component-pending" : "component-missing"}
            >
              {isRunning ? "Selecting…" : "Part needed"}
            </p>
          )}
          {product?.manufacturer.trim() && (
            <p className="component-manufacturer">{product.manufacturer}</p>
          )}
        </div>
      </div>
      {component.purpose && (
        <p className="component-purpose">{component.purpose}</p>
      )}
      {!hasSelectedProduct && !isRunning && failures.length === 0 && (
        <p className="component-selection-error">
          A suitable part has not been selected yet.
        </p>
      )}
      {hasSelectedProduct && (
        <div className="component-purchase">
          {row && (
            <div className="component-price-row">
              <p className="component-price">
                {row.unit_price === null
                  ? "Price unavailable"
                  : formatMoney(row.unit_price, row.currency)}
                {row.unit_price !== null && <span>each</span>}
              </p>
              {row.availability === "out_of_stock" && (
                <p className="stock-exception">
                  {row.stock === null
                    ? "Unavailable"
                    : row.stock === 0
                      ? "Out of stock"
                      : `Only ${row.stock} available`}
                </p>
              )}
            </div>
          )}
          {(purchaseUrl || datasheetUrl) && (
            <div className="component-links">
              {purchaseUrl && (
                <a
                  className="component-supplier"
                  href={purchaseUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View supplier <ExternalLink size={14} aria-hidden="true" />
                </a>
              )}
              {datasheetUrl && (
                <a
                  href={datasheetUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Datasheet <ExternalLink size={14} aria-hidden="true" />
                </a>
              )}
            </div>
          )}
        </div>
      )}
      {failures.length > 0 && (
        <section className="component-failures">
          <h3>Compatibility issues</h3>
          {failures.map((finding) => (
            <CompatibilityIssue
              key={finding.id}
              snapshot={snapshot}
              finding={finding}
              onSelect={onSelect}
            />
          ))}
        </section>
      )}
      {component.selection_reason &&
        component.selection_reason !== component.purpose && (
          <details className="component-rationale" key={componentId}>
            <summary>
              Why this part <ChevronDown size={14} aria-hidden="true" />
            </summary>
            <p>{component.selection_reason}</p>
          </details>
        )}
    </aside>
  );
}
