/** The supplier contract separates physical parts from packaging offers. */
export interface SupplierOffer {
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

export interface SupplierProduct {
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

export interface DigiKeyTokenResponse {
  access_token: string;
  expires_in: number;
}

export interface DigiKeyLocale {
  Site?: string;
  Currency?: string;
}

export interface DigiKeyVariation {
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

export interface DigiKeyProduct {
  ManufacturerProductNumber?: string;
  Manufacturer?: { Name?: string };
  Description?: { ProductDescription?: string; DetailedDescription?: string };
  DatasheetUrl?: string;
  ProductUrl?: string;
  Parameters?: Array<{ ParameterText: string; ValueText: string }>;
  ProductVariations?: DigiKeyVariation[];
}

export interface DigiKeySearchResponse {
  Products: DigiKeyProduct[];
  SearchLocaleUsed?: DigiKeyLocale;
}

export interface DigiKeyDetailsResponse {
  Product: DigiKeyProduct;
  SearchLocaleUsed?: DigiKeyLocale;
}
