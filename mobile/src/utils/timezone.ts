/**
 * Format an ISO timestamp into a human-readable string in the user's local timezone.
 * e.g. "Wed, Oct 9 · 12:05 AM EDT"
 */
export function formatLocalDateTime(isoString: string): string {
  const date = new Date(isoString);

  const day = date.toLocaleDateString("en-US", { weekday: "short" });
  const month = date.toLocaleDateString("en-US", { month: "short" });
  const dayNum = date.getDate();
  const time = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
  const tz = getTimezoneAbbrev();

  return `${day}, ${month} ${dayNum} · ${time} ${tz}`;
}

/**
 * Get the user's timezone abbreviation (e.g. "EDT", "PST", "GMT").
 */
export function getTimezoneAbbrev(): string {
  try {
    const resolved = Intl.DateTimeFormat().resolvedOptions();
    const tzName = resolved.timeZone; // e.g. "America/New_York"

    // Try to get the short timezone name
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZoneName: "short",
      timeZone: tzName,
    });
    const parts = formatter.formatToParts(new Date());
    const tzPart = parts.find((p) => p.type === "timeZoneName");
    if (tzPart) return tzPart.value;

    // Fallback: extract from timezone name
    if (tzName) {
      const segments = tzName.split("/");
      return segments[segments.length - 1].replace(/_/g, " ");
    }

    return "";
  } catch {
    return "";
  }
}

/**
 * Get the user's full timezone name (e.g. "America/New_York").
 */
export function getTimezoneName(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "Unknown";
  } catch {
    return "Unknown";
  }
}

/**
 * Format a countdown from now to a future ISO timestamp.
 * e.g. "in 2d 4h", "in 3h 22m", "in 45m"
 */
export function formatCountdown(isoString: string): string {
  const now = new Date();
  const target = new Date(isoString);
  const diffMs = target.getTime() - now.getTime();

  if (diffMs <= 0) return "now";

  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) {
    const remainingHours = hours % 24;
    return remainingHours > 0 ? `in ${days}d ${remainingHours}h` : `in ${days}d`;
  }
  if (hours > 0) {
    return minutes > 0 ? `in ${hours}h ${minutes}m` : `in ${hours}h`;
  }
  return `in ${minutes}m`;
}