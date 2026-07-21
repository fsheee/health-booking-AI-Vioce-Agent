"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  LayoutDashboard, Users, CalendarDays, Stethoscope, Mic,
  UserPlus, LogOut, Shield,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navConfig: Record<string, NavItem[]> = {
  admin: [
    { label: "Dashboard", href: "/dashboard/admin", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Patients", href: "/dashboard/admin", icon: <Users className="h-4 w-4" /> },
    { label: "Appointments", href: "/dashboard/admin", icon: <CalendarDays className="h-4 w-4" /> },
    { label: "Doctors", href: "/dashboard/admin", icon: <Stethoscope className="h-4 w-4" /> },
    { label: "Voice Sessions", href: "/dashboard/admin", icon: <Mic className="h-4 w-4" /> },
  ],
  doctor: [
    { label: "Dashboard", href: "/dashboard/doctor", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Patients", href: "/dashboard/doctor", icon: <Users className="h-4 w-4" /> },
    { label: "Schedule", href: "/dashboard/doctor", icon: <CalendarDays className="h-4 w-4" /> },
    { label: "Voice Reviews", href: "/dashboard/doctor", icon: <Mic className="h-4 w-4" /> },
  ],
  front_desk: [
    { label: "Dashboard", href: "/dashboard/front-desk", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Register Patient", href: "/dashboard/front-desk", icon: <UserPlus className="h-4 w-4" /> },
    { label: "Appointments", href: "/dashboard/front-desk", icon: <CalendarDays className="h-4 w-4" /> },
  ],
  patient: [
    { label: "Dashboard", href: "/dashboard/patient", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Appointments", href: "/dashboard/patient", icon: <CalendarDays className="h-4 w-4" /> },
    { label: "Voice Assistant", href: "/dashboard/patient/voice", icon: <Mic className="h-4 w-4" /> },
  ],
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      router.push("/login");
      return;
    }
    api.auth.me().then(setUser).catch(() => {
      localStorage.removeItem("access_token");
      document.cookie = "access_token=; path=/; max-age=0";
      router.push("/login");
    });
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    document.cookie = "access_token=; path=/; max-age=0";
    router.push("/login");
  }

  if (!user) {
    return (
      <div className="flex min-h-screen">
        <aside className="w-64 border-r bg-card p-4 space-y-4">
          <Skeleton className="h-8 w-32" />
          <div className="space-y-2">
            {[1,2,3].map((i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </aside>
        <main className="flex-1 p-8">
          <Skeleton className="h-8 w-48" />
        </main>
      </div>
    );
  }

  const items = navConfig[user.role] ?? navConfig.patient;

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r bg-card flex flex-col">
        <div className="p-4 border-b">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg">
            <Shield className="h-5 w-5 text-primary" />
            Healthcare AI
          </Link>
          <p className="text-xs text-muted-foreground mt-1 capitalize">{user.role.replace("_", " ")}</p>
        </div>

        <ScrollArea className="flex-1 p-3">
          <nav className="space-y-1">
            {items.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    active
                      ? "bg-primary/10 text-primary font-medium"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </ScrollArea>

        <div className="p-3 border-t mt-auto">
          <div className="mb-2 px-3 py-2 text-xs text-muted-foreground truncate">
            {user.email}
          </div>
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground hover:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
          <p className="text-[10px] text-muted-foreground text-center mt-3 px-2">
            This system does not provide medical advice.
          </p>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto bg-background">
        {children}
      </main>
    </div>
  );
}
