"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GraduationCap,
  Layers,
  TrendingUp,
  Target,
  ClipboardList,
  MessageSquare,
  X,
  BarChart3,
  UserCircle,
  Lock,
  Shield,
} from "lucide-react";

import { useQuery } from "@tanstack/react-query";

import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { useCalibrationScore } from "@/hooks/useCalibrationScore";

const PRO_ROUTES = new Set(["/probability-lab", "/paper-trade"]);

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Decisions", href: "/decisions", icon: ClipboardList },
  { name: "Probability Lab", href: "/probability-lab", icon: Target },
  { name: "AI Chat", href: "/chat", icon: MessageSquare },
  { name: "Strategies", href: "/strategies", icon: Layers },
  { name: "Paper Trade", href: "/paper-trade", icon: TrendingUp },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { isPro } = useBillingStatus();
  const { user } = useAuthStore();

  const { data: progress } = useQuery({
    queryKey: ["onboarding-progress"],
    queryFn: () => api.getOnboardingProgress(),
  });

  const isOnboardingComplete = progress?.is_complete ?? false;

  const bottomNav = [
    ...(isOnboardingComplete
      ? [{ name: "Profile", href: "/profile", icon: UserCircle }]
      : [{ name: "Onboarding", href: "/onboarding", icon: GraduationCap }]),
    ...(user?.is_admin
      ? [{ name: "Admin", href: "/admin", icon: Shield }]
      : []),
  ];

  return (
    <nav className="flex flex-1 flex-col">
      <div className="flex flex-col gap-1 p-3">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-[#00D4AA]/10 text-[#00D4AA] border border-[#00D4AA]/20"
                  : "text-gray-400 hover:bg-[#1A2942] hover:text-gray-100"
              )}
            >
              <item.icon className={cn("h-5 w-5", isActive && "text-[#00D4AA]")} />
              {item.name}
              {PRO_ROUTES.has(item.href) && !isPro && (
                item.href === "/probability-lab" ? (
                  <span className="ml-auto rounded-full bg-[#00D4AA]/20 px-1.5 py-0.5 text-[10px] font-semibold text-[#00D4AA]">
                    PRO
                  </span>
                ) : (
                  <Lock className="ml-auto h-3 w-3 text-gray-600" />
                )
              )}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto border-t border-gray-800 p-3">
        {bottomNav.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onNavigate}
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
  );
}

function CalibrationBadge() {
  const { score } = useCalibrationScore();
  if (score === null) return null;
  return (
    <Link href="/probability-lab" className="flex items-center gap-2 rounded-lg bg-[#1A2942] px-3 py-2 hover:bg-[#1A2942]/80 transition-colors">
      <Target className="h-4 w-4 text-[#00D4AA]" />
      <span className="text-xs text-gray-400">Calibration</span>
      <span className="ml-auto text-sm font-bold font-mono-nums text-[#00D4AA]">{score}</span>
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 flex-shrink-0 border-r border-gray-800 bg-[#0A1628] lg:flex lg:flex-col">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2 border-b border-gray-800 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
            <BarChart3 className="h-4 w-4 text-[#0A1628]" />
          </div>
          <span className="text-lg font-bold text-white">LCS Engine</span>
        </div>

        {/* Navigation */}
        <div className="flex flex-1 flex-col overflow-y-auto py-2">
          <NavLinks />
        </div>

        {/* Calibration Score Badge */}
        <div className="px-3 pb-2">
          <CalibrationBadge />
        </div>

        {/* Version */}
        <div className="border-t border-gray-800 p-4">
          <p className="text-xs text-gray-600">v3.0</p>
        </div>
      </div>
    </aside>
  );
}

export function MobileSidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <SheetContent
        side="left"
        className="w-64 border-r border-gray-800 bg-[#0A1628] p-0"
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-800 px-4 py-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
                <BarChart3 className="h-4 w-4 text-[#0A1628]" />
              </div>
              <span className="text-lg font-bold text-white">LCS Engine</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:bg-[#1A2942] hover:text-white"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <div className="flex flex-1 flex-col overflow-y-auto py-2">
            <NavLinks onNavigate={() => setSidebarOpen(false)} />
          </div>

          {/* Version */}
          <div className="border-t border-gray-800 p-4">
            <p className="text-xs text-gray-600">v3.0</p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
