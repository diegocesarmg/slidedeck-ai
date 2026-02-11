/**
 * Typed API client for communicating with the SlideDeck AI backend.
 */

import type {
    GenerateRequest,
    GenerateResponse,
    GenerationMode,
    RefineRequest,
    RefineResponse,
} from "@/types/schema";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
    ) {
        super(message);
        this.name = "ApiError";
    }
}

async function request<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
        ...options,
    });

    if (!res.ok) {
        const body = await res.text();
        throw new ApiError(res.status, body || res.statusText);
    }

    return res.json();
}

async function requestMultipart<T>(
    path: string,
    formData: FormData,
): Promise<T> {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        method: "POST",
        body: formData,
        // Do NOT set Content-Type — browser sets it with boundary
    });

    if (!res.ok) {
        const body = await res.text();
        throw new ApiError(res.status, body || res.statusText);
    }

    return res.json();
}

// ── Public API ──────────────────────────────────────────────────────────────

export async function generatePresentation(
    data: GenerateRequest,
    file?: File,
): Promise<GenerateResponse> {
    const formData = new FormData();
    formData.append("prompt", data.prompt);

    if (data.num_slides !== undefined && data.num_slides !== null) {
        formData.append("num_slides", String(data.num_slides));
    }

    formData.append("generation_mode", data.generation_mode || "from_scratch");

    if (file) {
        formData.append("file", file);
    }

    return requestMultipart<GenerateResponse>("/api/generate", formData);
}

export async function refinePresentation(
    presentationId: string,
    instruction: string,
): Promise<RefineResponse> {
    return request<RefineResponse>(`/api/refine/${presentationId}`, {
        method: "POST",
        body: JSON.stringify({ instruction }),
    });
}

export function getDownloadUrl(presentationId: string): string {
    return `${API_BASE}/api/download/${presentationId}`;
}

export function getPreviewUrl(
    presentationId: string,
    slideIndex: number,
): string {
    return `${API_BASE}/api/preview/${presentationId}/${slideIndex}`;
}

export async function healthCheck(): Promise<{ status: string }> {
    return request<{ status: string }>("/health");
}
