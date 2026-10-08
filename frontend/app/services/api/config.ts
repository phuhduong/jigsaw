export const API_CONFIG = {
  generationDisabled: import.meta.env?.VITE_DISABLE_GENERATION === "true",
  baseUrl: import.meta.env?.VITE_BACKEND_URL || "http://localhost:3001",
};
