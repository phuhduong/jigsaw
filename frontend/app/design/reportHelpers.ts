import type {
  DesignSnapshot,
  Finding,
  Product,
} from "../services/api/designRunApi";

export function isSelectedProduct(product: Product | null): boolean {
  return Boolean(product?.manufacturer.trim() && product.mpn.trim());
}

export function formatMoney(value: number | null, currency: string): string {
  if (value === null) return "Unknown";
  return `${currency} ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
}

export function getCurrentFindings(snapshot: DesignSnapshot): Finding[] {
  return snapshot.findings.filter(
    (finding) => finding.revision === snapshot.revision,
  );
}

export function isBlockingFinding(finding: Finding): boolean {
  return (
    finding.kind === "check" &&
    finding.status === "fail" &&
    finding.area !== "evidence"
  );
}

/** Resolve saved subject references to placements without inventing connections. */
export function getSubjectComponentIds(
  snapshot: DesignSnapshot,
  id: string,
): string[] {
  const getDirectComponentIds = (subjectId: string): string[] => {
    if (snapshot.components.some((component) => component.id === subjectId))
      return [subjectId];
    const rail = snapshot.rails.find((item) => item.id === subjectId);
    if (rail)
      return [
        rail.source_component_id,
        ...rail.loads.map((load) => load.component_id),
      ];
    const bus = snapshot.interfaces.find((item) => item.id === subjectId);
    if (bus) return bus.endpoints.map((endpoint) => endpoint.component_id);
    const requirement = snapshot.requirements.find(
      (item) => item.id === subjectId || `req:${item.id}` === subjectId,
    );
    if (requirement) return requirement.component_ids;
    const signal = snapshot.signal_checks.find((item) => item.id === subjectId);
    if (signal)
      return [signal.source_component_id, signal.receiver_component_id];
    return [];
  };
  const support = snapshot.support_needs.find((item) => item.id === id);
  const source = snapshot.source_support_needs.find((item) => item.id === id);
  const componentIds = support
    ? [
        ...support.component_ids,
        ...support.parent_ids.flatMap(getDirectComponentIds),
        ...(source?.parent_ids.flatMap(getDirectComponentIds) ?? []),
      ]
    : source
      ? source.parent_ids.flatMap(getDirectComponentIds)
      : getDirectComponentIds(id);
  return [...new Set(componentIds)].filter((ref) =>
    snapshot.components.some((component) => component.id === ref),
  );
}
