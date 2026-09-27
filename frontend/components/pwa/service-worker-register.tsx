"use client";

import { useEffect } from "react";

/**
 * Registers the PWA service worker on the client.
 *
 * Registration is skipped in development so it never interferes with
 * hot-reload/HMR; in production it enables installability + offline shell.
 */
export function ServiceWorkerRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    const register = () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Registration is best-effort; the app works fully without it.
      });
    };

    if (document.readyState === "complete") {
      register();
    } else {
      window.addEventListener("load", register);
      return () => window.removeEventListener("load", register);
    }
  }, []);

  return null;
}
