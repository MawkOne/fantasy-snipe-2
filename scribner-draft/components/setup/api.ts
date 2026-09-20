import type { AdminSession } from "./types";

const SESSION_KEY = "fantasy-snipe:scribner-admin-session";

export class ApiError extends Error {
  status: number;
  data: Record<string, unknown>;

  constructor(message: string, status: number, data: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function errorMessage(data: Record<string, unknown>, fallback: string): string {
  const direct = data.error ?? data.message;
  const details = asRecord(data.details);
  const errors = data.issues ?? details.issues ?? data.errors;
  const messages = Array.isArray(errors)
    ? errors
        .map((entry) => {
          if (typeof entry === "string") return entry;
          const record = asRecord(entry);
          return typeof record.message === "string" ? record.message : "";
        })
        .filter(Boolean)
    : [];

  if (typeof direct === "string" && direct.trim()) {
    return messages.length ? `${direct} ${messages.join(" ")}` : direct;
  }
  if (messages.length) return messages.join(" ");
  return fallback;
}

export async function postJson(
  url: string,
  body: Record<string, unknown>,
  fallbackError: string,
): Promise<Record<string, unknown>> {
  let response: Response;

  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      "Could not reach the draft service. Check your connection and try again.",
      0,
      {},
    );
  }

  const data = asRecord(await response.json().catch(() => ({})));
  if (!response.ok) {
    throw new ApiError(errorMessage(data, fallbackError), response.status, data);
  }

  return data;
}

export function readAdminSession(): AdminSession | null {
  try {
    const value = window.localStorage.getItem(SESSION_KEY);
    if (!value) return null;
    const parsed = asRecord(JSON.parse(value) as unknown);
    if (
      typeof parsed.roomId !== "string" ||
      !parsed.roomId ||
      typeof parsed.adminToken !== "string" ||
      !parsed.adminToken
    ) {
      return null;
    }
    return { roomId: parsed.roomId, adminToken: parsed.adminToken };
  } catch {
    return null;
  }
}

export function saveAdminSession(session: AdminSession): void {
  try {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch {
    // Setup can still continue when private browsing blocks local storage.
  }
}

export function clearAdminSession(): void {
  try {
    window.localStorage.removeItem(SESSION_KEY);
  } catch {
    // Nothing else to clear.
  }
}

export async function copyText(value: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }

    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    return copied;
  } catch {
    return false;
  }
}
