import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js 16 proxy for route protection (Node.js runtime).
 *
 * Keep imports limited to `next/server` — do not import app/lib code here.
 * Edge middleware bundles `ua-parser-js` from `next/server`, which crashes with
 * `ReferenceError: __dirname is not defined`; the proxy convention avoids that.
 */

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;
  const hostname = request.headers.get("host") || "";

  // Demo subdomain: redirect root to dashboard, skip auth for all other routes
  if (hostname.includes("demo.")) {
    if (pathname === "/" || pathname === "/login" || pathname === "/register") {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    return NextResponse.next();
  }

  // Public routes: /, /login, /register, /forgot-password, /reset-password, /organizations — no auth required
  const isPublicPage =
    pathname === "/" ||
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password" ||
    pathname === "/organizations" ||
    pathname === "/privacy" ||
    pathname === "/terms" ||
    pathname === "/pricing";

  // Auth pages: redirect to dashboard if already logged in
  if ((pathname === "/login" || pathname === "/register") && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Protected routes: redirect to login if not authenticated
  if (!isPublicPage && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)",
  ],
};
