export interface PartObject {
  mpn: string;
  manufacturer: string;
  description: string;
  price: number;
  currency?: string;
  voltage?: string;
  package?: string;
  interfaces?: string[];
  datasheet?: string;
  quantity?: number;
}
