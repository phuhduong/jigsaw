import type { DesignSnapshot } from "../services/api/designRunApi.ts";
import {
  buildSystemMap,
  getInterfaceNodeId,
  getRailNodeId,
} from "./systemRelationships.ts";

interface Point {
  x: number;
  y: number;
}
export interface ComponentPosition extends Point {
  id: string;
  width: number;
  height: number;
}
interface ExternalPosition extends ComponentPosition {
  kind: "supply" | "interface";
  label: string;
  railId?: string;
  interfaceId?: string;
}
interface LayoutEndpoint extends Point {
  nodeId: string;
  side: "left" | "right";
  kind: "source" | "target" | "data";
}
interface LayoutPath {
  id: string;
  relationId: string;
  kind: "power" | "interface";
  componentIds: string[];
  d: string;
  runs: Point[][];
  endpoints: LayoutEndpoint[];
  label?: Point & { text: string; anchor: "start" | "middle" };
}
export interface SystemLayout {
  width: number;
  height: number;
  components: ComponentPosition[];
  externalNodes: ExternalPosition[];
  paths: LayoutPath[];
}

export function fitSystemLayout(
  layout: Pick<SystemLayout, "width" | "height">,
  width: number,
  height: number,
): number {
  return Math.min(1, width / layout.width, height / layout.height);
}

const CARD_WIDTH = 220;
const CARD_HEIGHT = 174;
const COLUMN_GAP = 128;
const ROW_GAP = 72;
const PADDING = 24;
const getPointKey = ({ x, y }: Point) => `${x},${y}`;

/** Round only bends, keeping branch junctions at their exact shared coordinates. */
function createRoundedPath(points: Point[], radius = 10): string {
  if (!points.length) return "";
  let d = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length - 1; index++) {
    const before = points[index - 1];
    const point = points[index];
    const after = points[index + 1];
    const beforeLength =
      Math.abs(point.x - before.x) + Math.abs(point.y - before.y);
    const afterLength =
      Math.abs(after.x - point.x) + Math.abs(after.y - point.y);
    const bend = Math.min(radius, beforeLength / 2, afterLength / 2);
    if (
      (before.x === point.x && point.x === after.x) ||
      (before.y === point.y && point.y === after.y)
    ) {
      d += ` L ${point.x} ${point.y}`;
      continue;
    }
    const approach = {
      x: point.x + Math.sign(before.x - point.x) * bend,
      y: point.y + Math.sign(before.y - point.y) * bend,
    };
    const depart = {
      x: point.x + Math.sign(after.x - point.x) * bend,
      y: point.y + Math.sign(after.y - point.y) * bend,
    };
    d += ` L ${approach.x} ${approach.y} Q ${point.x} ${point.y} ${depart.x} ${depart.y}`;
  }
  if (points.length > 1) d += ` L ${points.at(-1)!.x} ${points.at(-1)!.y}`;
  return d;
}

// Routing creates shared spines split at their branches. Join degree-two
// segments so their corners round; a junction itself must remain connected.
function joinSegments(segments: Point[][]): Point[][] {
  const vertices = new Map<string, { point: Point; edges: number[] }>();
  const edges: [string, string][] = [];
  const seen = new Set<string>();
  for (const [from, to] of segments) {
    const a = getPointKey(from);
    const b = getPointKey(to);
    const key = [a, b].sort().join("|");
    if (a === b || seen.has(key)) continue;
    seen.add(key);
    const index = edges.length;
    edges.push([a, b]);
    for (const point of [from, to]) {
      const id = getPointKey(point);
      if (!vertices.has(id)) vertices.set(id, { point, edges: [] });
      vertices.get(id)!.edges.push(index);
    }
  }
  const visited = new Set<number>();
  const runs: Point[][] = [];
  const walk = (start: string, edge: number) => {
    const run = [vertices.get(start)!.point];
    let current = start;
    while (!visited.has(edge)) {
      visited.add(edge);
      const [a, b] = edges[edge];
      current = a === current ? b : a;
      const vertex = vertices.get(current)!;
      run.push(vertex.point);
      if (vertex.edges.length !== 2) break;
      edge = vertex.edges.find((candidate) => !visited.has(candidate)) ?? edge;
    }
    runs.push(run);
  };
  for (const [id, vertex] of vertices) {
    if (vertex.edges.length === 2) continue;
    for (const edge of vertex.edges) {
      if (!visited.has(edge)) walk(id, edge);
    }
  }
  for (let edge = 0; edge < edges.length; edge++) {
    if (!visited.has(edge)) walk(edges[edge][0], edge);
  }
  return runs;
}

function addSpineSegments(
  segments: Point[][],
  x: number,
  branches: Point[],
  bottom?: number,
) {
  const ys = [
    ...new Set([
      ...branches.map((point) => point.y),
      ...(bottom === undefined ? [] : [bottom]),
    ]),
  ].sort((a, b) => a - b);
  for (let index = 1; index < ys.length; index++)
    segments.push([
      { x, y: ys[index - 1] },
      { x, y: ys[index] },
    ]);
  for (const point of branches) segments.push([point, { x, y: point.y }]);
}

/** A fixed architecture plane: resizing scrolls the map, never changes its topology. */
export function createSystemLayout(snapshot: DesignSnapshot): SystemLayout {
  const map = buildSystemMap(snapshot);
  const rails = snapshot.rails ?? [];
  const interfaces = snapshot.interfaces ?? [];
  const externalInterfaces = interfaces.filter((bus) =>
    bus.endpoints.some((endpoint) => endpoint.component_id === "external"),
  );
  let columns = map.powerColumns;
  if (columns.length <= 1 && map.core.length > 1 && !map.hasPowerConnections) {
    const count = Math.min(3, Math.ceil(Math.sqrt(map.core.length)));
    columns = Array.from({ length: count }, (_, column) =>
      map.core.filter((_, index) => index % count === column),
    );
  }
  const offset = map.externalRails.length ? 1 : 0;
  const columnCount =
    offset + columns.length + (externalInterfaces.length ? 1 : 0);
  const rows = Math.max(
    1,
    map.externalRails.length,
    externalInterfaces.length,
    ...columns.map((column) => column.length),
  );
  const contentHeight = rows * CARD_HEIGHT + (rows - 1) * ROW_GAP;
  const bottom = PADDING + contentHeight;
  const relationIds = [
    ...rails.map((rail) => `rail:${rail.id}`),
    ...interfaces.map((bus) => `bus:${bus.id}`),
  ];
  // Each relation keeps its own channel through every inter-column gutter.
  const getLaneOffset = (id: string) =>
    30 +
    (relationIds.length > 1
      ? (relationIds.indexOf(id) * 68) / (relationIds.length - 1)
      : 0);
  const hasReturnToFirstColumn =
    !offset &&
    rails.some((rail) => {
      const source = columns.findIndex((column) =>
        column.some((part) => part.id === rail.source_component_id),
      );
      return (
        source >= 0 &&
        rail.loads.some((load) =>
          columns[0]?.some((part) => part.id === load.component_id),
        )
      );
    });
  const left = hasReturnToFirstColumn ? COLUMN_GAP : PADDING;
  const getColumnX = (column: number) =>
    left + column * (CARD_WIDTH + COLUMN_GAP);
  const getRightChannelX = (column: number, relationId: string) =>
    getColumnX(column) + CARD_WIDTH + getLaneOffset(relationId);
  const getLeftChannelX = (column: number, relationId: string) =>
    getRightChannelX(column - 1, relationId);
  const components: ComponentPosition[] = [];
  const externalNodes: ExternalPosition[] = [];
  const columnByNodeId = new Map<string, number>();
  const getRowY = (index: number, count: number) =>
    PADDING +
    (contentHeight - (count * CARD_HEIGHT + (count - 1) * ROW_GAP)) / 2 +
    index * (CARD_HEIGHT + ROW_GAP);
  columns.forEach((column, depth) => {
    column.forEach((part, index) => {
      components.push({
        id: part.id,
        x: getColumnX(depth + offset),
        y: getRowY(index, column.length),
        width: CARD_WIDTH,
        height: CARD_HEIGHT,
      });
      columnByNodeId.set(part.id, depth + offset);
    });
  });
  map.externalRails.forEach((rail, index) => {
    const id = getRailNodeId(rail.id);
    externalNodes.push({
      id,
      kind: "supply",
      railId: rail.id,
      label:
        map.externalRails.length > 1
          ? `External supply ${index + 1}`
          : "External supply",
      x: getColumnX(0) + 52,
      y: getRowY(index, map.externalRails.length) + 56,
      width: 116,
      height: 48,
    });
    columnByNodeId.set(id, 0);
  });
  externalInterfaces.forEach((bus, index) => {
    const id = getInterfaceNodeId(bus.id);
    const column = columnCount - 1;
    externalNodes.push({
      id,
      kind: "interface",
      interfaceId: bus.id,
      label: "External interface",
      x: getColumnX(column) + 52,
      y: getRowY(index, externalInterfaces.length) + 63,
      width: 116,
      height: 48,
    });
    columnByNodeId.set(id, column);
  });
  const nodes = new Map(
    [...components, ...externalNodes].map((node) => [node.id, node]),
  );
  const coreIds = new Set(components.map((part) => part.id));
  const portRelations = new Map<string, string[]>();
  const registerPortRelation = (
    nodeId: string,
    kind: LayoutEndpoint["kind"],
    relationId: string,
  ) => {
    const key = `${kind}:${nodeId}`;
    const list = portRelations.get(key) ?? [];
    if (!list.includes(relationId)) list.push(relationId);
    portRelations.set(key, list);
  };
  for (const rail of rails) {
    const relationId = `rail:${rail.id}`;
    registerPortRelation(
      rail.source_component_id === "external"
        ? getRailNodeId(rail.id)
        : rail.source_component_id,
      "source",
      relationId,
    );
    for (const load of rail.loads)
      registerPortRelation(load.component_id, "target", relationId);
  }
  for (const bus of interfaces) {
    for (const endpoint of bus.endpoints) {
      registerPortRelation(
        endpoint.component_id === "external"
          ? getInterfaceNodeId(bus.id)
          : endpoint.component_id,
        "data",
        `bus:${bus.id}`,
      );
    }
  }
  const getPort = (
    nodeId: string,
    relationId: string,
    kind: LayoutEndpoint["kind"],
  ): LayoutEndpoint => {
    const node = nodes.get(nodeId)!;
    const relations = portRelations.get(`${kind}:${nodeId}`)!;
    const spread =
      relations.length > 1
        ? (relations.indexOf(relationId) / (relations.length - 1) - 0.5) *
          Math.min(24, (relations.length - 1) * 12)
        : 0;
    const side = kind === "target" ? "left" : "right";
    return {
      nodeId,
      kind,
      side,
      x: node.x + (side === "right" ? node.width : 0),
      y:
        node.y +
        (coreIds.has(nodeId) ? (kind === "data" ? 124 : 80) : node.height / 2) +
        spread,
    };
  };
  const paths: LayoutPath[] = [];
  let belowLanes = 0;
  const allocateBelowLane = () => bottom + 42 + belowLanes++ * 34;
  const addPath = (
    path: Omit<LayoutPath, "d" | "runs">,
    segments: Point[][],
  ) => {
    const runs = joinSegments(segments);
    paths.push({
      ...path,
      runs,
      d: runs.map((run) => createRoundedPath(run)).join(" "),
    });
  };
  for (const rail of rails) {
    const relationId = `rail:${rail.id}`;
    const sourceId =
      rail.source_component_id === "external"
        ? getRailNodeId(rail.id)
        : rail.source_component_id;
    if (!nodes.has(sourceId)) continue;
    const targets = [
      ...new Set(rail.loads.map((load) => load.component_id)),
    ].filter((id) => coreIds.has(id) && id !== sourceId);
    if (!targets.length) continue;
    const source = getPort(sourceId, relationId, "source");
    const sourceColumn = columnByNodeId.get(sourceId)!;
    const endpoints = [
      source,
      ...targets.map((id) => getPort(id, relationId, "target")),
    ];
    const adjacent = endpoints
      .slice(1)
      .filter(
        (endpoint) => columnByNodeId.get(endpoint.nodeId) === sourceColumn + 1,
      );
    const remote = endpoints
      .slice(1)
      .filter(
        (endpoint) => columnByNodeId.get(endpoint.nodeId) !== sourceColumn + 1,
      );
    const segments: Point[][] = [];
    const below = remote.length ? allocateBelowLane() : undefined;
    const sourceX = getRightChannelX(sourceColumn, relationId);
    addSpineSegments(segments, sourceX, [source, ...adjacent], below);
    if (below !== undefined) {
      const remoteColumns = [
        ...new Set(
          remote.map((endpoint) => columnByNodeId.get(endpoint.nodeId)!),
        ),
      ];
      const channels = [sourceX];
      for (const column of remoteColumns) {
        const x = getLeftChannelX(column, relationId);
        channels.push(x);
        addSpineSegments(
          segments,
          x,
          remote.filter(
            (endpoint) => columnByNodeId.get(endpoint.nodeId) === column,
          ),
          below,
        );
      }
      channels.sort((a, b) => a - b);
      for (let index = 1; index < channels.length; index++)
        segments.push([
          { x: channels[index - 1], y: below },
          { x: channels[index], y: below },
        ]);
    }
    addPath(
      {
        id: relationId,
        relationId,
        kind: "power",
        componentIds: [sourceId, ...targets].filter((id) => coreIds.has(id)),
        endpoints,
      },
      segments,
    );
  }
  for (const bus of interfaces) {
    const relationId = `bus:${bus.id}`;
    const ids = [
      ...new Set(
        bus.endpoints.map((endpoint) =>
          endpoint.component_id === "external"
            ? getInterfaceNodeId(bus.id)
            : endpoint.component_id,
        ),
      ),
    ].filter((id) => nodes.has(id));
    if (ids.length < 2) continue;
    const endpoints = ids.map((id) => getPort(id, relationId, "data"));
    const busColumns = [
      ...new Set(ids.map((id) => columnByNodeId.get(id)!)),
    ].sort((a, b) => a - b);
    const segments: Point[][] = [];
    const below = busColumns.length > 1 ? allocateBelowLane() : undefined;
    const channels = busColumns.map((column) =>
      getRightChannelX(column, relationId),
    );
    for (const column of busColumns)
      addSpineSegments(
        segments,
        getRightChannelX(column, relationId),
        endpoints.filter(
          (endpoint) => columnByNodeId.get(endpoint.nodeId) === column,
        ),
        below,
      );
    if (below !== undefined) {
      for (let index = 1; index < channels.length; index++) {
        segments.push([
          { x: channels[index - 1], y: below },
          { x: channels[index], y: below },
        ]);
      }
    }
    const label: NonNullable<LayoutPath["label"]> =
      below === undefined
        ? {
            x: channels[0] + 12,
            y:
              (Math.min(...endpoints.map((endpoint) => endpoint.y)) +
                Math.max(...endpoints.map((endpoint) => endpoint.y))) /
              2,
            text: bus.protocol,
            anchor: "start",
          }
        : {
            x: (channels[0] + channels.at(-1)!) / 2,
            y: below + 17,
            text: bus.protocol,
            anchor: "middle",
          };
    addPath(
      {
        id: relationId,
        relationId,
        kind: "interface",
        componentIds: ids.filter((id) => coreIds.has(id)),
        endpoints,
        label,
      },
      segments,
    );
  }
  const right = columnCount ? getColumnX(columnCount - 1) + CARD_WIDTH : 0;
  const labelsRight = paths.reduce(
    (edge, path) =>
      Math.max(
        edge,
        path.label ? path.label.x + path.label.text.length * 7 + 16 : 0,
      ),
    right,
  );
  return {
    width: Math.max(320, right + 110, labelsRight),
    height: belowLanes
      ? bottom + 42 + (belowLanes - 1) * 34 + 38
      : bottom + PADDING,
    components,
    externalNodes,
    paths,
  };
}
