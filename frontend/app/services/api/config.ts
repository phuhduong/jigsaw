export const API_CONFIG = {
  // Retain the existing live-generation off switch; it never fabricates a BOM.
  useMock: import.meta.env?.VITE_USE_MOCK === "true",
  baseUrl: import.meta.env?.VITE_BACKEND_URL || "http://localhost:3001",
};
