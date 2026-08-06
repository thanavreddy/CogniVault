"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { redirect } from "next/navigation";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  MessageSquare, 
  Files, 
  BarChart3, 
  CheckSquare, 
  Settings, 
  ShieldAlert
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Documents', href: '/documents', icon: Files },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Evaluation', href: '/evaluation', icon: CheckSquare },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Admin', href: '/admin', icon: ShieldAlert },
];

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { isLoaded, userId } = useAuth();
  const pathname = usePathname();

  if (isLoaded && !userId) {
    redirect("/sign-in");
  }

  if (!isLoaded) return <div className="h-screen w-full flex items-center justify-center">Loading...</div>;

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card flex flex-col">
        <div className="h-16 flex items-center px-6 border-b">
          <h1 className="text-xl font-bold text-primary">KnowledgeAI</h1>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary text-primary-foreground" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t flex items-center gap-3">
          <UserButton afterSignOutUrl="/" />
          <div className="flex flex-col">
            <span className="text-sm font-medium">My Account</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 border-b bg-background flex items-center justify-between px-6">
          <h2 className="text-lg font-semibold capitalize">
            {pathname.split('/')[1] || 'Dashboard'}
          </h2>
          {/* Header actions (Search, Notifications) could go here */}
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
