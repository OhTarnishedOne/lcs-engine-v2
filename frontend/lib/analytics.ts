"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const FLUSH_INTERVAL_MS = 10_000;
const FLUSH_THRESHOLD = 5;

interface QueuedEvent {
  event_name: string;
  event_properties?: Record<string, unknown>;
  path?: string;
  duration_ms?: number;
}

let sessionId: string | null = null;
let lastEventTime: number | null = null;
let buffer: QueuedEvent[] = [];
let timer: ReturnType<typeof setInterval> | null = null;

function getSessionId(): string {
  try {
    if (typeof window === "undefined") return "";
    if (sessionId) return sessionId;
    const stored = localStorage.getItem("analytics_session_id");
    if (stored) {
      sessionId = stored;
      return stored;
    }
    const id = crypto.randomUUID();
    localStorage.setItem("analytics_session_id", id);
    sessionId = id;
    return id;
  } catch {
    return "";
  }
}

function flush() {
  try {
    if (typeof window === "undefined") return;
    if (buffer.length === 0) return;

    const events = [...buffer];
    buffer = [];

    const token = localStorage.getItem("access_token");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    fetch(`${API_URL}/analytics/events`, {
      method: "POST",
      headers,
      body: JSON.stringify({ session_id: getSessionId(), events }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // fail silently
  }
}

export function trackEvent(
  eventName: string,
  properties?: Record<string, unknown>
) {
  try {
    if (typeof window === "undefined") return;

    const now = Date.now();
    const duration_ms =
      lastEventTime !== null ? now - lastEventTime : undefined;
    lastEventTime = now;

    const event: QueuedEvent = {
      event_name: eventName,
      path: window.location.pathname,
      duration_ms,
    };
    if (properties && Object.keys(properties).length > 0) {
      event.event_properties = properties;
    }

    buffer.push(event);

    if (buffer.length >= FLUSH_THRESHOLD) {
      flush();
    }
  } catch {
    // fail silently
  }
}

// Self-initialize on import
function init() {
  try {
    if (typeof window === "undefined") return;

    getSessionId();

    if (!timer) {
      timer = setInterval(flush, FLUSH_INTERVAL_MS);
    }

    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        flush();
      }
    });

    window.addEventListener("beforeunload", flush);
  } catch {
    // fail silently
  }
}

init();
