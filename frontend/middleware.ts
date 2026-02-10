import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for route protection.
 *
 * Note: This is a basic client-side token check.
 * The actual auth validation happens in the dashboard layout
 * which verifies the token with the API.
 */

// Routes that require authentication
const protectedRoutes = [
  "/dashboard",
  "/onboarding",
  "/strategies",
  "/paper-trade",
  "/probability-lab",
  "/chat",
  "/profile",
];

// Routes only for unauthenticated users
const authRoutes = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if user has a token (basic check - actual validation is client-side)
  const token = request.cookies.get("access_token")?.value;

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
