interface SupplierOffer {
  sku: string;
  url: string | null;
  currency: string | null;
  region: string | null;
  packaging: string | null;
  stock: number | null;
  moq: number | null;
  order_multiple: number | null;
  standard_package: number | null;
  price_breaks: Array<{ quantity: number; unit_price: number }>;
  retrieved_at: string;
}

interface SupplierProduct {
  manufacturer: string;
  mpn: string;
  package: string;
  description: string;
  datasheet_url: string | null;
  product_url: string | null;
  parameters: Array<{ name: string; value: string }>;
  offers: SupplierOffer[];
  retrieved_at: string;
}

interface DigiKeyLocale {
  Site?: string;
  Currency?: string;
}

interface DigiKeyVariation {
  DigiKeyProductNumber?: string;
  ProductUrl?: string;
  PackageType?: { Name?: string };
  QuantityAvailableforPackageType?: number | null;
  MinimumOrderQuantity?: number | null;
  OrderMultiple?: number | null;
  StandardPackage?: number | null;
  StandardPricing?: Array<{ BreakQuantity: number; UnitPrice?: number | string | null }>;
  MarketPlace?: boolean;
}

interface DigiKeyProduct {
  ManufacturerProductNumber?: string;
  Manufacturer?: { Name?: string };
  Description?: { ProductDescription?: string; DetailedDescription?: string };
  DatasheetUrl?: string;
  ProductUrl?: string;
  Parameters?: Array<{ ParameterText: string; ValueText: string }>;
  ProductVariations?: DigiKeyVariation[];
}

export class SupplierError extends Error {
  constructor(message: string, public statusCode?: number, public retryAfter?: string) {
    super(message);
    this.name = 'SupplierError';
  }
}

interface LookupOptions {
  region?: string;
  currency?: string;
  /** Absolute deadline includes the caller's MCP initialization and transport time. */
  deadlineMs?: number;
}

function numberOrNull(value: unknown): number | null {
  if (typeof value !== 'number' && (typeof value !== 'string' || value.trim() === '')) return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function integerOrNull(value: unknown, minimum = 0): number | null {
  const number = numberOrNull(value);
  return number !== null && Number.isSafeInteger(number) && number >= minimum ? number : null;
}

function providerUrl(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return ['http:', 'https:'].includes(new URL(value).protocol) ? value : null;
  } catch {
    return null;
  }
}

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
        stock: integerOrNull(v.QuantityAvailableforPackageType),
        moq: integerOrNull(v.MinimumOrderQuantity, 1),
        // StandardPackage is the manufacturer's pack size, not an order multiple.
        order_multiple: integerOrNull(v.OrderMultiple, 1),
        standard_package: integerOrNull(v.StandardPackage, 1),
        price_breaks: (v.StandardPricing ?? [])
          .flatMap(p => {
            const quantity = integerOrNull(p.BreakQuantity, 1);
            const unitPrice = numberOrNull(p.UnitPrice);
            return quantity === null || unitPrice === null ? [] : [{ quantity, unit_price: unitPrice }];
          })
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
    private http: typeof fetch = fetch,
  ) {}

  private async request<T>(url: string, options: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await this.http(url, options);
    } catch {
      throw new SupplierError('Could not reach DigiKey');
    }
    if (!response.ok) {
      if (response.status === 401) this.accessToken = null;
      // Release the connection without replacing the provider's HTTP failure.
      await response.body?.cancel().catch(() => {});
      throw new SupplierError(
        `DigiKey request failed (HTTP ${response.status})`,
        response.status, response.headers.get('retry-after') ?? undefined,
      );
    }
    try {
      const data: unknown = await response.json();
      if (data === null || typeof data !== 'object' || Array.isArray(data)) {
        throw new Error('Expected an object');
      }
      return data as T;
    } catch {
      throw new SupplierError('Invalid DigiKey response');
    }
  }

  private async getAccessToken(signal: AbortSignal): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExpiresAt - 30000) return this.accessToken;
    const response = await this.request<{ access_token: string; expires_in: number }>(
      'https://api.digikey.com/v1/oauth2/token', {
        method: 'POST', signal,
        body: new URLSearchParams({ grant_type: 'client_credentials', client_id: this.clientId, client_secret: this.clientSecret }),
        headers: { Accept: 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' },
      });
    if (typeof response.access_token !== 'string' || !response.access_token.trim()
      || !Number.isFinite(response.expires_in) || response.expires_in <= 0) {
      throw new SupplierError('Invalid DigiKey access token response');
    }
    this.accessToken = response.access_token;
    this.tokenExpiresAt = Date.now() + response.expires_in * 1000;
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
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
        'X-DIGIKEY-Client-Id': this.clientId,
        'X-DIGIKEY-Locale-Site': options.region ?? 'US',
        'X-DIGIKEY-Locale-Currency': options.currency ?? 'USD',
        'X-DIGIKEY-Locale-Language': 'en',
      });
    } catch (error) {
      if (controller.signal.aborted) throw new SupplierError('Supplier operation deadline exceeded');
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  async searchComponents(query: string, limit = 3, options: LookupOptions = {}): Promise<SupplierProduct[]> {
    return this.lookup(options, async (signal, headers) => {
      const response = await this.request<{ Products: DigiKeyProduct[]; SearchLocaleUsed?: DigiKeyLocale }>(
        'https://api.digikey.com/products/v4/search/keyword',
        { method: 'POST', signal, headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ Keywords: query, Limit: limit, Offset: 0, ExcludeMarketPlaceProducts: true }) },
      );
      if (!Array.isArray(response.Products)) throw new SupplierError('Invalid DigiKey search response');
      return response.Products.map(p => mapProduct(p, response.SearchLocaleUsed));
    });
  }

  async getProduct(productNumber: string, options: LookupOptions = {}): Promise<SupplierProduct> {
    return this.lookup(options, async (signal, headers) => {
      const response = await this.request<{ Product: DigiKeyProduct; SearchLocaleUsed?: DigiKeyLocale }>(
        `https://api.digikey.com/products/v4/search/${encodeURIComponent(productNumber)}/productdetails`,
        { signal, headers },
      );
      return mapProduct(response.Product, response.SearchLocaleUsed);
    });
  }
}
