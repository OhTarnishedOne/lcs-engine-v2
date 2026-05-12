"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle } from "lucide-react";

export function UpgradeSuccessBanner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [show, setShow] = useState(false);

  const [message, setMessage] = useState<{ title: string; body: string } | null>(null);

  useEffect(() => {
    if (searchParams.get("upgrade") === "success") {
      setShow(true);
      setMessage({ title: "You're now on Pro!", body: "All features are unlocked. Welcome to the full LCS Engine experience." });
      queryClient.invalidateQueries({ queryKey: ["billing-status"] });
      const url = new URL(window.location.href);
      url.searchParams.delete("upgrade");
      router.replace(url.pathname + url.search, { scroll: false });
    } else if (searchParams.get("claimed") === "true") {
      setShow(true);
      setMessage({ title: "Welcome — your trial activity has been saved.", body: "Your predictions, trades, and Calibration Score are now part of your permanent account." });
      const url = new URL(window.location.href);
      url.searchParams.delete("claimed");
      router.replace(url.pathname + url.search, { scroll: false });
    }
  }, [searchParams, router, queryClient]);

  if (!show || !message) return null;

  return (
    <div className="mb-6 flex items-center gap-3 rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
      <CheckCircle className="h-5 w-5 shrink-0 text-[#00D4AA]" />
      <div>
        <p className="text-sm font-semibold text-[#00D4AA]">{message.title}</p>
        <p className="text-sm text-gray-400">{message.body}</p>
      </div>
    </div>
  );
}
