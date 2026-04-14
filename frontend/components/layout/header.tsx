"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, LogOut, User, BarChart3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import { useBillingStatus } from "@/hooks/useBillingStatus";

export function Header() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();
  const { isPro } = useBillingStatus();

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : "??";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-[#0A1628]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0A1628]/80">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Left: Mobile menu button + Logo (mobile only) */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden text-gray-400 hover:bg-[#1A2942] hover:text-white"
            onClick={toggleSidebar}
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle menu</span>
          </Button>
          <Link href="/dashboard" className="flex items-center gap-2 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
              <BarChart3 className="h-4 w-4 text-[#0A1628]" />
            </div>
            <span className="text-lg font-bold text-white">LCS Engine</span>
          </Link>
        </div>

        {/* Right: User menu */}
        <div className="ml-auto">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-10 w-10 rounded-full hover:bg-[#1A2942]"
              >
                <Avatar className="h-10 w-10 border-2 border-[#00D4AA]/30">
                  <AvatarFallback className="bg-[#1A2942] text-[#00D4AA] font-semibold">
                    {initials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="w-56 border-gray-800 bg-[#1F2937]"
            >
              <div className="flex items-center gap-3 p-3">
                <Avatar className="h-10 w-10 border-2 border-[#00D4AA]/30">
                  <AvatarFallback className="bg-[#1A2942] text-[#00D4AA] text-sm font-semibold">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col">
                  <p className="text-sm font-medium text-gray-100 truncate max-w-[150px]">
                    {user?.email}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <p className="text-xs text-gray-500">{isPro ? "Pro" : "Free"} Plan</p>
                    {isPro && (
                      <span className="rounded-full bg-[#00D4AA]/20 px-1.5 py-0.5 text-[10px] font-semibold text-[#00D4AA]">
                        PRO
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <DropdownMenuSeparator className="bg-gray-700" />
              <DropdownMenuItem
                asChild
                className="text-gray-300 focus:bg-[#1A2942] focus:text-white cursor-pointer"
              >
                <Link href="/profile" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-gray-700" />
              <DropdownMenuItem
                onClick={handleLogout}
                className="flex items-center gap-2 text-red-400 focus:bg-red-500/10 focus:text-red-400 cursor-pointer"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
