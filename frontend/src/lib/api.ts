/**
 * Typed API client — all backend calls go through here.
 * Base URL proxied via Next.js rewrites so the frontend never calls the backend directly.
 */

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    let code = "UNKNOWN_ERROR";
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      code = body?.error?.code ?? body?.detail ?? code;
      message = body?.error?.message ?? body?.detail ?? message;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---- Types ----------------------------------------------------------------

export interface Customer {
  id: string;
  label: string;
}

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  customer: string;
  status: DocumentStatus;
  error_message: string | null;
  node_count: number;
  title_count: number;
  requirement_count: number;
  doc_title: string | null;
  doc_reference: string | null;
  doc_author: string | null;
  doc_company: string | null;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

export type ApplicabilityValue = "NA" | "A" | "A/M" | "TBC" | "T";
export type ConformityValue = "NA" | "C" | "C TBC" | "PC" | "NC" | "TBC" | "T";

export interface Node {
  id: string;
  document_id: string;
  order: number;
  type: "title" | "requirement";
  section: string | null;
  req_id: string | null;
  title: string;
  description: string;
  applicability: ApplicabilityValue;
  conformity: ConformityValue;
  updated_by: string | null;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: Record<string, unknown>;
}

// ---- API calls ------------------------------------------------------------

export const api = {
  customers: {
    list: (): Promise<{ data: Customer[] }> =>
      request("/customers"),
  },

  documents: {
    list: (params?: { limit?: number; offset?: number }): Promise<PaginatedResponse<Document>> => {
      const qs = new URLSearchParams();
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      if (params?.offset !== undefined) qs.set("offset", String(params.offset));
      return request(`/documents?${qs}`);
    },

    get: (id: string): Promise<Document> => request(`/documents/${id}`),

    delete: (id: string): Promise<void> =>
      request(`/documents/${id}`, { method: "DELETE" }),

    upload: async (file: File, customer: string): Promise<Document> => {
      const form = new FormData();
      form.append("file", file);
      form.append("customer", customer);
      const res = await fetch(`${BASE}/documents`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new ApiError(res.status, "UPLOAD_ERROR", body?.detail ?? "Upload failed");
      }
      return res.json() as Promise<Document>;
    },
  },

  nodes: {
    list: (
      documentId: string,
      params?: { limit?: number; offset?: number },
    ): Promise<PaginatedResponse<Node>> => {
      const qs = new URLSearchParams();
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      if (params?.offset !== undefined) qs.set("offset", String(params.offset));
      return request(`/documents/${documentId}/nodes?${qs}`);
    },

    update: (
      nodeId: string,
      body: { applicability?: ApplicabilityValue; conformity?: ConformityValue },
    ): Promise<Node> =>
      request(`/nodes/${nodeId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
  },
};
