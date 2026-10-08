import assert from "node:assert/strict";
import { test } from "node:test";
import type { Finding } from "../app/services/api/designRunApi.ts";
import {
  formatMoney,
  getCompatibilityFailures,
  getSubjectComponentIds,
  isSelectedProduct,
} from "../app/design/reportHelpers.ts";
import { createPart, savedRun } from "./fixtures/designRun.ts";

test("review shows only this revision's findings and never revives discarded source errors", () => {
  const finding: Finding = {
    id: "current",
    revision: 2,
    area: "power",
    method: "model_review",
    kind: "check",
    status: "fail",
    subject_ids: ["U1"],
    evidence_ids: [],
    document_id: null,
    explanation: "Supply exceeds the operating range.",
    remedy: "",
  };
  const old: Finding = {
    ...finding,
    id: "old",
    revision: 1,
  };
  assert.deepEqual(
    getCompatibilityFailures({
      ...savedRun,
      revision: 2,
      findings: [old, finding],
      evidence_errors: [old],
    }),
    [finding],
  );
});

test("reports show explicit current failures, keeping diagnostics and active reviews quiet", () => {
  const failure: Finding = {
    id: "power",
    revision: 1,
    area: "power",
    method: "code",
    kind: "check",
    status: "fail",
    subject_ids: ["U1"],
    evidence_ids: [],
    document_id: null,
    explanation: "Supply exceeds the operating range.",
    remedy: "Select a compatible supply.",
  };
  const snapshot = {
    ...savedRun,
    findings: [
      failure,
      { ...failure, status: "unknown" as const },
      { ...failure, area: "evidence" as const },
      { ...failure, kind: "guidance" as const },
    ],
  };
  assert.deepEqual(getCompatibilityFailures(snapshot), [failure]);
  assert.deepEqual(
    getCompatibilityFailures({ ...snapshot, lifecycle: "running" }),
    [],
  );
});

test("shared support links retain both source parents and fulfillment placements", () => {
  const snapshot = {
    ...savedRun,
    components: [createPart("U1"), createPart("U2"), createPart("R1")],
    interfaces: [
      {
        id: "I2C",
        protocol: "I2C",
        configuration: "",
        evidence_ids: [],
        endpoints: ["U1", "U2", "external"].map((component_id) => ({
          component_id,
          address: null,
          assumption_id: null,
        })),
      },
    ],
    source_support_needs: [
      {
        id: "pullup",
        purpose: "Pull-up",
        parent_ids: ["I2C"],
        necessity: "required" as const,
        connection_requirement: "4.7k",
        evidence_ids: [],
        document_id: null,
      },
    ],
    support_needs: [
      {
        id: "pullup",
        purpose: "Pull-up",
        parent_ids: ["U1"],
        necessity: "required" as const,
        status: "unresolved" as const,
        component_ids: ["R1"],
        connections: "",
        evidence_ids: [],
        explanation: "",
      },
    ],
  };
  assert.deepEqual(getSubjectComponentIds(snapshot, "pullup"), [
    "R1",
    "U1",
    "U2",
  ]);
  assert.deepEqual(getSubjectComponentIds(snapshot, "missing"), []);
});

test("unknown pricing remains distinct from a quoted zero", () => {
  assert.equal(formatMoney(null, "USD"), "Unknown");
  assert.notEqual(formatMoney(0, "USD"), "Unknown");
  assert.match(formatMoney(0, "USD"), /^USD /);
});

test("a selected part needs both manufacturer and MPN, matching the backend BOM", () => {
  const product = {
    manufacturer: "Example",
    mpn: "PART-1",
    package: null,
    description: "",
    datasheet_url: null,
    product_url: null,
    parameters: [],
    retrieved_at: "2026-09-29T12:00:00Z",
  };
  assert.equal(isSelectedProduct(product), true);
  assert.equal(isSelectedProduct(null), false);
  assert.equal(isSelectedProduct({ ...product, manufacturer: "  " }), false);
  assert.equal(isSelectedProduct({ ...product, mpn: "" }), false);
});
