const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  errors: Record<string, unknown> | null;

  constructor(status: number, detail: string, errors: Record<string, unknown> | null) {
    super(detail);
    this.status = status;
    this.errors = errors;
  }
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export async function apiFetch<T>(
  path: string,
  options: { method?: string; body?: unknown } = {}
): Promise<T> {
  const method = options.method || "GET";
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (UNSAFE_METHODS.has(method)) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    credentials: "include",
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  let data: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const payload = (data as { detail?: string; errors?: Record<string, unknown> }) || {};
    throw new ApiError(response.status, payload.detail || "خطایی رخ داد.", payload.errors || null);
  }

  return data as T;
}

// Django only sets the csrftoken cookie when something explicitly marks it
// "used" (e.g. django.contrib.auth.login, or this dedicated bootstrap view).
// Call once on app load so the cookie exists before any POST/PATCH/DELETE.
export async function ensureCsrfCookie(): Promise<void> {
  if (getCookie("csrftoken")) return;
  await fetch(`${API_BASE_URL}/api/auth/csrf/`, { credentials: "include" }).catch(() => undefined);
}
