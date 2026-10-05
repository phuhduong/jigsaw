import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  ChevronDown,
  CircuitBoard,
  Layers,
  Maximize2,
  Minus,
  Plus,
  Plug,
} from "lucide-react";
import type { Component, DesignSnapshot } from "../services/api/designRunApi";
import { buildSystemMap } from "./systemRelationships.ts";
import {
  createSystemLayout,
  fitSystemLayout,
  type ComponentPosition,
} from "./systemLayout.ts";
import {
  getCurrentFindings,
  isBlockingFinding,
  isSelectedProduct,
  getSubjectComponentIds,
} from "./reportHelpers";
import { getComponentRole, getComponentTitle } from "./componentPresentation";
import PartIllustration from "./PartIllustration";
import "./SystemMap.css";

type Props = {
  snapshot: DesignSnapshot;
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export default function SystemMap({ snapshot, selectedId, onSelect }: Props) {
  const map = useMemo(() => buildSystemMap(snapshot), [snapshot]);
  const layout = useMemo(() => createSystemLayout(snapshot), [snapshot]);
  const viewport = useRef<HTMLDivElement>(null);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const [scale, setScale] = useState(1);
  const fittedLayout = useRef("");
  const manuallyZoomed = useRef(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const activeId = hoveredId ?? focusedId ?? selectedId;
  const traceId = map.core.some((part) => part.id === activeId)
    ? activeId
    : null;
  const tracedPaths = layout.paths.filter(
    (path) => traceId && path.componentIds.includes(traceId),
  );
  const neighbors = new Set([
    traceId,
    ...tracedPaths.flatMap((path) => path.componentIds),
  ]);
  const rails = snapshot.rails ?? [];
  const interfaces = snapshot.interfaces ?? [];
  const unresolvedNeeds = snapshot.support_needs.filter(
    (need) => need.status === "unresolved",
  );
  const failedChecks =
    snapshot.lifecycle === "running"
      ? []
      : getCurrentFindings(snapshot).filter(isBlockingFinding);

  // Only measure the viewport. Node positions and paths share one coordinate
  // system; opening the inspector never changes their arrangement or zoom.
  useEffect(() => {
    const element = viewport.current;
    if (!element) return;
    const measure = () => {
      const width = element.clientWidth;
      // Fit uses the available space, not the height shortened by zooming out.
      const height = parseFloat(getComputedStyle(element).maxHeight);
      const layoutKey = `${layout.width}:${layout.height}`;
      if (
        width > 0 &&
        height > 0 &&
        layout.components.length &&
        fittedLayout.current !== layoutKey &&
        !manuallyZoomed.current
      ) {
        const fit = fitSystemLayout(layout, width, height);
        setScale(
          window.matchMedia("(max-width: 560px)").matches
            ? Math.max(0.7, fit)
            : fit,
        );
        fittedLayout.current = layoutKey;
      }
      setViewportSize((previous) =>
        previous.width === width && previous.height === height
          ? previous
          : { width, height },
      );
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [layout.width, layout.height, layout.components.length]);

  useEffect(() => {
    const element = viewport.current;
    const node = layout.components.find((part) => part.id === selectedId);
    if (!element || !node) return;
    const originX = Math.max(
      0,
      (element.clientWidth - layout.width * scale) / 2,
    );
    const originY = Math.max(
      0,
      (element.clientHeight - layout.height * scale) / 2,
    );
    const left = originX + node.x * scale;
    const right = originX + (node.x + node.width) * scale;
    const top = originY + node.y * scale;
    const bottom = originY + (node.y + node.height) * scale;
    const revealX =
      left < element.scrollLeft ||
      right > element.scrollLeft + element.clientWidth;
    const revealY =
      top < element.scrollTop ||
      bottom > element.scrollTop + element.clientHeight;
    if (revealX || revealY)
      element.scrollTo({
        left: revealX
          ? (left + right - element.clientWidth) / 2
          : element.scrollLeft,
        top: revealY
          ? (top + bottom - element.clientHeight) / 2
          : element.scrollTop,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
  }, [selectedId, viewportSize, scale, layout]);

  const handleZoomChange = (nextScale: number) => {
    manuallyZoomed.current = true;
    setScale(nextScale);
  };

  const renderComponentNode = (
    part: Component,
    position: ComponentPosition,
  ) => {
    const hasProduct = isSelectedProduct(part.product);
    const failures = failedChecks.filter((finding) =>
      finding.subject_ids.some((subject) =>
        getSubjectComponentIds(snapshot, subject).includes(part.id),
      ),
    );
    const title = getComponentTitle(part);
    const status =
      snapshot.lifecycle === "running" && !part.selection_error
        ? "Selecting…"
        : "Not selected";
    const productLabel = hasProduct ? part.product!.mpn : status;
    const failureLabel = `${failures.length} failed ${failures.length === 1 ? "check" : "checks"}`;
    return (
      <button
        key={part.id}
        type="button"
        data-map-node={part.id}
        style={{
          left: position.x,
          top: position.y,
          width: position.width,
          height: position.height,
        }}
        className={`system-node${!hasProduct ? " system-node-pending" : ""}${traceId && !neighbors.has(part.id) ? " is-muted" : ""}${part.id === traceId ? " is-trace-source" : ""}`}
        aria-pressed={selectedId === part.id}
        aria-label={`${title}, ${productLabel}, ${part.id}${failures.length ? `, ${failureLabel}` : ""}`}
        onClick={() => onSelect(part.id)}
        onPointerEnter={(event) => {
          if (event.pointerType !== "touch") setHoveredId(part.id);
        }}
        onPointerLeave={() => setHoveredId(null)}
        onFocus={() => setFocusedId(part.id)}
        onBlur={() => setFocusedId(null)}
        title={part.purpose || part.name}
      >
        {map.core.filter((component) => getComponentTitle(component) === title)
          .length > 1 && (
          <span className="system-node-reference">{part.id}</span>
        )}
        <span className="system-object-stage">
          <PartIllustration
            role={getComponentRole(part)}
            wireless={title === "Wireless controller"}
            usb={title.startsWith("USB-C")}
          />
        </span>
        <span className="system-object-label">
          <strong className="system-node-title">{title}</strong>
          <span className="system-node-mpn">{productLabel}</span>
        </span>
        {failures.length > 0 && (
          <span className="system-node-issue" title={failureLabel}>
            <AlertCircle size={15} aria-hidden="true" />
            <span className="sr-only">{failureLabel}</span>
          </span>
        )}
      </button>
    );
  };

  return (
    <section
      className="system-map"
      aria-label="Selected system and recorded relationships"
    >
      {!snapshot.components.length ? (
        <div className="system-map-empty">
          <CircuitBoard size={38} strokeWidth={1} aria-hidden="true" />
          <p>
            {snapshot.lifecycle === "running"
              ? "Building a component plan…"
              : "No components selected yet."}
          </p>
        </div>
      ) : (
        <>
          <div className="system-map-toolbar">
            <div className="system-map-legend" aria-label="Relationship types">
              {rails.length > 0 && (
                <span>
                  <i className="system-legend-power" />
                  Power
                </span>
              )}
              {interfaces.length > 0 && (
                <span>
                  <i className="system-legend-interface" />
                  Data
                </span>
              )}
            </div>
            <div className="system-zoom" role="group" aria-label="Diagram zoom">
              <button
                type="button"
                aria-label="Zoom out"
                title="Zoom out"
                onClick={() => handleZoomChange(Math.max(0.2, scale - 0.15))}
                disabled={scale <= 0.2}
              >
                <Minus size={14} />
              </button>
              <span className="system-zoom-value" aria-live="polite">
                {Math.round(scale * 100)}%
              </span>
              <button
                type="button"
                aria-label="Zoom in"
                title="Zoom in"
                onClick={() => handleZoomChange(Math.min(1.25, scale + 0.15))}
                disabled={scale >= 1.25}
              >
                <Plus size={14} />
              </button>
              <button
                type="button"
                className="system-zoom-fit"
                aria-label="Fit diagram"
                title="Fit diagram"
                onClick={() => {
                  const element = viewport.current;
                  if (element)
                    handleZoomChange(
                      fitSystemLayout(
                        layout,
                        element.clientWidth,
                        parseFloat(getComputedStyle(element).maxHeight),
                      ),
                    );
                }}
              >
                <Maximize2 size={13} />
                <span>Fit</span>
              </button>
            </div>
          </div>
          <div
            className="system-viewport"
            style={{
              height: `min(${layout.height * scale + 24}px, var(--map-height))`,
            }}
            ref={viewport}
            tabIndex={0}
            role="region"
            aria-label="Component diagram"
          >
            <div
              className="system-scaled-canvas"
              style={{
                width: layout.width * scale,
                height: layout.height * scale,
              }}
            >
              <div
                className="system-canvas"
                style={{
                  width: layout.width,
                  height: layout.height,
                  transform: `scale(${scale})`,
                }}
              >
                <svg
                  className="system-connectors"
                  width={layout.width}
                  height={layout.height}
                  aria-hidden="true"
                >
                  {layout.paths.map((path) => {
                    const related =
                      !traceId || path.componentIds.includes(traceId);
                    return (
                      <g
                        key={path.id}
                        className={`system-connection system-connection-${path.kind}${related ? " is-related" : ""}${traceId && related ? " is-traced" : ""}`}
                      >
                        <path d={path.d} />
                        {path.endpoints.map((endpoint, index) =>
                          endpoint.kind === "target" ? (
                            <path
                              key={index}
                              className="system-arrow"
                              d={
                                endpoint.side === "left"
                                  ? `M ${endpoint.x - 5} ${endpoint.y - 3} L ${endpoint.x} ${endpoint.y} L ${endpoint.x - 5} ${endpoint.y + 3}`
                                  : `M ${endpoint.x + 5} ${endpoint.y - 3} L ${endpoint.x} ${endpoint.y} L ${endpoint.x + 5} ${endpoint.y + 3}`
                              }
                            />
                          ) : (
                            <circle
                              key={index}
                              className="system-port"
                              cx={endpoint.x}
                              cy={endpoint.y}
                              r={2.3}
                            />
                          ),
                        )}
                        {path.label && (
                          <text
                            className="system-connection-label"
                            x={path.label.x}
                            y={path.label.y}
                            textAnchor={path.label.anchor}
                            dominantBaseline="middle"
                          >
                            {path.label.text}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </svg>
                {layout.components.map((node) => {
                  const part = map.byId.get(node.id);
                  return part ? renderComponentNode(part, node) : null;
                })}
                {layout.externalNodes.map((node) => (
                  <div
                    className="system-external-node"
                    key={node.id}
                    style={{
                      left: node.x,
                      top: node.y,
                      width: node.width,
                      height: node.height,
                    }}
                  >
                    {node.kind === "supply" && (
                      <Plug size={15} strokeWidth={1.5} aria-hidden="true" />
                    )}
                    <span>{node.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {(map.supportGroups.length > 0 || unresolvedNeeds.length > 0) && (
        <div className="system-support">
          <div className="system-subheading">
            <Layers size={15} aria-hidden="true" />
            <h3>Supporting parts</h3>
          </div>
          {map.supportGroups.map((group) => (
            <details
              key={group.id}
              className="system-support-group"
              open={
                group.components.some((part) => part.id === selectedId) ||
                undefined
              }
            >
              <summary>
                <span>
                  For{" "}
                  {group.parentIds
                    .map((id) => map.byId.get(id))
                    .filter((part) => part !== undefined)
                    .map(getComponentTitle)
                    .join(" · ") || "this device"}
                </span>
                <span>
                  {group.components.length}{" "}
                  {group.components.length === 1 ? "part" : "parts"}
                  <ChevronDown size={14} aria-hidden="true" />
                </span>
              </summary>
              <ul>
                {group.components.map((part) => (
                  <li key={part.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(part.id)}
                      aria-pressed={selectedId === part.id}
                    >
                      <span className="system-node-id">{part.id}</span>
                      <span>
                        <strong>{getComponentTitle(part)}</strong>
                        <small>
                          {part.product?.mpn.trim() || part.name}
                          {!isSelectedProduct(part.product)
                            ? " · Not selected"
                            : ""}
                        </small>
                      </span>
                      <ArrowRight size={14} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            </details>
          ))}
          {unresolvedNeeds.length > 0 && (
            <details className="system-support-notes">
              <summary>Support notes</summary>
              <ul>
                {unresolvedNeeds.map((need) => (
                  <li key={need.id}>
                    {need.purpose}
                    {need.parent_ids.length > 0 && (
                      <span> · {need.parent_ids.join(", ")}</span>
                    )}
                    {need.explanation && <p>{need.explanation}</p>}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      <ul
        className="system-accessible-connections"
        aria-label="Recorded relationships"
      >
        {rails.map((rail) => (
          <li key={`power:${rail.id}`}>
            {rail.source_component_id === "external"
              ? "External supply"
              : (map.byId.get(rail.source_component_id)?.name ??
                rail.source_component_id)}{" "}
            supplies{" "}
            {rail.loads
              .map(
                (load) =>
                  map.byId.get(load.component_id)?.name ?? load.component_id,
              )
              .join(", ") || "no recorded loads"}
            .
          </li>
        ))}
        {interfaces.map((bus) => (
          <li key={`data:${bus.id}`}>
            {bus.protocol} shared by{" "}
            {bus.endpoints
              .map((endpoint) =>
                endpoint.component_id === "external"
                  ? "an external endpoint"
                  : (map.byId.get(endpoint.component_id)?.name ??
                    endpoint.component_id),
              )
              .join(", ")}
            .
          </li>
        ))}
      </ul>
    </section>
  );
}
