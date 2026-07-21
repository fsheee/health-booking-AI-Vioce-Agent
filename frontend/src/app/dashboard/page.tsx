"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const rolePaths: Record<string, string> = {
  admin: "/dashboard/admin",
  doctor: "/dashboard/doctor",
  front_desk: "/dashboard/front-desk",
  patient: "/dashboard/patient",
};

export default function DashboardRedirect() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    api.auth.me().then((u) => {
      setUser(u);
      router.push(rolePaths[u.role] ?? "/dashboard/patient");
    }).catch(() => {
      localStorage.removeItem("access_token");
      document.cookie = "access_token=; path=/; max-age=0";
      router.push("/login");
    });
  }, [router]);

  return <div className="p-8">Redirecting...</div>;
}
