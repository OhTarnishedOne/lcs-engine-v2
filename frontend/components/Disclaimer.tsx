"use client";

export const DISCLAIMER_SHORT =
  "For educational purposes only. LCS Engine is not investment, financial, legal, or tax advice. Strategies and information shown are illustrations to help you learn — not recommendations to buy or sell any security. Investing involves risk, including possible loss of principal.";

export const DISCLAIMER_FOOTER =
  "LCS Engine is for educational purposes only and is not investment, financial, or tax advice. Investing involves risk, including loss of principal.";

export function DisclaimerInline({ className = "" }: { className?: string }) {
  return (
    <p className={`text-xs text-gray-500 leading-relaxed ${className}`}>
      {DISCLAIMER_SHORT}
    </p>
  );
}

export function DisclaimerFooter() {
  return (
    <div className="border-t border-gray-800 px-6 py-4 text-center">
      <p className="text-xs text-gray-500 max-w-3xl mx-auto">
        {DISCLAIMER_FOOTER}
      </p>
    </div>
  );
}
