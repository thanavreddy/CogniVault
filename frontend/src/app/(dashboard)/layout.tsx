"use client";

import Link from "next/link";
import { Files, MessageSquare } from "lucide-react";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return <div className="min-h-screen bg-background text-foreground">
    <header className="border-b bg-card"><div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
      <Link href="/documents" className="text-xl font-semibold tracking-tight">CogniVault</Link>
      <nav className="flex gap-2">
        <NavLink href="/documents" active={pathname.startsWith("/documents")}><Files size={16} /> Documents</NavLink>
        <NavLink href="/chat" active={pathname.startsWith("/chat")}><MessageSquare size={16} /> Chat</NavLink>
      </nav>
    </div></header>
    <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
  </div>;
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: ReactNode }) {
  return <Link href={href} className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm ${active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}>{children}</Link>;
}
