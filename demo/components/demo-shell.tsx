"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Layers,
  TrendingUp,
  BarChart3,
  LineChart,
  UserCircle,
  Target,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Risk Profile", href: "/risk-profile", icon: UserCircle },
  { name: "Strategies", href: "/strategies", icon: Layers },
  { name: "Probability Lab", href: "/probability-lab", icon: Target },
  { name: "Paper Trading", href: "/paper-trading", icon: TrendingUp },
  { name: "Backtesting", href: "/backtesting", icon: LineChart },
];

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 flex-shrink-0 border-r border-gray-800 bg-[#0A1628] lg:flex lg:flex-col">
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-2 border-b border-gray-800 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
            <BarChart3 className="h-4 w-4 text-[#0A1628]" />
          </div>
          <span className="text-lg font-bold text-white">LCS Engine</span>
        </div>

        <nav className="flex flex-1 flex-col p-3">
          <div className="flex flex-col gap-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                    isActive
                      ? "bg-[#00D4AA]/10 text-[#00D4AA] border border-[#00D4AA]/20"
                      : "text-gray-400 hover:bg-[#1A2942] hover:text-gray-100"
                  )}
                >
                  <item.icon className={cn("h-5 w-5", isActive && "text-[#00D4AA]")} />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="border-t border-gray-800 p-4">
          <p className="text-xs text-gray-600">v3.0 · Demo</p>
        </div>
      </div>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-[#0A1628]/95 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">LCS Engine</span>
          <span className="text-sm text-gray-500">|</span>
          <span className="text-sm text-gray-400">Strategy Demo</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-[#F59E0B]/20 px-2.5 py-0.5 text-xs font-semibold text-[#F59E0B]">
            Demo Mode
          </span>
          <a
            href="https://www.lcsengine.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#00D4AA] px-3 py-1.5 text-xs font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
          >
            Full Platform
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </header>
  );
}

function DemoBanner() {
  return (
    <div className="flex items-center justify-center gap-2 border-b border-[#F59E0B]/30 bg-[#F59E0B]/10 px-4 py-2">
      <AlertTriangle className="h-3.5 w-3.5 text-[#F59E0B]" />
      <p className="text-xs text-[#F59E0B]">
        Market data is simulated for demo purposes
      </p>
    </div>
  );
}

export function DemoShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0A1628]">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <TopBar />
        <DemoBanner />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
