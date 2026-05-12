"use client";

import { useState, useRef } from "react";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

export function InfoTip({ content, children }: TooltipProps) {
  const [show, setShow] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout>>(undefined);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => {
        timeout.current = setTimeout(() => setShow(true), 300);
      }}
      onMouseLeave={() => {
        clearTimeout(timeout.current);
        setShow(false);
      }}
      onTouchStart={() => setShow(!show)}
    >
      {children}
      {show && (
        <span className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-normal rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-xs text-gray-300 shadow-lg max-w-[250px] text-center pointer-events-none">
          {content}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#1F2937]" />
        </span>
      )}
    </span>
  );
}
