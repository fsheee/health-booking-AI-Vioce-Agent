"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { Users, CalendarClock, Stethoscope, Mic } from "lucide-react";

export default function AdminDashboard() {
  const [stats, setStats] = useState({ patients: 0, appointments: 0, doctors: 0, sessions: 0 });
  const [appointments, setAppointments] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.patients.list().then((p) => {
        setPatients(p);
        setStats((s) => ({ ...s, patients: p.length }));
      }),
      api.appointments.list().then((a) => {
        setAppointments(a);
        setStats((s) => ({ ...s, appointments: a.length }));
      }),
      api.doctors.list().then((d) => setStats((s) => ({ ...s, doctors: d.length }))),
      api.voice.listSessions().then((v) => setStats((s) => ({ ...s, sessions: v.length }))),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
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

  return (
    <div className="space-y-6">
      <WelcomeBanner />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Patients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.patients}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Appointments</CardTitle>
            <CalendarClock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.appointments}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Doctors</CardTitle>
            <Stethoscope className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.doctors}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Voice Sessions</CardTitle>
            <Mic className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.sessions}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.length === 0 && (
                  <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No appointments</TableCell></TableRow>
                )}
                {appointments.slice(0, 5).map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">
                      {a.patient_name || a.patient_id?.slice(0,8) || "—"}
                    </TableCell>
                    <TableCell>{new Date(a.scheduled_at).toLocaleDateString()}</TableCell>
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
            <CardTitle>Recent Patients</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.length === 0 && (
                  <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No patients</TableCell></TableRow>
                )}
                {patients.slice(0, 5).map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.first_name} {p.last_name}</TableCell>
                    <TableCell>{p.phone || "—"}</TableCell>
                    <TableCell>{new Date(p.created_at).toLocaleDateString()}</TableCell>
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
