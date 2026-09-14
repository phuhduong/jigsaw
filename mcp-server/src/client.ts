/** DigiKey OAuth and catalog lookup. Engineering interpretation stays in Python. */
import axios, { AxiosInstance } from 'axios';
import {
  DigiKeyDetailsResponse, DigiKeyLocale, DigiKeyProduct, DigiKeySearchResponse,
  DigiKeyTokenResponse, SupplierProduct,
} from './types.js';

export class SupplierError extends Error {
  constructor(message: string, public statusCode?: number, public retryAfter?: string) {
    super(message);
    this.name = 'SupplierError';
  }
}

export interface LookupOptions {
  region?: string;
  currency?: string;
  /** Absolute deadline includes the caller's MCP initialization and transport time. */
  deadlineMs?: number;
}

function numberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null;
  const number = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function positiveInteger(value: unknown): number | null {
  const number = numberOrNull(value);
  return number !== null && Number.isInteger(number) && number > 0 ? number : null;
}

function providerUrl(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return ['http:', 'https:'].includes(new URL(value).protocol) ? value : null;
  } catch {
    return null;
  }
}

/** Pure normalization shared by keyword search and ProductDetails. */
export function mapProduct(
  product: DigiKeyProduct,
  locale: DigiKeyLocale = {},
  retrievedAt = new Date().toISOString(),
): SupplierProduct {
  if (!product?.ManufacturerProductNumber || !product.Manufacturer?.Name) {
    throw new SupplierError('DigiKey returned a product without exact manufacturer/MPN identity');
  }
  const parameters = (product.Parameters ?? []).map(p => ({ name: p.ParameterText, value: p.ValueText }));
  const productUrl = providerUrl(product.ProductUrl);
  return {
    manufacturer: product.Manufacturer.Name,
    mpn: product.ManufacturerProductNumber,
    package: parameters.find(p => p.name === 'Package / Case')?.value
      ?? parameters.find(p => p.name === 'Supplier Device Package')?.value ?? '',
    description: product.Description?.DetailedDescription || product.Description?.ProductDescription || '',
    datasheet_url: providerUrl(product.DatasheetUrl),
    product_url: productUrl,
    parameters,
    offers: (product.ProductVariations ?? [])
      .filter(v => v.DigiKeyProductNumber && !v.MarketPlace)
      .map(v => ({
        sku: v.DigiKeyProductNumber!,
        url: providerUrl(v.ProductUrl) ?? productUrl,
        currency: locale.Currency ?? null,
        region: locale.Site ?? null,
        packaging: v.PackageType?.Name ?? null,
        stock: numberOrNull(v.QuantityAvailableforPackageType),
        moq: positiveInteger(v.MinimumOrderQuantity),
        // StandardPackage is the manufacturer's pack size, not an order multiple.
        order_multiple: positiveInteger(v.OrderMultiple),
        standard_package: positiveInteger(v.StandardPackage),
        price_breaks: (v.StandardPricing ?? [])
          .filter(p => positiveInteger(p.BreakQuantity) !== null && numberOrNull(p.UnitPrice) !== null)
          .map(p => ({ quantity: p.BreakQuantity, unit_price: numberOrNull(p.UnitPrice)! }))
          .sort((a, b) => a.quantity - b.quantity),
        retrieved_at: retrievedAt,
      })),
    retrieved_at: retrievedAt,
  };
}

export class DigiKeyClient {
  private accessToken: string | null = null;
  private tokenExpiresAt = 0;

  constructor(
    private clientId: string,
    private clientSecret: string,
    private http: AxiosInstance = axios.create(),
  ) {
    if (!clientId || !clientSecret) throw new SupplierError('DigiKey credentials are required');
  }

  private async getAccessToken(signal: AbortSignal): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExpiresAt - 30000) return this.accessToken;
    const response = await this.http.post<DigiKeyTokenResponse>(
      'https://api.digikey.com/v1/oauth2/token',
      new URLSearchParams({ grant_type: 'client_credentials', client_id: this.clientId, client_secret: this.clientSecret }),
      { signal, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
    );
    if (!response.data.access_token) throw new SupplierError('DigiKey returned no access token');
    this.accessToken = response.data.access_token;
    this.tokenExpiresAt = Date.now() + response.data.expires_in * 1000;
    return this.accessToken;
  }

  private async lookup<T>(
    options: LookupOptions,
    operation: (signal: AbortSignal, headers: Record<string, string>) => Promise<T>,
  ): Promise<T> {
    const remaining = (options.deadlineMs ?? Date.now() + 20000) - Date.now();
    if (remaining <= 0) throw new SupplierError('Supplier operation deadline exceeded');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), remaining);
    try {
      const token = await this.getAccessToken(controller.signal);
      return await operation(controller.signal, {
        Authorization: `Bearer ${token}`,
        'X-DIGIKEY-Client-Id': this.clientId,
        'X-DIGIKEY-Locale-Site': options.region ?? 'US',
        'X-DIGIKEY-Locale-Currency': options.currency ?? 'USD',
        'X-DIGIKEY-Locale-Language': 'en',
      });
    } catch (error) {
      if (controller.signal.aborted) throw new SupplierError('Supplier operation deadline exceeded');
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401) this.accessToken = null;
        throw new SupplierError(
          status ? `DigiKey request failed (HTTP ${status})` : 'Could not reach DigiKey',
          status, error.response?.headers['retry-after'],
        );
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  async searchComponents(query: string, limit = 3, options: LookupOptions = {}): Promise<SupplierProduct[]> {
    return this.lookup(options, async (signal, headers) => {
      const response = await this.http.post<DigiKeySearchResponse>(
        'https://api.digikey.com/products/v4/search/keyword',
        { Keywords: query, Limit: limit, Offset: 0, ExcludeMarketPlaceProducts: true },
        { signal, headers },
      );
      if (!Array.isArray(response.data.Products)) throw new SupplierError('Invalid DigiKey search response');
      return response.data.Products.map(p => mapProduct(p, response.data.SearchLocaleUsed));
    });
  }

  async getProduct(productNumber: string, options: LookupOptions = {}): Promise<SupplierProduct> {
    return this.lookup(options, async (signal, headers) => {
      const response = await this.http.get<DigiKeyDetailsResponse>(
        `https://api.digikey.com/products/v4/search/${encodeURIComponent(productNumber)}/productdetails`,
        { signal, headers },
      );
      return mapProduct(response.data.Product, response.data.SearchLocaleUsed);
    });
  }
}
