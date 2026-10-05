import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  Component,
  Interface,
  Rail,
} from "../app/services/api/designRunApi.ts";
import {
  createSystemLayout,
  fitSystemLayout,
} from "../app/design/systemLayout.ts";
import { savedRun } from "./fixtures/designRun.ts";

const createPart = (id: string): Component => ({
  id,
  name: id,
  kind: "active",
  purpose: "Fixture part",
  support_for: [],
  selection_reason: "",
  selection_error: null,
  product: null,
  document_ids: [],
  document_errors: [],
});
const createRail = (id: string, source: string, loads: string[]): Rail => ({
  id,
  source_component_id: source,
  description: "Fixture supply",
  voltage_min: null,
  voltage_max: null,
  available_current: null,
  evidence_ids: [],
  loads: loads.map((component_id) => ({
    component_id,
    voltage_min: null,
    voltage_max: null,
    current: null,
  })),
});
const createInterface = (id: string, endpoints: string[]): Interface => ({
  id,
  protocol: "I2C",
  configuration: "",
  evidence_ids: [],
  endpoints: endpoints.map((component_id) => ({
    component_id,
    address: null,
    assumption_id: null,
  })),
});

test("diagram fit respects both dimensions without enlarging small diagrams", () => {
  assert.equal(fitSystemLayout({ width: 1000, height: 800 }, 1200, 600), 0.75);
  assert.equal(fitSystemLayout({ width: 1000, height: 400 }, 800, 600), 0.8);
  assert.equal(fitSystemLayout({ width: 300, height: 200 }, 800, 600), 1);
});

/** Routes may touch a node's ports or boundary, but never cross its interior. */
function assertClearRoutes(layout: ReturnType<typeof createSystemLayout>) {
  const nodes = [...layout.components, ...layout.externalNodes];
  for (const node of nodes) {
    assert.ok(node.x >= 0 && node.y >= 0);
    assert.ok(
      node.x + node.width <= layout.width &&
        node.y + node.height <= layout.height,
    );
    for (const other of nodes) {
      if (node === other) continue;
      assert.ok(
        node.x + node.width <= other.x ||
          other.x + other.width <= node.x ||
          node.y + node.height <= other.y ||
          other.y + other.height <= node.y,
        `${node.id} overlaps ${other.id}`,
      );
    }
  }
  for (const path of layout.paths) {
    assert.ok(path.d.length > 0);
    for (const run of path.runs) {
      for (const point of run)
        assert.ok(
          point.x >= 0 &&
            point.x <= layout.width &&
            point.y >= 0 &&
            point.y <= layout.height,
          `${path.id} leaves the canvas`,
        );
      for (let i = 1; i < run.length; i++) {
        const [a, b] = [run[i - 1], run[i]];
        assert.ok(
          a.x === b.x || a.y === b.y,
          `${path.id} has a diagonal segment`,
        );
        for (const node of nodes) {
          const crosses =
            a.x === b.x
              ? a.x > node.x &&
                a.x < node.x + node.width &&
                Math.max(a.y, b.y) > node.y &&
                Math.min(a.y, b.y) < node.y + node.height
              : a.y > node.y &&
                a.y < node.y + node.height &&
                Math.max(a.x, b.x) > node.x &&
                Math.min(a.x, b.x) < node.x + node.width;
          assert.ok(!crosses, `${path.id} crosses ${node.id}`);
        }
      }
    }
    for (const endpoint of path.endpoints) {
      const node = nodes.find((node) => node.id === endpoint.nodeId);
      assert.ok(node, `${path.id} references a missing node`);
      assert.equal(
        endpoint.x,
        endpoint.side === "left" ? node.x : node.x + node.width,
      );
      assert.ok(endpoint.y > node.y && endpoint.y < node.y + node.height);
    }
  }
}

test("power branches and a same-column bus preserve recorded relationships without crossing parts", () => {
  const layout = createSystemLayout({
    ...savedRun,
    components: ["U1", "U2", "J1", "U3"].map(createPart),
    rails: [
      createRail("5V", "J1", ["U3"]),
      createRail("3V3", "U3", ["U1", "U2"]),
    ],
    interfaces: [createInterface("SENSORS", ["U1", "U2"])],
  });
  assert.deepEqual(
    new Set(layout.components.map((node) => node.id)),
    new Set(["U1", "U2", "J1", "U3"]),
  );
  assert.deepEqual(layout.paths.map((path) => path.relationId).sort(), [
    "bus:SENSORS",
    "rail:3V3",
    "rail:5V",
  ]);
  const input = layout.paths.find((path) => path.relationId === "rail:5V")!;
  assert.equal(
    input.endpoints[0].y,
    input.endpoints[1].y,
    "one input and one output should remain aligned",
  );
  const power = layout.paths.find((path) => path.relationId === "rail:3V3")!;
  assert.deepEqual(
    power.endpoints.map(({ nodeId, kind, side }) => [nodeId, kind, side]),
    [
      ["U3", "source", "right"],
      ["U1", "target", "left"],
      ["U2", "target", "left"],
    ],
  );
  const data = layout.paths.find((path) => path.kind === "interface")!;
  assert.equal(data.label?.text, "I2C");
  assert.ok(
    data.endpoints.every(
      (endpoint) => endpoint.kind === "data" && endpoint.side === "right",
    ),
  );
  const ys = data.endpoints.map((endpoint) => endpoint.y);
  assert.ok(
    data.runs
      .flat()
      .every(
        (point) => point.y >= Math.min(...ys) && point.y <= Math.max(...ys),
      ),
    "same-column bus should use a side spine",
  );
  assertClearRoutes(layout);
});

test("long regulator chains and rails skipping columns retain separate clear routes", () => {
  const layout = createSystemLayout({
    ...savedRun,
    components: ["E", "D", "C", "B", "A"].map(createPart),
    rails: [
      createRail("AB", "A", ["B"]),
      createRail("BC", "B", ["C", "E"]),
      createRail("CD", "C", ["D"]),
      createRail("DE", "D", ["E"]),
      createRail("AE", "A", ["E"]),
    ],
  });
  const positions = new Map(layout.components.map((node) => [node.id, node.x]));
  assert.ok(
    ["A", "B", "C", "D"].every(
      (id, index) =>
        positions.get(id)! < positions.get(["B", "C", "D", "E"][index])!,
    ),
  );
  assert.equal(layout.paths.length, 5);
  assertClearRoutes(layout);
});

test("external supplies and external interface endpoints connect through clear cross-column routes", () => {
  const singleSupply = createSystemLayout({
    ...savedRun,
    components: [createPart("A")],
    rails: [createRail("VIN", "external", ["A"])],
  });
  assert.equal(
    singleSupply.paths[0].endpoints[0].y,
    singleSupply.paths[0].endpoints[1].y,
    "external supply should align with the component power port",
  );
  const parallelLoads = createSystemLayout({
    ...savedRun,
    components: [createPart("A"), createPart("B")],
    rails: [createRail("VIN", "external", ["A", "B"])],
  });
  assert.equal(
    parallelLoads.components[0].x,
    parallelLoads.components[1].x,
    "externally powered parallel loads should share a column",
  );
  assertClearRoutes(parallelLoads);
  const layout = createSystemLayout({
    ...savedRun,
    components: ["A", "B", "C"].map(createPart),
    rails: [
      createRail("VIN", "external", ["A", "C"]),
      createRail("VOUT", "A", ["B"]),
    ],
    interfaces: [createInterface("CONTROL", ["A", "B", "external"])],
  });
  assert.deepEqual(layout.externalNodes.map((node) => node.kind).sort(), [
    "interface",
    "supply",
  ]);
  const supply = layout.externalNodes.find((node) => node.kind === "supply")!;
  const externalInterface = layout.externalNodes.find(
    (node) => node.kind === "interface",
  )!;
  assert.equal(supply.railId, "VIN");
  assert.equal(externalInterface.interfaceId, "CONTROL");
  assert.ok(
    layout.paths
      .find((path) => path.relationId === "rail:VIN")!
      .endpoints.some(
        (endpoint) =>
          endpoint.nodeId === supply.id && endpoint.kind === "source",
      ),
  );
  assert.ok(
    layout.paths
      .find((path) => path.relationId === "bus:CONTROL")!
      .endpoints.some(
        (endpoint) =>
          endpoint.nodeId === externalInterface.id && endpoint.kind === "data",
      ),
  );
  assertClearRoutes(layout);
});

test("missing references never invent nodes or power paths", () => {
  const layout = createSystemLayout({
    ...savedRun,
    components: ["A", "B"].map(createPart),
    rails: [
      createRail("NO_SOURCE", "missing", ["A"]),
      createRail("NO_LOAD", "A", ["missing"]),
    ],
    interfaces: [createInterface("CONTROL", ["A", "B", "missing"])],
  });
  assert.deepEqual(layout.components.map((node) => node.id).sort(), ["A", "B"]);
  assert.deepEqual(layout.externalNodes, []);
  assert.deepEqual(
    layout.paths.map((path) => path.relationId),
    ["bus:CONTROL"],
  );
  assert.deepEqual(new Set(layout.paths[0].componentIds), new Set(["A", "B"]));
  assertClearRoutes(layout);
});
