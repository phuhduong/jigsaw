import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer, type ViteDevServer } from "vite";
import type { BomRow, Component } from "../app/services/api/designRunApi.ts";
import { formatMoney } from "../app/design/reportHelpers.ts";
import { savedRun } from "./fixtures/designRun.ts";

let server: ViteDevServer;
let PartsList: typeof import("../app/design/PartsList.tsx").default;
let ComponentDetail: typeof import("../app/design/ComponentDetail.tsx").default;

// Use the existing TSX/CSS loader; no browser, supplier, or model is involved.
before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    configFile: false,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true, hmr: false, watch: null },
  });
  PartsList = (await server.ssrLoadModule("/app/design/PartsList.tsx")).default;
  ComponentDetail = (
    await server.ssrLoadModule("/app/design/ComponentDetail.tsx")
  ).default;
});
after(async () => server?.close());

const component: Component = {
  id: "U1",
  name: "Controller",
  kind: "active",
  purpose: "Control the device",
  support_for: [],
  selection_reason: "",
  selection_error: null,
  product: {
    manufacturer: "Example",
    mpn: "PART-1",
    package: null,
    description: "Controller",
    datasheet_url: null,
    product_url: "https://example.com/part",
    parameters: [],
    retrieved_at: savedRun.updated_at,
  },
  document_ids: [],
  document_errors: [],
};
const row: BomRow = {
  reference_ids: [component.id],
  purposes: [component.purpose],
  manufacturer: "Example",
  mpn: "PART-1",
  package: null,
  installed_quantity: 1,
  board_quantity: 1,
  required_quantity: 1,
  order_quantity: 1,
  unit_price: 2,
  extended_price: 2,
  currency: "USD",
  supplier_sku: "SKU-1",
  purchase_url: "https://example.com/part",
  datasheet_url: null,
  stock: 10,
  moq: 1,
  order_multiple: 1,
  retrieved_at: savedRun.updated_at,
  availability: "available",
  ordering_note:
    "Quoted component prices exclude any custom-reeling/setup fee; confirm the total at checkout.",
  review_status: null,
};

test("purchasing views retain ordering caveats and label quoted prices as a parts subtotal", () => {
  const snapshot = { ...savedRun, components: [component], bom: [row] };
  const parts = renderToStaticMarkup(
    createElement(PartsList, { snapshot, onSelect: () => {} }),
  );
  const detail = renderToStaticMarkup(
    createElement(ComponentDetail, { snapshot, componentId: component.id }),
  );
  for (const report of [parts, detail])
    assert.ok(report.includes(row.ordering_note));
  assert.match(parts, /Parts subtotal/);
  assert.match(parts, /Shipping, tax, and unquoted fees are excluded/);
});

test("unquoted prices remain partial while a quoted zero is a known subtotal", () => {
  const renderParts = (price: number | null) =>
    renderToStaticMarkup(
      createElement(PartsList, {
        snapshot: {
          ...savedRun,
          components: [component],
          bom: [
            { ...row, unit_price: price, extended_price: price, ordering_note: "" },
          ],
        },
        onSelect: () => {},
      }),
    );
  const unknown = renderParts(null);
  assert.match(unknown, /Partial parts subtotal/);
  assert.match(unknown, /Not quoted/);
  const zero = renderParts(0);
  assert.match(zero, /Parts subtotal/);
  assert.ok(zero.includes(formatMoney(0, "USD")));
  assert.doesNotMatch(zero, /Partial parts subtotal|Not quoted|bom-ordering-note/);
});
