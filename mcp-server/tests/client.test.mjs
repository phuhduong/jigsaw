import assert from 'node:assert/strict';
import test from 'node:test';
import { DigiKeyClient, mapProduct, SupplierError } from '../dist/client.js';

const product = {
  Manufacturer: { Name: 'Example Semiconductor' },
  ManufacturerProductNumber: 'REG-3V3',
  ProductUrl: 'https://www.digikey.com/en/products/detail/example/reg/123',
  DatasheetUrl: 'https://example.com/reg.pdf',
  Parameters: [
    { ParameterText: 'Voltage - Input (Max)', ValueText: '16V' },
    { ParameterText: 'Voltage - Output (Min/Fixed)', ValueText: '3.3V' },
    { ParameterText: 'Package / Case', ValueText: 'SOT-23-5' },
  ],
  ProductVariations: [{
    DigiKeyProductNumber: '123-REG-CT-ND', PackageType: { Name: 'Cut Tape (CT)' },
    QuantityAvailableforPackageType: 12, MinimumOrderQuantity: 1, StandardPackage: 3000,
    StandardPricing: [{ BreakQuantity: 1, UnitPrice: '0.25' }, { BreakQuantity: 10, UnitPrice: 0.20 }],
  }, {
    DigiKeyProductNumber: '123-REG-TR-ND', PackageType: { Name: 'Tape & Reel (TR)' },
    QuantityAvailableforPackageType: 0, MinimumOrderQuantity: 3000,
    StandardPricing: [{ BreakQuantity: 3000, UnitPrice: null }],
  }],
};

test('keeps supply labels, exact identity, packaging offers and unknown values', () => {
  const result = mapProduct(product, { Site: 'CA', Currency: 'CAD' }, '2026-09-13T12:00:00Z');
  assert.equal(result.mpn, 'REG-3V3');
  assert.equal(result.package, 'SOT-23-5');
  assert.deepEqual(result.parameters[0], { name: 'Voltage - Input (Max)', value: '16V' });
  assert.deepEqual(result.parameters[1], { name: 'Voltage - Output (Min/Fixed)', value: '3.3V' });
  assert.equal(result.offers[0].currency, 'CAD');
  assert.equal(result.offers[0].url, product.ProductUrl);
  assert.equal(result.offers[0].standard_package, 3000);
  assert.equal(result.offers[0].order_multiple, null);
  assert.deepEqual(result.offers[0].price_breaks, [{ quantity: 1, unit_price: 0.25 }, { quantity: 10, unit_price: 0.2 }]);
  assert.equal(result.offers[1].stock, 0);
  assert.deepEqual(result.offers[1].price_breaks, []);
  const missing = mapProduct({ ...product, ProductUrl: undefined, DatasheetUrl: undefined, ProductVariations: [{ DigiKeyProductNumber: 'UNPRICED' }] });
  assert.equal(missing.product_url, null);
  assert.equal(missing.offers[0].stock, null);
  assert.equal(missing.offers[0].currency, null);
  assert.deepEqual(missing.offers[0].price_breaks, []);
});

test('does not turn malformed numeric fields into stock or prices', () => {
  for (const value of [' ', false, true, []]) {
    const [offer] = mapProduct({ ...product, ProductVariations: [{
      DigiKeyProductNumber: 'UNPRICED', QuantityAvailableforPackageType: value,
      MinimumOrderQuantity: value, OrderMultiple: value, StandardPackage: value,
      StandardPricing: [{ BreakQuantity: 1, UnitPrice: value }],
    }] }).offers;
    assert.equal(offer.stock, null);
    assert.equal(offer.moq, null);
    assert.equal(offer.order_multiple, null);
    assert.equal(offer.standard_package, null);
    assert.deepEqual(offer.price_breaks, []);
  }
  const [offer] = mapProduct({ ...product, ProductVariations: [{
    DigiKeyProductNumber: 'NUMERIC', QuantityAvailableforPackageType: 1.5,
    MinimumOrderQuantity: '2', StandardPricing: [{ BreakQuantity: '2', UnitPrice: '0.25' }],
  }] }).offers;
  assert.equal(offer.stock, null);
  assert.equal(offer.moq, 2);
  assert.deepEqual(offer.price_breaks, [{ quantity: 2, unit_price: 0.25 }]);
});

test('search and ProductDetails use real response shapes and shared token authentication', async () => {
  const calls = [];
  const http = async (url, options) => {
    calls.push({ url, ...options });
    const data = url.endsWith('/token')
      ? { access_token: 'local-fake-token', expires_in: 3600 }
      : url.endsWith('/keyword')
        ? { Products: [product], SearchLocaleUsed: { Site: 'US', Currency: 'USD' } }
        : { Product: product, SearchLocaleUsed: { Site: 'CA', Currency: 'CAD' } };
    return new Response(JSON.stringify(data));
  };
  const client = new DigiKeyClient('fake-id', 'fake-secret', http);
  assert.equal((await client.searchComponents('regulator'))[0].mpn, 'REG-3V3');
  assert.equal((await client.getProduct('123-REG-CT-ND', { region: 'CA', currency: 'CAD' })).offers[0].region, 'CA');
  assert.equal(calls.filter(c => c.url.endsWith('/token')).length, 1);
  assert.ok(calls[2].url.endsWith('/123-REG-CT-ND/productdetails'));
  assert.equal(calls[2].headers['X-DIGIKEY-Locale-Currency'], 'CAD');
});

test('supplier errors propagate without a fabricated part or internal retry', async () => {
  let calls = 0;
  const http = async () => {
    calls += 1;
    return new Response('{}', { status: 503, headers: { 'retry-after': '10' } });
  };
  await assert.rejects(new DigiKeyClient('fake-id', 'fake-secret', http).searchComponents('sensor'),
    error => error instanceof SupplierError && error.statusCode === 503 && error.retryAfter === '10');
  assert.equal(calls, 1);
  await assert.rejects(new DigiKeyClient('fake-id', 'fake-secret', async () => {
    throw new TypeError('local fake network failure');
  }).searchComponents('sensor'), error => error instanceof SupplierError && error.statusCode === undefined);
});

test('a rejected access token is refreshed on the next operation without retrying the failed lookup', async () => {
  let tokens = 0;
  const authorizations = [];
  const http = async (url, options) => {
    if (url.endsWith('/token')) {
      return Response.json({ access_token: `token-${++tokens}`, expires_in: 3600 });
    }
    authorizations.push(options.headers.Authorization);
    return authorizations.length === 1
      ? new Response('{}', { status: 401 })
      : Response.json({ Products: [product] });
  };
  const client = new DigiKeyClient('fake-id', 'fake-secret', http);
  await assert.rejects(client.searchComponents('sensor'),
    error => error instanceof SupplierError && error.statusCode === 401);
  assert.deepEqual(authorizations, ['Bearer token-1']);
  assert.equal((await client.searchComponents('sensor'))[0].mpn, product.ManufacturerProductNumber);
  assert.deepEqual(authorizations, ['Bearer token-1', 'Bearer token-2']);
});

test('malformed JSON and OAuth payloads remain supplier errors', async () => {
  for (const body of ['{', 'null', '{}', '{"access_token":{},"expires_in":3600}', '{"access_token":"fake"}']) {
    await assert.rejects(new DigiKeyClient('fake-id', 'fake-secret', async () => new Response(body))
      .searchComponents('sensor'), error => error instanceof SupplierError);
  }
});
