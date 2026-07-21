"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  org_id: string;
}

export function WelcomeBanner() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auth.me()
      .then(setUser)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Skeleton className="h-20 rounded-xl" />;
  }

  if (!user) return null;

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const getDisplayName = () => {
    if (user.role === "doctor") {
      return `Dr. ${user.full_name}`;
    }
    return user.full_name;
  };

  const getEmoji = () => {
    if (user.role === "doctor") return "👨‍⚕️";
    if (user.role === "admin") return "👋";
    return "👋";
  };

  return (
    <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
      <CardContent className="flex items-center justify-between p-6">
        <div>
          <p className="text-sm text-muted-foreground">{getGreeting()}</p>
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome, {getDisplayName()} {getEmoji()}
          </h2>
        </div>
      </CardContent>
    </Card>
  );
}
