"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { CalendarDays, Users, Mic } from "lucide-react";

export default function DoctorDashboard() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.appointments.list().then(setAppointments),
      api.patients.list().then(setPatients),
      api.voice.listSessions().then(setSessions),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-3 gap-4">
          {[1,2,3].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      </div>
    );
  }

  const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
    scheduled: "default",
    confirmed: "success",
    completed: "secondary",
    cancelled: "destructive",
    pending: "warning",
  };

  const now = new Date();
  const upcoming = appointments.filter((a) => new Date(a.scheduled_at) > now && a.status !== "cancelled");
  const past = appointments.filter((a) => new Date(a.scheduled_at) <= now || a.status === "completed");

  return (
    <div className="space-y-6">
      <WelcomeBanner />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Upcoming Appointments</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{upcoming.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Patients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{patients.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Voice Sessions</CardTitle>
            <Mic className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{sessions.length}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upcoming Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient ID</TableHead>
                <TableHead>Date & Time</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {upcoming.length === 0 && (
                <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No upcoming appointments</TableCell></TableRow>
              )}
              {upcoming.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-mono text-xs">{a.patient_id?.slice(0,8)}</TableCell>
                  <TableCell>{new Date(a.scheduled_at).toLocaleString()}</TableCell>
                  <TableCell>{a.duration_minutes} min</TableCell>
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

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Past Appointments</CardTitle>
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

        <Card>
          <CardHeader>
            <CardTitle>Voice Session Reviews</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Emergency</TableHead>
                  <TableHead>Escalated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.length === 0 && (
                  <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No voice sessions</TableCell></TableRow>
                )}
                {sessions.slice(0, 5).map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{new Date(s.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge variant={s.is_emergency ? "destructive" : "secondary"}>
                        {s.is_emergency ? "Yes" : "No"}
                      </Badge>
                    </TableCell>
                    <TableCell>{s.escalated_to_human ? "Yes" : "No"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
