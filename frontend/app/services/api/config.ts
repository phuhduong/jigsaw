export const API_CONFIG = {
  // The legacy environment flag disables generation; it does not provide mock data.
  generationDisabled: import.meta.env?.VITE_USE_MOCK === "true",
  baseUrl: import.meta.env?.VITE_BACKEND_URL || "http://localhost:3001",
};
