"use client";

/**
 * Root page — middleware redirects / to /login or /dashboard.
 * This component is a fallback that should rarely render.
 */
export default function RootPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A1628]">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#00D4AA] border-t-transparent" />
    </div>
  );
}
