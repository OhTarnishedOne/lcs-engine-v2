"use client";

import { ArrowRight, Shield } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

const GUEST_TRIAL_DAYS = 5;

export function DemoBanner() {
  if (typeof window === "undefined") return null;
  if (!window.location.hostname.includes("demo.")) return null;

  return <GuestBannerInner />;
}

function GuestBannerInner() {
  const { user } = useAuthStore();

  const isAdmin = user?.is_admin ?? false;
  const isGuest = user?.is_guest ?? false;
  const daysRemaining = user?.days_remaining ?? null;
  const guestId = user?.id;

  // Admin users: show admin badge, never show trial banner
  if (isAdmin) {
    return (
      <div className="sticky top-0 z-[60] flex items-center justify-center gap-2 bg-[#1A2942] border-b border-[#00D4AA]/20 px-4 py-1.5">
        <Shield className="h-3 w-3 text-[#00D4AA]" />
        <p className="text-xs text-[#00D4AA] font-medium">Admin View</p>
      </div>
    );
  }

  // Expired guest: conversion gate
  const isExpired = daysRemaining !== null && daysRemaining !== undefined && daysRemaining <= 0;
  if (isExpired && isGuest) {
    return (
      <div className="sticky top-0 z-[60] flex flex-col items-center gap-2 bg-[#EF4444]/20 border-b border-[#EF4444]/30 px-4 py-3 sm:flex-row sm:justify-center sm:gap-4">
        <p className="text-sm text-[#EF4444] font-medium text-center">
          Your trial has ended. Claim your account to keep your Calibration Score, predictions, and history.
        </p>
        <a
          href={`https://www.lcsengine.com/register?from=demo&guest_id=${guestId}`}
          className="inline-flex items-center gap-1 rounded-md bg-[#00D4AA] px-4 py-1.5 text-xs font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
        >
          Claim your account
          <ArrowRight className="h-3 w-3" />
        </a>
      </div>
    );
  }

  // Active trial: countdown banner
  const isUrgent = daysRemaining !== null && daysRemaining !== undefined && daysRemaining <= 2;
  const dayLabel = daysRemaining !== null && daysRemaining !== undefined
    ? `Day ${GUEST_TRIAL_DAYS - daysRemaining + 1} of ${GUEST_TRIAL_DAYS}`
    : null;

  return (
    <div className={`sticky top-0 z-[60] flex items-center justify-center gap-3 px-4 py-2 border-b ${
      isUrgent
        ? "bg-[#F59E0B]/20 border-[#F59E0B]/30"
        : "bg-[#1A2942] border-[#00D4AA]/20"
    }`}>
      <p className={`text-xs ${isUrgent ? "text-[#F59E0B]" : "text-gray-300"}`}>
        {dayLabel && <span className="font-semibold">{dayLabel} — </span>}
        Claim your account to keep your progress
      </p>
      <a
        href={`https://www.lcsengine.com/register?from=demo&guest_id=${guestId || ""}`}
        className="inline-flex items-center gap-1 rounded-md bg-[#00D4AA] px-3 py-1 text-xs font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
      >
        Get Started
        <ArrowRight className="h-3 w-3" />
      </a>
    </div>
  );
}
