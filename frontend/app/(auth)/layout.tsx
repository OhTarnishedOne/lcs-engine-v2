/**
 * Auth layout - centered card layout for login/register.
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-slate-900">LCS Engine</h1>
        <p className="mt-2 text-slate-600">Your investment learning platform</p>
      </div>
      {children}
    </div>
  );
}
