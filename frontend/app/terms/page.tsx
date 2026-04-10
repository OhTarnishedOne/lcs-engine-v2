import Link from "next/link";

export const metadata = {
  title: "Terms of Service | LCS Engine",
  description: "Terms and conditions for using the LCS Engine platform.",
};

const LAST_UPDATED = "April 2026";
const CONTACT_EMAIL = "rico@lcsengine.com";
const COMPANY_NAME = "LCS Engine";

export default function TermsPage() {
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
          <h1 className="text-3xl font-bold text-[#F9FAFB] mb-2">Terms of Service</h1>
          <p className="text-sm text-[#6B7280]">Last updated: {LAST_UPDATED}</p>
        </div>

        <div className="space-y-10 text-[#9CA3AF] text-sm leading-relaxed">
          <Section title="1. Acceptance of terms">
            <p>By accessing or using the LCS Engine platform (&quot;Service&quot;), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>
          </Section>

          <Section title="2. Description of service">
            <p>{COMPANY_NAME} provides an AI-powered financial literacy platform including an investor archetype engine, AI tutor, paper trading simulator, probability training lab, and related educational tools. The Service is for educational and informational purposes only.</p>
          </Section>

          <Section title="3. Not financial advice">
            <p><strong className="text-[#F9FAFB] font-medium">Nothing on the LCS Engine platform constitutes financial, investment, legal, or tax advice.</strong> All content, AI tutor responses, simulations, and educational materials are provided for informational and educational purposes only. Always consult a qualified financial advisor before making investment decisions.</p>
          </Section>

          <Section title="4. Eligibility">
            <p>You must be at least 18 years old to use the Service. By using the Service, you represent that you meet this requirement.</p>
          </Section>

          <Section title="5. User accounts">
            <p>You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. Notify us immediately at <a href={`mailto:${CONTACT_EMAIL}`} className="underline hover:text-[#F9FAFB]">{CONTACT_EMAIL}</a> of any unauthorized use.</p>
          </Section>

          <Section title="6. Acceptable use">
            <p className="mb-3">You agree not to:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Use the Service for any unlawful purpose.</li>
              <li>Attempt to reverse engineer, scrape, or extract data from the platform.</li>
              <li>Transmit harmful, offensive, or misleading content.</li>
              <li>Circumvent authentication or security measures.</li>
              <li>Use the Service to provide financial advice to third parties.</li>
              <li>Create multiple accounts to circumvent limitations or access controls.</li>
            </ul>
          </Section>

          <Section title="7. Intellectual property">
            <p>The Service and its original content, features, and functionality are and will remain the exclusive property of {COMPANY_NAME}. Our trademarks and trade dress may not be used without our prior written consent.</p>
          </Section>

          <Section title="8. Third-party services">
            <p>The Service integrates with Anthropic (AI), Alpaca (paper trading), Kalshi, and Metaculus (probability data). Use of these integrations is subject to the respective third-party terms of service.</p>
          </Section>

          <Section title="9. Disclaimers">
            <p>THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.</p>
          </Section>

          <Section title="10. Limitation of liability">
            <p>TO THE MAXIMUM EXTENT PERMITTED BY LAW, {COMPANY_NAME.toUpperCase()} SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF THE SERVICE.</p>
          </Section>

          <Section title="11. Termination">
            <p>We may suspend or terminate your account at any time for violation of these Terms. You may terminate your account at any time by contacting us.</p>
          </Section>

          <Section title="12. Governing law">
            <p>These Terms shall be governed by the laws of the State of New York, without regard to its conflict of law provisions. Disputes shall be subject to the exclusive jurisdiction of courts in New York County, New York.</p>
          </Section>

          <Section title="13. Changes to terms">
            <p>We reserve the right to modify these Terms at any time. Continued use of the Service after changes constitutes acceptance.</p>
          </Section>

          <Section title="14. Contact">
            <p>Questions? <a href={`mailto:${CONTACT_EMAIL}`} className="underline hover:text-[#F9FAFB]">{CONTACT_EMAIL}</a></p>
          </Section>
        </div>
      </main>

      <footer className="border-t border-[#374151] mt-10">
        <div className="max-w-3xl mx-auto px-6 py-8 flex items-center justify-between">
          <p className="text-xs text-[#6B7280]">© {new Date().getFullYear()} {COMPANY_NAME}</p>
          <div className="flex gap-5 text-xs text-[#6B7280]">
            <Link href="/privacy" className="hover:text-[#9CA3AF] transition-colors">Privacy</Link>
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
