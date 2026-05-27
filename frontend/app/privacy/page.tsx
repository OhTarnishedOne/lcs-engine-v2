import Link from "next/link";

export const metadata = {
  title: "Privacy Policy | LCS Engine",
  description: "How LCS Engine collects, uses, and protects your data.",
};

const LAST_UPDATED = "April 2026";
const CONTACT_EMAIL = "rico@lcsengine.com";
const COMPANY_NAME = "LCS Engine";
const SITE_URL = "https://www.lcsengine.com";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--lcs-primary)", color: "var(--lcs-text-primary)" }}>
      <nav className="border-b border-[#374151]">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-1.5">
            <span className="font-bold" style={{ color: "var(--lcs-accent)" }}>LCS</span>
            <span className="text-[#F9FAFB] font-semibold text-sm">Engine</span>
          </Link>
          <Link href="/" className="text-xs text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors">← Back to home</Link>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-16">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-[#F9FAFB] mb-2">Privacy Policy</h1>
          <p className="text-sm text-[#6B7280]">Last updated: {LAST_UPDATED}</p>
        </div>

        <div className="space-y-10 text-[#9CA3AF] text-sm leading-relaxed">
          <Section title="1. Introduction">
            <p>{COMPANY_NAME} (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) operates {SITE_URL} and the LCS Engine platform (the &quot;Service&quot;). This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Service. Please read this policy carefully. If you disagree with its terms, please discontinue use of the Service.</p>
          </Section>

          <Section title="2. Information we collect">
            <p className="mb-3">We may collect the following categories of information:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-[#F9FAFB] font-medium">Account information:</strong> Name, email address, and password when you register.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Profile and onboarding data:</strong> Investor archetype, risk tolerance, and financial literacy level as captured during onboarding.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Usage data:</strong> Pages visited, features used, session duration, and platform interactions.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Device and log data:</strong> IP address, browser type, operating system, and referring URLs.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Communications:</strong> Messages you send to our AI tutor and any support correspondence.</li>
            </ul>
          </Section>

          <Section title="3. How we use your information">
            <ul className="list-disc pl-5 space-y-2">
              <li>To provide, operate, and improve the Service.</li>
              <li>To personalize your experience based on your investor archetype.</li>
              <li>To send transactional emails (e.g., password resets) via our email provider.</li>
              <li>To analyze aggregate usage trends and platform performance.</li>
              <li>To comply with legal obligations.</li>
            </ul>
            <p className="mt-3">We do not sell your personal information to third parties.</p>
          </Section>

          <Section title="4. Third-party services">
            <p className="mb-3">We use select third-party services to operate the platform:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-[#F9FAFB] font-medium">Anthropic (Claude API):</strong> Powers our AI tutor.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Alpaca Markets:</strong> Powers the paper trading simulator.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Resend:</strong> Handles transactional email delivery.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Stripe:</strong> Processes subscription payments. When you upgrade to Pro, you are redirected to Stripe&apos;s hosted checkout page to enter payment details — card information is collected and stored entirely by Stripe and never reaches LCS Engine servers. We share your email address with Stripe to pre-fill the checkout form and to associate the payment with your LCS Engine account. We store only a Stripe customer identifier on our side to manage your subscription status. Stripe&apos;s privacy policy and PCI DSS compliance govern their handling of your payment data.</li>
              <li><strong className="text-[#F9FAFB] font-medium">PostHog:</strong> Analyzes aggregate usage and product engagement to help us improve the service.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Polygon:</strong> Provides market data for our paper trading and prediction features; does not receive personal user data.</li>
              <li><strong className="text-[#F9FAFB] font-medium">Railway / Vercel:</strong> Cloud infrastructure hosting.</li>
            </ul>
          </Section>

          <Section title="5. Data retention">
            <p>We retain your account data for as long as your account is active. You may request deletion at any time by emailing <a href={`mailto:${CONTACT_EMAIL}`} className="underline hover:text-[#F9FAFB]">{CONTACT_EMAIL}</a>.</p>
          </Section>

          <Section title="6. Data security">
            <p>We implement industry-standard security measures including HTTPS encryption, hashed passwords, token-based authentication with expiry, and access controls. No method of transmission over the internet is 100% secure.</p>
          </Section>

          <Section title="7. Children's privacy">
            <p>The Service is not directed to individuals under the age of 18. We do not knowingly collect personal information from minors.</p>
          </Section>

          <Section title="8. Your rights">
            <p className="mb-3">Depending on your jurisdiction, you may have the right to access, correct, delete, or port your personal data. To exercise any of these rights, contact us at <a href={`mailto:${CONTACT_EMAIL}`} className="underline hover:text-[#F9FAFB]">{CONTACT_EMAIL}</a>.</p>
          </Section>

          <Section title="9. Changes to this policy">
            <p>We may update this Privacy Policy from time to time. We will notify registered users of material changes via email.</p>
          </Section>

          <Section title="10. Contact us">
            <p>Questions? <a href={`mailto:${CONTACT_EMAIL}`} className="underline hover:text-[#F9FAFB]">{CONTACT_EMAIL}</a></p>
          </Section>
        </div>
      </main>

      <footer className="border-t border-[#374151] mt-10">
        <div className="max-w-3xl mx-auto px-6 py-8 flex items-center justify-between">
          <p className="text-xs text-[#6B7280]">© {new Date().getFullYear()} {COMPANY_NAME}</p>
          <div className="flex gap-5 text-xs text-[#6B7280]">
            <Link href="/terms" className="hover:text-[#9CA3AF] transition-colors">Terms</Link>
            <Link href="/organizations" className="hover:text-[#9CA3AF] transition-colors">For Organizations</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-base font-semibold text-[#F9FAFB] mb-3">{title}</h2>
      {children}
    </div>
  );
}
