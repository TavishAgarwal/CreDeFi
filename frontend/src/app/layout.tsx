import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppProvider } from "@/providers/app-provider";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CreDeFi — Reputation-Powered DeFi Credit Protocol",
  description:
    "Your Digital Reputation is Your Collateral. CreDeFi bridges Web2 income data with DeFi lending using AI-powered trust scores.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="font-sans antialiased bg-background text-foreground">
        <AppProvider>{children}</AppProvider>
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: "oklch(0.12 0 0)",
              border: "1px solid oklch(0.22 0 0)",
              color: "oklch(0.95 0 0)",
            },
          }}
        />
      </body>
    </html>
  );
}
