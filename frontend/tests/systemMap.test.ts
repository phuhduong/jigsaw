import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  Component,
  DesignSnapshot,
  Rail,
} from "../app/services/api/designRunApi.ts";
import { buildSystemMap } from "../app/design/systemRelationships.ts";
import { createSystemLayout } from "../app/design/systemLayout.ts";
import {
  getComponentRole,
  getComponentTitle,
} from "../app/design/componentPresentation.ts";
import { savedRun } from "./fixtures/designRun.ts";

function createPart(id: string, supportFor: string[] = []): Component {
  return {
    id,
    name: id,
    kind: "active",
    purpose: "Fixture part",
    support_for: supportFor,
    selection_reason: "",
    selection_error: null,
    document_ids: [],
    document_errors: [],
    product: {
      mpn: "same-part",
      manufacturer: "Fixture",
      package: null,
      description: "",
      datasheet_url: null,
      product_url: null,
      parameters: [],
      retrieved_at: "2026-09-29T12:00:00Z",
    },
  };
}
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

test("concise titles distinguish a component's function from the parts it serves", () => {
  const controller = {
    ...createPart("U1"),
    purpose: "Main microcontroller with Wi-Fi and Bluetooth",
  };
  const regulator = {
    ...createPart("U3"),
    purpose: "3.3V LDO voltage regulator to power the MCU and sensor",
  };
  const sensor = {
    ...createPart("U2"),
    purpose: "High-accuracy digital temperature and humidity sensor",
  };
  assert.deepEqual([controller, regulator, sensor].map(getComponentTitle), [
    "Wireless controller",
    "Voltage regulator",
    "Temperature & humidity",
  ]);
  assert.equal(
    getComponentTitle({
      ...controller,
      purpose: "Controller for an external Wi-Fi module",
    }),
    "Controller",
  );
  assert.equal(
    getComponentTitle({
      ...regulator,
      purpose: "Voltage regulator for a battery charger",
    }),
    "Voltage regulator",
  );
  assert.equal(
    getComponentTitle({
      ...controller,
      purpose:
        "Main controller assembly providing Wi-Fi, Bluetooth LE, and processing capabilities.",
    }),
    "Wireless controller",
  );
  assert.equal(
    getComponentRole({
      ...createPart("C1"),
      kind: "passive",
      purpose: "Microcontroller decoupling",
    }),
    "other",
  );
  assert.equal(
    getComponentTitle({
      ...createPart("X1"),
      purpose: "Unrecognized function",
    }),
    "X1",
  );
});

test("action-led descriptions stay concise and preserve the component role", () => {
  const controller = {
    ...createPart("U2"),
    name: "same-part",
    purpose:
      "Controls the system, reads I2C sensors, and reports data over Bluetooth LE.",
  };
  assert.equal(getComponentRole(controller), "controller");
  assert.equal(getComponentTitle(controller), "Wireless controller");
  assert.equal(
    getComponentTitle({
      ...createPart("U1"),
      purpose:
        "Regulates incoming 5V from USB-C down to 3.3V for the MCU and sensors.",
      product: null,
    }),
    "Voltage regulator",
  );
  assert.equal(
    getComponentTitle({
      ...createPart("U3"),
      purpose: "Measures temperature at the first location.",
    }),
    "Temperature sensor",
  );
  assert.equal(
    getComponentTitle({
      ...createPart("X1"),
      name: "same-part",
      purpose:
        "Provides an unfamiliar function with several implementation details that belong in the part details.",
    }),
    "Component",
  );
  const tiltController = {
    ...controller,
    purpose:
      "Monitors the tilt sensor and drives the buzzer when the threshold is exceeded.",
    product: {
      ...controller.product!,
      description: "ARM Cortex-M0+ SAM D10C Microcontroller IC",
    },
  };
  assert.equal(getComponentTitle(tiltController), "Controller");
  assert.equal(
    getComponentTitle({
      ...createPart("U2"),
      purpose: "Measures ambient temperature and relative humidity.",
    }),
    "Temperature & humidity",
  );
  assert.equal(
    getComponentTitle({
      ...createPart("BT2"),
      purpose:
        "Primary 3V coin cell battery supplying power via battery holder BT1.",
    }),
    "Battery",
  );
  assert.equal(
    getComponentTitle({
      ...createPart("LS1"),
      purpose: "Sounds the audible tilt alarm.",
      product: null,
    }),
    "Audible alarm",
  );
});

test("processing and environmental measurement descriptions select their functional illustrations", () => {
  const controller = {
    ...createPart("U1"),
    purpose:
      "Provides main processing, Wi-Fi, and Bluetooth (BLE) functionality.",
  };
  const sensor = {
    ...createPart("U2"),
    purpose:
      "Measures environmental temperature and humidity accurately via I2C.",
  };
  assert.deepEqual([controller, sensor].map(getComponentRole), [
    "controller",
    "sensor",
  ]);
  assert.deepEqual([controller, sensor].map(getComponentTitle), [
    "Wireless controller",
    "Temperature & humidity",
  ]);
});

test("placements stay distinct; power is directed and a shared bus uses a common junction", () => {
  const snapshot: DesignSnapshot = {
    ...savedRun,
    components: [createPart("U1"), createPart("U2"), createPart("U3")],
    rails: [
      {
        ...createRail("VIN", "external", ["U1"]),
        voltage_min: {
          value: 4.75,
          unit: "V",
          basis: "min",
          evidence_ids: ["unbound"],
          assumption_id: null,
        },
      },
      createRail("3V3", "U1", ["U2", "U3"]),
    ],
    interfaces: [
      {
        id: "BUS1",
        protocol: "I2C",
        configuration: "100 kHz",
        evidence_ids: [],
        endpoints: ["U1", "U2", "U3"].map((component_id) => ({
          component_id,
          address: null,
          assumption_id: null,
        })),
      },
    ],
  };
  const map = buildSystemMap(snapshot);
  const layout = createSystemLayout(snapshot);
  assert.deepEqual(
    map.core.map((part) => part.id),
    ["U1", "U2", "U3"],
  );
  assert.equal(map.hasPowerConnections, true);
  assert.deepEqual(
    layout.paths
      .filter((path) => path.kind === "power")
      .map((path) => path.endpoints.map((endpoint) => endpoint.nodeId)),
    [
      ["rail:VIN", "U1"],
      ["U1", "U2", "U3"],
    ],
  );
  assert.deepEqual(
    layout.paths
      .filter((path) => path.kind === "interface")
      .map((path) => path.componentIds),
    [["U1", "U2", "U3"]],
  );
  assert.equal(map.externalRails[0].id, "VIN");
  assert.deepEqual(
    map.powerColumns.map((column) => column.map((part) => part.id)),
    [["U1"], ["U2", "U3"]],
  );
});

test("support is grouped by recorded parents; supply sources stay on the main map", () => {
  const map = buildSystemMap({
    ...savedRun,
    components: [
      createPart("U1"),
      createPart("U2", ["U1"]),
      createPart("C1", ["U1"]),
      createPart("C2"),
    ],
    rails: [createRail("3V3", "U2", ["U1", "C1"])],
    support_needs: [
      {
        id: "S1",
        parent_ids: ["U1"],
        component_ids: ["C2"],
        necessity: "required",
        status: "satisfied",
        purpose: "Bypass",
        connections: "",
        explanation: "",
        evidence_ids: [],
      },
    ],
  });
  assert.deepEqual(
    map.core.map((part) => part.id),
    ["U1", "U2"],
  );
  assert.deepEqual(
    map.supportGroups.map((group) => [
      group.parentIds,
      group.components.map((part) => part.id),
    ]),
    [[["U1"], ["C1", "C2"]]],
  );
  assert.equal(map.hasPowerConnections, true);
});

test("requirement-only support references keep primary parts visible while explicit support stays grouped", () => {
  const map = buildSystemMap({
    ...savedRun,
    components: [
      createPart("U1"),
      createPart("U2", ["REQ-1"]),
      createPart("J1", ["REQ-3"]),
      createPart("U3", ["req:REQ-3"]),
      createPart("C1", ["REQ-3"]),
    ],
    requirements: [
      {
        id: "req:REQ-1",
        clause: "Sensor",
        description: "Measure temperature",
        component_ids: ["U2"],
      },
      {
        id: "req:REQ-3",
        clause: "USB-C power",
        description: "Power the device",
        component_ids: ["J1", "U3", "C1"],
      },
    ],
    support_needs: [
      {
        id: "S1",
        parent_ids: ["U3"],
        component_ids: ["C1"],
        necessity: "required",
        status: "satisfied",
        purpose: "Bypass",
        connections: "",
        explanation: "",
        evidence_ids: [],
      },
    ],
  });
  assert.deepEqual(
    map.core.map((part) => part.id),
    ["U1", "U2", "J1", "U3"],
  );
  assert.deepEqual(
    map.supportGroups.map((group) => [
      group.parentIds,
      group.components.map((part) => part.id),
    ]),
    [[["U3"], ["C1"]]],
  );
});

test("missing references never become invented components or edges", () => {
  const unresolved = {
    ...createPart("U1"),
    product: null,
    selection_error: "No product matched",
  };
  const map = buildSystemMap({
    ...savedRun,
    components: [unresolved],
    rails: [
      createRail("VIN", "missing", ["U1"]),
      createRail("VOUT", "U1", ["missing"]),
    ],
  });
  assert.deepEqual(map.core, [unresolved]);
  assert.equal(map.hasPowerConnections, false);
  assert.deepEqual(buildSystemMap(savedRun).core, []);
});

test("power layout follows source, regulator, and parallel loads regardless of plan order", () => {
  const map = buildSystemMap({
    ...savedRun,
    components: [
      createPart("U1"),
      createPart("U2"),
      createPart("J1"),
      createPart("U3"),
    ],
    rails: [
      createRail("5V", "J1", ["U3"]),
      createRail("3V3", "U3", ["U1", "U2"]),
    ],
  });
  assert.deepEqual(
    map.powerColumns.map((column) => column.map((part) => part.id)),
    [["J1"], ["U3"], ["U1", "U2"]],
  );
  const cycle = buildSystemMap({
    ...savedRun,
    components: [createPart("U1"), createPart("U2")],
    rails: [createRail("A", "U1", ["U2"]), createRail("B", "U2", ["U1"])],
  });
  assert.deepEqual(
    cycle.powerColumns.map((column) => column.map((part) => part.id)),
    [["U1", "U2"]],
  );
});
