"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Target,
  MessageSquare,
  Layers,
  UserCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useBillingStatus } from "@/hooks/useBillingStatus";

const PRO_ROUTES = new Set(["/probability-lab", "/paper-trade"]);

const tabs = [
  { name: "Home", href: "/dashboard", icon: LayoutDashboard },
  { name: "Lab", href: "/probability-lab", icon: Target },
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "Strategies", href: "/strategies", icon: Layers },
  { name: "Profile", href: "/profile", icon: UserCircle },
];

/**
 * Mobile tab bar. Shown only below the `lg` breakpoint, complementing the
 * desktop sidebar and the full-nav hamburger sheet. Fixed to the bottom with
 * iOS safe-area padding so it clears the home indicator.
 */
export function BottomNav() {
  const pathname = usePathname();
  const { isPro } = useBillingStatus();

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-800 bg-[#0A1628]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0A1628]/85 lg:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      aria-label="Primary"
    >
      <div className="flex items-stretch justify-around">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.href || pathname.startsWith(`${tab.href}/`);
          const showPro = PRO_ROUTES.has(tab.href) && !isPro;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "relative flex min-h-[3.25rem] flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 text-[0.65rem] font-medium transition-colors",
                isActive
                  ? "text-[#00D4AA]"
                  : "text-gray-500 hover:text-gray-300"
              )}
            >
              <tab.icon className="h-5 w-5" />
              <span className="leading-none">{tab.name}</span>
              {showPro && (
                <span className="absolute right-2 top-1.5 h-1.5 w-1.5 rounded-full bg-[#00D4AA]" />
              )}
              {isActive && (
                <span className="absolute inset-x-4 top-0 h-0.5 rounded-full bg-[#00D4AA]" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
