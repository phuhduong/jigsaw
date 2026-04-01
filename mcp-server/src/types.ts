/**
 * TypeScript type definitions for DigiKey MCP Server
 */

/**
 * PartObject interface matching frontend types.ts
 */
export interface PartObject {
  mpn: string; // Manufacturer Part Number
  manufacturer: string;
  description: string;
  price: number;
  currency?: string; // Default: "USD"
  voltage?: string; // Voltage range (e.g., "3.0V ~ 3.6V")
  package?: string; // Package type (e.g., "32-QFN")
  interfaces?: string[]; // Array of interfaces (e.g., ["I2C", "SPI", "UART", "WiFi"])
  datasheet?: string; // URL to datasheet
  quantity?: number; // Default: 1
}

/**
 * DigiKey OAuth2 token response
 */
export interface DigiKeyTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * DigiKey Product Parameter
 */
export interface DigiKeyParameter {
  ParameterId: number;
  ParameterText: string;
  ValueId: string;
  ValueText: string;
}

/**
 * DigiKey Product from keyword search response
 */
export interface DigiKeyProduct {
  DigiKeyPartNumber: string;
  ManufacturerProductNumber: string;
  Manufacturer: {
    Name: string;
  };
  Description: {
    ProductDescription: string;
    DetailedDescription?: string;
  };
  UnitPrice: number;
  Currency?: string;
  DatasheetUrl?: string;
  Parameters: DigiKeyParameter[];
  ProductUrl?: string;
}

/**
 * DigiKey keyword search response
 */
export interface DigiKeySearchResponse {
  Products: DigiKeyProduct[];
  ProductsCount: number;
  ExactManufacturerProductsCount: number;
}
