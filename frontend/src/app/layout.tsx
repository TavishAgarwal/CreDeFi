import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppProvider } from "@/providers/app-provider";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "CreDeFi",
  description: "Decentralised credit scoring and lending platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-950 text-gray-100 antialiased">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
