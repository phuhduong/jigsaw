import assert from 'node:assert/strict';
import test from 'node:test';
import axios from 'axios';
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

test('search and ProductDetails use real response shapes and shared token authentication', async () => {
  const calls = [];
  const http = axios.create({ adapter: async config => {
    calls.push(config);
    const data = config.url.endsWith('/token')
      ? { access_token: 'local-fake-token', expires_in: 3600 }
      : config.url.endsWith('/keyword')
        ? { Products: [product], SearchLocaleUsed: { Site: 'US', Currency: 'USD' } }
        : { Product: product, SearchLocaleUsed: { Site: 'CA', Currency: 'CAD' } };
    return { data, status: 200, statusText: 'OK', headers: {}, config };
  } });
  const client = new DigiKeyClient('fake-id', 'fake-secret', http);
  assert.equal((await client.searchComponents('regulator'))[0].mpn, 'REG-3V3');
  assert.equal((await client.getProduct('123-REG-CT-ND', { region: 'CA', currency: 'CAD' })).offers[0].region, 'CA');
  assert.equal(calls.filter(c => c.url.endsWith('/token')).length, 1);
  assert.ok(calls[2].url.endsWith('/123-REG-CT-ND/productdetails'));
  assert.equal(calls[2].headers['X-DIGIKEY-Locale-Currency'], 'CAD');
});

test('supplier errors propagate without a fabricated part or internal retry', async () => {
  let calls = 0;
  const http = axios.create({ adapter: async config => {
    calls += 1;
    throw new axios.AxiosError('unavailable', 'ERR_BAD_RESPONSE', config, undefined, {
      status: 503, data: {}, headers: { 'retry-after': '10' }, config, statusText: 'Unavailable',
    });
  } });
  await assert.rejects(new DigiKeyClient('fake-id', 'fake-secret', http).searchComponents('sensor'),
    error => error instanceof SupplierError && error.statusCode === 503 && error.retryAfter === '10');
  assert.equal(calls, 1);
});
