"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GraduationCap,
  BarChart3,
  LineChart,
  MessageSquare,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { useUIStore } from "@/stores/ui-store";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Onboarding", href: "/onboarding", icon: GraduationCap },
  { name: "Strategies", href: "/strategies", icon: BarChart3 },
  { name: "Paper Trade", href: "/paper-trade", icon: LineChart },
  { name: "Probability Lab", href: "/probability-lab", icon: BarChart3 },
  { name: "Chat", href: "/chat", icon: MessageSquare },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1 p-2">
      {navigation.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.name}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-blue-50 text-blue-600"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 flex-shrink-0 border-r bg-white lg:block">
      <div className="flex h-full flex-col">
        <div className="flex-1 overflow-y-auto py-4">
          <NavLinks />
        </div>
        <Separator />
        <div className="p-4">
          <p className="text-xs text-slate-500">LCS Engine v2</p>
        </div>
      </div>
    </aside>
  );
}

export function MobileSidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <SheetContent side="left" className="w-64 p-0">
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <span className="text-lg font-semibold">Menu</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto py-4">
            <NavLinks onNavigate={() => setSidebarOpen(false)} />
          </div>
          <Separator />
          <div className="p-4">
            <p className="text-xs text-slate-500">LCS Engine v2</p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
