function getEnv(key: string): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    return (import.meta as any).env?.[key];
  } catch {
    return undefined;
  }
}

export const API_CONFIG = {
  get useMock(): boolean {
    const envVal = getEnv("VITE_USE_MOCK");
    if (envVal !== undefined) return envVal === "true";
    // The design flow uses the real local backend unless demo mode is explicit.
    return false;
  },
  get baseUrl(): string {
    return getEnv("VITE_BACKEND_URL") || "http://localhost:3001";
  },
};
