import type {
  Component,
  DesignSnapshot,
} from "../services/api/designRunApi.ts";

interface SupportGroup {
  id: string;
  parentIds: string[];
  components: Component[];
}

export const getRailNodeId = (id: string) => `rail:${id}`;
export const getInterfaceNodeId = (id: string) => `interface:${id}`;

/** The map is a view of recorded relationships, never a wiring inference. */
export function buildSystemMap(snapshot: DesignSnapshot) {
  const rails = snapshot.rails ?? [];
  const interfaces = snapshot.interfaces ?? [];
  const needs = snapshot.support_needs ?? [];
  const byId = new Map(snapshot.components.map((part) => [part.id, part]));
  const functionalIds = new Set([
    ...rails.map((rail) => rail.source_component_id),
    ...interfaces.flatMap((bus) =>
      bus.endpoints.map((endpoint) => endpoint.component_id),
    ),
  ]);
  const supportParents = new Set([
    ...byId.keys(),
    ...rails.map((rail) => rail.id),
    ...interfaces.map((bus) => bus.id),
  ]);
  // Planning can put requirement IDs in support_for; those do not describe
  // a physical support relationship and must not hide primary components.
  const parentIds = new Map(
    snapshot.components.map((part) => [
      part.id,
      new Set(
        (part.support_for ?? []).filter(
          (id) => id !== part.id && supportParents.has(id),
        ),
      ),
    ]),
  );
  for (const need of needs) {
    for (const id of need.component_ids) {
      for (const parent of need.parent_ids) {
        if (id !== parent) parentIds.get(id)?.add(parent);
      }
    }
  }

  const core: Component[] = [];
  const groups = new Map<string, SupportGroup>();
  for (const part of snapshot.components) {
    const parents = [...(parentIds.get(part.id) ?? [])].sort();
    if (!parents.length || functionalIds.has(part.id)) {
      core.push(part);
      continue;
    }
    const id = JSON.stringify(parents);
    if (!groups.has(id))
      groups.set(id, { id, parentIds: parents, components: [] });
    groups.get(id)!.components.push(part);
  }
  const coreIds = new Set(core.map((part) => part.id));
  const externalRails = rails.filter(
    (rail) => rail.source_component_id === "external",
  );
  const hasPowerConnections = rails.some(
    (rail) =>
      (rail.source_component_id === "external" ||
        coreIds.has(rail.source_component_id)) &&
      rail.loads.some(
        (load) =>
          coreIds.has(load.component_id) &&
          load.component_id !== rail.source_component_id,
      ),
  );
  // Power depth only controls placement. Unconnected/cyclic parts keep a
  // neutral starting position; no interface direction or missing link is inferred.
  const incoming = new Map(core.map((part) => [part.id, new Set<string>()]));
  const outgoing = new Map(core.map((part) => [part.id, new Set<string>()]));
  for (const rail of rails) {
    if (!coreIds.has(rail.source_component_id)) continue;
    for (const load of rail.loads) {
      if (
        !coreIds.has(load.component_id) ||
        load.component_id === rail.source_component_id
      )
        continue;
      incoming.get(load.component_id)!.add(rail.source_component_id);
      outgoing.get(rail.source_component_id)!.add(load.component_id);
    }
  }
  const depths = new Map(core.map((part) => [part.id, 0]));
  const ready = core
    .filter((part) => !incoming.get(part.id)!.size)
    .map((part) => part.id);
  const placed = new Set<string>();
  for (let index = 0; index < ready.length; index++) {
    const id = ready[index];
    placed.add(id);
    for (const child of outgoing.get(id)!) {
      depths.set(child, Math.max(depths.get(child)!, depths.get(id)! + 1));
      incoming.get(child)!.delete(id);
      if (!incoming.get(child)!.size) ready.push(child);
    }
  }
  for (const part of core) if (!placed.has(part.id)) depths.set(part.id, 0);
  const powerColumns: Component[][] = [];
  for (const part of [...core].sort(
    (a, b) => depths.get(a.id)! - depths.get(b.id)!,
  )) {
    const column = depths.get(part.id)!;
    (powerColumns[column] ??= []).push(part);
  }
  return {
    core,
    powerColumns,
    supportGroups: [...groups.values()],
    externalRails,
    hasPowerConnections,
    byId,
  };
}
