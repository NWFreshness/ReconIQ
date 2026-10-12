import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono, Zilla_Slab } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const zillaSlab = Zilla_Slab({
  variable: "--font-zilla-slab",
  subsets: ["latin"],
  weight: ["500", "600"],
});

export const metadata: Metadata = {
  title: "ReconIQ — Marketing Intelligence",
  description: "AI-powered competitive intelligence and market research platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${zillaSlab.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <header className="border-b border-foreground">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <Link href="/" className="font-display text-xl font-semibold">
              ReconIQ
            </Link>
            <span className="text-xs text-muted">Competitor research</span>
          </div>
        </header>
        <main className="flex-1 page-enter">{children}</main>
        <footer className="border-t border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 text-xs text-muted">ReconIQ v1.0.0</div>
        </footer>
      </body>
    </html>
  );
}
