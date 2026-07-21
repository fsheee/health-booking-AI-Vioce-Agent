"use client";

import { useEffect, useState, useCallback } from "react";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { ApprovalQueue } from "@/components/ApprovalQueue";
import { toast } from "sonner";
import { CalendarDays, Plus, CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export default function FrontDeskDashboard() {
  const [patients, setPatients] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showPatientForm, setShowPatientForm] = useState(false);
  const [showApptForm, setShowApptForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const [apptPatientId, setApptPatientId] = useState("");
  const [apptDoctorId, setApptDoctorId] = useState("");
  const [apptDate, setApptDate] = useState<Date | undefined>(undefined);
  const [apptTime, setApptTime] = useState("");
  const [apptReason, setApptReason] = useState("");
  const [apptDuration, setApptDuration] = useState(30);

  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);

  const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
    scheduled: "default",
    confirmed: "success",
    completed: "secondary",
    cancelled: "destructive",
    pending: "warning",
  };

  useEffect(() => {
    Promise.all([
      api.patients.list().then(setPatients),
      api.appointments.list().then(setAppointments),
      api.doctors.list().then(setDoctors),
    ]).finally(() => setLoading(false));
  }, []);

  const fetchAvailability = useCallback(async (doctorId: string, date: Date) => {
    if (!doctorId || !date) return;
    setSlotsLoading(true);
    setApptTime("");
    try {
      const dateStr = format(date, "yyyy-MM-dd");
      const result = await api.doctors.getAvailability(doctorId, dateStr);
      const slots = result[0]?.slots || [];
      setAvailableSlots(slots);
    } catch {
      setAvailableSlots([]);
    } finally {
      setSlotsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (apptDoctorId && apptDate) {
      fetchAvailability(apptDoctorId, apptDate);
    } else {
      setAvailableSlots([]);
    }
  }, [apptDoctorId, apptDate, fetchAvailability]);

  async function handleCreatePatient(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const data = {
      first_name: form.get("first_name") as string,
      last_name: form.get("last_name") as string,
      phone: form.get("phone") as string,
      email: form.get("email") as string,
      address: form.get("address") as string,
      medical_history: form.get("medical_history") as string,
      emergency_contact: form.get("emergency_contact") as string,
    };
    try {
      const patient = await api.patients.create(data);
      setPatients((prev) => [patient, ...prev]);
      toast.success("Patient registered successfully");
      setShowPatientForm(false);
    } catch (err: any) {
      toast.error(err.message);
    }
  }

  async function handleCreateAppointment(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!apptDate || !apptTime) {
      toast.error("Please select a date and time slot");
      return;
    }
    const [hours, minutes] = apptTime.split(":").map(Number);
    const scheduledAt = new Date(apptDate);
    scheduledAt.setHours(hours, minutes, 0, 0);

    try {
      const appt = await api.appointments.create({
        patient_id: apptPatientId,
        doctor_id: apptDoctorId,
        scheduled_at: scheduledAt.toISOString(),
        duration_minutes: apptDuration,
        reason: apptReason || undefined,
      });
      setAppointments((prev) => [appt, ...prev]);
      toast.success("Appointment booked successfully");
      setShowApptForm(false);
      setApptPatientId("");
      setApptDoctorId("");
      setApptDate(undefined);
      setApptTime("");
      setApptReason("");
      setApptDuration(30);
      setAvailableSlots([]);
    } catch (err: any) {
      toast.error(err.message);
    }
  }

  const filteredPatients = searchTerm
    ? patients.filter((p) =>
        `${p.first_name} ${p.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : patients;

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 gap-4">
          {[1,2].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <WelcomeBanner />

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Patients</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{patients.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Appointments Today</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {appointments.filter((a) => {
                const d = new Date(a.scheduled_at);
                const today = new Date();
                return d.toDateString() === today.toDateString();
              }).length}
            </p>
          </CardContent>
        </Card>
      </div>

      <ApprovalQueue />

      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">Patients</h2>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search patients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-60"
          />
          <Dialog open={showPatientForm} onOpenChange={setShowPatientForm}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-1" /> Register Patient</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Register New Patient</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreatePatient} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input id="first_name" name="first_name" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input id="last_name" name="last_name" required />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" name="phone" type="tel" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" name="email" type="email" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input id="address" name="address" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="medical_history">Medical History</Label>
                  <Input id="medical_history" name="medical_history" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="emergency_contact">Emergency Contact</Label>
                  <Input id="emergency_contact" name="emergency_contact" />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => setShowPatientForm(false)}>Cancel</Button>
                  <Button type="submit">Register</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
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
              {filteredPatients.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No patients found</TableCell></TableRow>
              )}
              {filteredPatients.map((p) => (
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

      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">Appointments</h2>
        <Dialog open={showApptForm} onOpenChange={setShowApptForm}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-1" /> Book Appointment</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Book New Appointment</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateAppointment} className="space-y-4">
              <div className="space-y-2">
                <Label>Patient *</Label>
                <Select value={apptPatientId} onValueChange={setApptPatientId}>
                  <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                  <SelectContent>
                    {patients.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.first_name} {p.last_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Doctor *</Label>
                <Select value={apptDoctorId} onValueChange={setApptDoctorId}>
                  <SelectTrigger><SelectValue placeholder="Select doctor" /></SelectTrigger>
                  <SelectContent>
                    {doctors.map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.full_name || "Doctor"}
                        {d.specialization ? ` — ${d.specialization}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Date *</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn("w-full justify-start text-left font-normal", !apptDate && "text-muted-foreground")}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {apptDate ? format(apptDate, "PPP") : "Pick a date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={apptDate}
                      onSelect={setApptDate}
                      disabled={(date) => date < new Date(new Date().setHours(0,0,0,0))}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
              {apptDoctorId && apptDate && (
                <div className="space-y-2">
                  <Label>Available Time Slots</Label>
                  {slotsLoading ? (
                    <div className="flex gap-2 flex-wrap"><Skeleton className="h-9 w-20" /><Skeleton className="h-9 w-20" /><Skeleton className="h-9 w-20" /></div>
                  ) : availableSlots.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No available slots for this date</p>
                  ) : (
                    <div className="flex gap-2 flex-wrap">
                      {availableSlots.map((slot) => (
                        <Button
                          key={slot}
                          type="button"
                          variant={apptTime === slot ? "default" : "outline"}
                          size="sm"
                          onClick={() => setApptTime(slot)}
                        >
                          {slot}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="duration_minutes">Duration (minutes)</Label>
                <Input id="duration_minutes" name="duration_minutes" type="number" value={apptDuration} onChange={(e) => setApptDuration(Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Reason</Label>
                <Input id="reason" name="reason" value={apptReason} onChange={(e) => setApptReason(e.target.value)} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowApptForm(false)}>Cancel</Button>
                <Button type="submit">Book</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {appointments.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No appointments</TableCell></TableRow>
              )}
              {appointments.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-mono text-xs">{a.patient_id?.slice(0,8)}</TableCell>
                  <TableCell>{new Date(a.scheduled_at).toLocaleString()}</TableCell>
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
