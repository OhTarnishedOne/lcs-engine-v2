import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { DemoShell } from "@/components/demo-shell";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LCS Engine | Strategy Demo",
  description: "Interactive demo of the LCS Engine investment education platform. All data is simulated.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${plusJakarta.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <DemoShell>{children}</DemoShell>
      </body>
    </html>
  );
}
