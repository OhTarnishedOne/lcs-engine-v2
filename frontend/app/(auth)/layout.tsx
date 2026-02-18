import { BarChart3, Brain, TrendingUp, Target } from "lucide-react";

/**
 * Auth layout - split screen: branding left, form right (desktop).
 * Centered card with logo on mobile.
 */

const highlights = [
  {
    icon: Brain,
    text: "AI-powered lessons that adapt to your level",
  },
  {
    icon: TrendingUp,
    text: "Paper trade with real market data, zero risk",
  },
  {
    icon: Target,
    text: "Predict markets and sharpen your judgment",
  },
];

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-[#0A1628]">
      {/* Left branding panel — hidden on mobile and tablets */}
      <div className="hidden xl:flex xl:w-1/2 flex-col justify-center px-16 2xl:px-24">
        <div className="max-w-md">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#00D4AA]">
              <BarChart3 className="h-6 w-6 text-[#0A1628]" />
            </div>
            <span className="text-2xl font-bold text-white">LCS Engine</span>
          </div>

          <h2 className="mb-4 text-4xl font-bold tracking-tight text-white">
            Learn to invest.{" "}
            <span className="text-[#00D4AA]">Without the fear.</span>
          </h2>
          <p className="mb-10 text-lg text-gray-400">
            AI-powered financial education that meets you where you are.
          </p>

          <div className="space-y-5">
            {highlights.map((h) => (
              <div key={h.text} className="flex items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1A2942]">
                  <h.icon className="h-5 w-5 text-[#00D4AA]" />
                </div>
                <span className="text-base text-gray-300">{h.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full xl:w-1/2 flex-col items-center justify-center px-6 py-12">
        {/* Logo — shown when left panel is hidden */}
        <div className="mb-8 flex flex-col items-center xl:hidden">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-[#00D4AA]">
            <BarChart3 className="h-7 w-7 text-[#0A1628]" />
          </div>
          <span className="text-2xl font-bold text-white">LCS Engine</span>
          <p className="mt-1 text-sm text-gray-400">
            Your investment learning platform
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
