import { NextRequest, NextResponse } from "next/server";
import { DraftError } from "./store";

export async function readJsonObject(
  request: NextRequest,
): Promise<Record<string, unknown>> {
  let value: unknown;
  try {
    value = await request.json();
  } catch {
    throw new DraftError(
      400,
      "invalid_json",
      "Request body must contain valid JSON.",
    );
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new DraftError(
      400,
      "invalid_request_body",
      "Request body must be a JSON object.",
    );
  }
  return value as Record<string, unknown>;
}

export function apiErrorResponse(error: unknown): NextResponse {
  if (error instanceof DraftError) {
    return NextResponse.json(
      {
        error: error.message,
        code: error.code,
        ...(error.details ? { details: error.details, ...error.details } : {}),
      },
      { status: error.status },
    );
  }

  console.error("Unhandled Scribner Draft API error:", error);
  return NextResponse.json(
    {
      error: "An unexpected server error occurred.",
      code: "internal_error",
    },
    { status: 500 },
  );
}

export function requestOrigin(request: NextRequest): string {
  const configuredOrigin =
    process.env.NEXT_PUBLIC_APP_URL?.trim() || process.env.APP_URL?.trim();
  if (configuredOrigin) {
    try {
      return new URL(configuredOrigin).origin;
    } catch {
      // Fall through to request headers when an optional configured URL is invalid.
    }
  }

  const forwardedHost = request.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const forwardedProtocol =
    request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim() ||
    request.nextUrl.protocol.replace(":", "");
  if (forwardedHost) {
    try {
      return new URL(`${forwardedProtocol}://${forwardedHost}`).origin;
    } catch {
      // request.nextUrl.origin remains a safe fallback.
    }
  }
  return request.nextUrl.origin;
}
