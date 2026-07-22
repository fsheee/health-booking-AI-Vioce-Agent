"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { CalendarDays, Mic, Clock, Stethoscope, User, FileText, Calendar, XCircle, RefreshCw } from "lucide-react";

export default function PatientDashboard() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Reschedule dialog state
  const [rescheduleTarget, setRescheduleTarget] = useState<any | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState("");
  const [rescheduleTime, setRescheduleTime] = useState("");
  const [rescheduleReason, setRescheduleReason] = useState("");
  const [resubmitting, setResubmitting] = useState(false);

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

  async function handleReschedule(e: React.FormEvent) {
    e.preventDefault();
    if (!rescheduleTarget || !rescheduleDate || !rescheduleTime) {
      toast.error("Please select a date and time");
      return;
    }
    setResubmitting(true);
    try {
      const [hours, minutes] = rescheduleTime.split(":").map(Number);
      const scheduledAt = new Date(rescheduleDate);
      scheduledAt.setHours(hours, minutes, 0, 0);

      await api.appointments.reschedule(rescheduleTarget.id, {
        scheduled_at: scheduledAt.toISOString(),
        reason: rescheduleReason || undefined,
      });
      toast.success("Appointment rescheduled successfully");
      setRescheduleTarget(null);
      setRescheduleDate("");
      setRescheduleTime("");
      setRescheduleReason("");
      loadAppointments();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setResubmitting(false);
    }
  }

  function openReschedule(appt: any) {
    const d = new Date(appt.scheduled_at);
    setRescheduleDate(format(d, "yyyy-MM-dd"));
    setRescheduleTime(format(d, "HH:mm"));
    setRescheduleReason("");
    setRescheduleTarget(appt);
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
  const upcoming = appointments.filter(
    (a) => new Date(a.scheduled_at) > now && a.status !== "cancelled" && a.status !== "completed"
  );
  const past = appointments.filter(
    (a) => new Date(a.scheduled_at) <= now || a.status === "completed" || a.status === "cancelled"
  );

  function AppointmentCard({ a, isPast }: { a: any; isPast: boolean }) {
    const d = new Date(a.scheduled_at);
    const dateStr = format(d, "MMMM d, yyyy");
    const timeStr = format(d, "h:mm a");
    const statusText =
      a.status === "scheduled" ? "Scheduled" :
      a.status === "confirmed" ? "Confirmed" :
      a.status === "completed" ? "Completed" :
      a.status === "cancelled" ? "Cancelled" : a.status;

    return (
      <Card className={isPast ? "opacity-75" : ""}>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-semibold text-base">{a.doctor_name || "Doctor"}</p>
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <Stethoscope className="h-3.5 w-3.5" />
                  {a.specialization || "General"}
                </p>
              </div>
            </div>
            <Badge variant={statusVariant[a.status] || "default"}>{statusText}</Badge>
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>{dateStr}</span>
            </div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{timeStr}</span>
            </div>
          </div>

          {a.reason && (
            <div className="flex items-start gap-1.5 text-sm text-muted-foreground">
              <FileText className="h-4 w-4 mt-0.5 shrink-0" />
              <span>Reason: {a.reason}</span>
            </div>
          )}

          {!isPast && a.status !== "cancelled" && (
            <div className="flex gap-2 pt-1">
              <Button variant="destructive" size="sm" onClick={() => handleCancel(a.id)}>
                <XCircle className="h-4 w-4 mr-1" /> Cancel
              </Button>
              <Button variant="outline" size="sm" onClick={() => openReschedule(a)}>
                <RefreshCw className="h-4 w-4 mr-1" /> Reschedule
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

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

      <div>
        <h2 className="text-xl font-semibold mb-4">Upcoming Appointments</h2>
        {upcoming.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              No upcoming appointments
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {upcoming.map((a) => (
              <AppointmentCard key={a.id} a={a} isPast={false} />
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Appointment History</h2>
        {past.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              No past appointments
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {past.slice(0, 10).map((a) => (
              <AppointmentCard key={a.id} a={a} isPast={true} />
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!rescheduleTarget} onOpenChange={(open) => !open && setRescheduleTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Reschedule Appointment</DialogTitle>
          </DialogHeader>
          {rescheduleTarget && (
            <form onSubmit={handleReschedule} className="space-y-4">
              <div className="text-sm text-muted-foreground">
                {rescheduleTarget.doctor_name && (
                  <p>Doctor: <strong>{rescheduleTarget.doctor_name}</strong></p>
                )}
                <p>
                  Current: <strong>{format(new Date(rescheduleTarget.scheduled_at), "MMMM d, yyyy 'at' h:mm a")}</strong>
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="reschedule-date">New Date</Label>
                <Input
                  id="reschedule-date"
                  type="date"
                  value={rescheduleDate}
                  onChange={(e) => setRescheduleDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reschedule-time">New Time</Label>
                <Input
                  id="reschedule-time"
                  type="time"
                  value={rescheduleTime}
                  onChange={(e) => setRescheduleTime(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reschedule-reason">Reason (optional)</Label>
                <Input
                  id="reschedule-reason"
                  value={rescheduleReason}
                  onChange={(e) => setRescheduleReason(e.target.value)}
                  placeholder="Why are you rescheduling?"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setRescheduleTarget(null)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={resubmitting}>
                  {resubmitting ? "Saving..." : "Confirm Reschedule"}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
