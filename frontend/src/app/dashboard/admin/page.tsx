"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { ApprovalQueue } from "@/components/ApprovalQueue";
import {
  Users,
  CalendarClock,
  Stethoscope,
  Mic,
  UserCog,
  FileText,
  BarChart3,
  Building2,
  Mail,
  AlertTriangle,
} from "lucide-react";

const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  scheduled: "default",
  confirmed: "success",
  completed: "secondary",
  cancelled: "destructive",
  pending: "warning",
};

export default function AdminDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard.get().then(setData).finally(() => setLoading(false));
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

  if (!data) return null;

  const stats = [
    { label: "Total Patients", value: data.total_patients, icon: Users },
    { label: "Total Appointments", value: data.total_appointments, icon: CalendarClock },
    { label: "Doctors", value: data.total_doctors, icon: Stethoscope },
    { label: "Voice Sessions", value: data.voice_sessions?.length || 0, icon: Mic },
  ];

  return (
    <div className="space-y-6">
      <WelcomeBanner />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{s.label}</CardTitle>
              <s.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <ApprovalQueue />

      <Card>
        <CardHeader>
          <CardTitle>Appointments ({data.total_appointments})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Doctor</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.appointments?.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No appointments</TableCell></TableRow>
              )}
              {data.appointments?.map((a: any) => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium">{a.patient_name || a.patient_id?.slice(0, 8) || "—"}</TableCell>
                  <TableCell>{a.doctor_name || "—"}</TableCell>
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
          <CardTitle>Patients ({data.total_patients})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.patients?.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No patients</TableCell></TableRow>
              )}
              {data.patients?.map((p: any) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.first_name} {p.last_name}</TableCell>
                  <TableCell>{p.phone || "—"}</TableCell>
                  <TableCell>{p.email || "—"}</TableCell>
                  <TableCell>{new Date(p.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {data.total_users != null && (
        <>
          <h2 className="text-xl font-semibold pt-4">Admin Overview</h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
                <UserCog className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.total_users}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Pending HITL</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.pending_hitl_requests?.length || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Voice Sessions</CardTitle>
                <Mic className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.system_statistics?.total_voice_sessions || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Approvals</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.system_statistics?.total_approval_requests || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Audit Events</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.system_statistics?.total_audit_logs || 0}</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Organization
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.organization_details ? (
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between"><dt className="text-muted-foreground">Name</dt><dd>{data.organization_details.name}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Slug</dt><dd>{data.organization_details.slug}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Phone</dt><dd>{data.organization_details.phone || "—"}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Email</dt><dd>{data.organization_details.email || "—"}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Address</dt><dd>{data.organization_details.address || "—"}</dd></div>
                  </dl>
                ) : (
                  <p className="text-sm text-muted-foreground">No organization details</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.email_notification_statistics ? (
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between"><dt className="text-muted-foreground">Sent</dt><dd className="font-medium text-green-600">{data.email_notification_statistics.total_sent}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Failed</dt><dd className="font-medium text-red-600">{data.email_notification_statistics.total_failed}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Pending</dt><dd className="font-medium text-amber-600">{data.email_notification_statistics.total_pending}</dd></div>
                  </dl>
                ) : (
                  <p className="text-sm text-muted-foreground">No email data</p>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                System Statistics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { label: "Appointments Today", value: data.system_statistics?.total_appointments_today },
                  { label: "Appointments This Week", value: data.system_statistics?.total_appointments_this_week },
                  { label: "Total Reminders", value: data.system_statistics?.total_reminders },
                  { label: "Voice Sessions", value: data.system_statistics?.total_voice_sessions },
                  { label: "Approval Requests", value: data.system_statistics?.total_approval_requests },
                  { label: "Audit Events", value: data.system_statistics?.total_audit_logs },
                ].map((s) => (
                  <div key={s.label} className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-2xl font-bold">{s.value ?? 0}</p>
                    <p className="text-xs text-muted-foreground">{s.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Recent Audit Logs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.audit_logs?.length === 0 && (
                    <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No audit logs</TableCell></TableRow>
                  )}
                  {data.audit_logs?.slice(0, 10).map((log: any) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs">{log.action}</TableCell>
                      <TableCell>{log.resource_type}</TableCell>
                      <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
