// Thin typed client for the Combuyn API.
// In dev, Vite proxies these paths to the FastAPI backend (see vite.config.ts).
// In production (Vercel), set VITE_API_BASE_URL to the Render backend URL.

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface Summary {
  frameworks: number;
  requirements: number;
  common_controls: number;
  mappings: number;
}

export interface Framework {
  id: string;
  key: string;
  name: string;
  version: string;
  authority: string;
  description: string;
  category: string;
  requirement_count: number;
}

export interface RequirementRef {
  framework_key: string;
  framework_name: string;
  citation: string;
  title: string;
  relationship_type: string;
}

export interface ControlCoverage {
  id: string;
  key: string;
  name: string;
  domain: string;
  description: string;
  frameworks_covered: string[];
  requirements: RequirementRef[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  summary: () => get<Summary>("/api/summary"),
  frameworks: () => get<Framework[]>("/api/frameworks"),
  coverage: () => get<ControlCoverage[]>("/api/coverage"),
};
