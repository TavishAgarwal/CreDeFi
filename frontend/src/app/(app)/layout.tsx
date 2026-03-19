"use client";

import { type ReactNode } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { AuthGuard } from "@/components/layout/auth-guard";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <AuthGuard>
        <main className="min-h-[calc(100vh-8rem)]">{children}</main>
      </AuthGuard>
      <Footer />
    </>
  );
}
