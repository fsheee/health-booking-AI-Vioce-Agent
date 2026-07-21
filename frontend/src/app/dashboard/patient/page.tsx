"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { toast } from "sonner";
import { CalendarDays, Mic, Clock } from "lucide-react";

export default function PatientDashboard() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  function loadAppointments() {
    setLoading(true);
    api.appointments.listMy().then(setAppointments).finally(() => setLoading(false));
  }

  useEffect(() => { loadAppointments(); }, []);

  async function handleCancel(id: string) {
    try {
      await api.appointments.cancel(id);
      toast.success("Appointment cancelled");
      loadAppointments();
    } catch (err: any) {
      toast.error(err.message);
    }
  }

  const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
    scheduled: "default",
    confirmed: "success",
    completed: "secondary",
    cancelled: "destructive",
    pending: "warning",
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-28 rounded-xl" />
        <Skeleton className="h-28 rounded-xl" />
      </div>
    );
  }

  const now = new Date();
  const upcoming = appointments.filter((a) => new Date(a.scheduled_at) > now && a.status !== "cancelled");
  const past = appointments.filter((a) => new Date(a.scheduled_at) <= now || a.status === "completed" || a.status === "cancelled");

  return (
    <div className="space-y-6">
      <WelcomeBanner />

      <Card className="bg-gradient-to-r from-blue-500 to-cyan-400 text-white">
        <CardContent className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm opacity-90">Need help? Use the</p>
            <p className="text-xl font-semibold">AI Voice Assistant</p>
          </div>
          <Link href="/dashboard/patient/voice">
            <Button variant="secondary" size="lg" className="gap-2 bg-white text-blue-600 hover:bg-blue-50">
              <Mic className="h-5 w-5" />
              Launch
            </Button>
          </Link>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Upcoming</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{upcoming.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Past Appointments</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{past.length}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upcoming Appointments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date & Time</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {upcoming.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No upcoming appointments</TableCell></TableRow>
              )}
              {upcoming.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{new Date(a.scheduled_at).toLocaleString()}</TableCell>
                  <TableCell>{a.reason || "—"}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant[a.status] || "default"}>{a.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {a.status !== "cancelled" && (
                      <Button variant="destructive" size="sm" onClick={() => handleCancel(a.id)}>Cancel</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appointment History</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {past.length === 0 && (
                <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No past appointments</TableCell></TableRow>
              )}
              {past.slice(0, 5).map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{new Date(a.scheduled_at).toLocaleDateString()}</TableCell>
                  <TableCell>{a.reason || "—"}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant[a.status] || "default"}>{a.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
