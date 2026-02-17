import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for route protection.
 *
 * Note: This is a basic client-side token check.
 * The actual auth validation happens in the dashboard layout
 * which verifies the token with the API.
 */

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // We can't check localStorage from middleware, so we rely on client-side auth
  // The dashboard layout handles the actual redirect if not authenticated

  // Redirect root to dashboard or login
  if (pathname === "/") {
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
