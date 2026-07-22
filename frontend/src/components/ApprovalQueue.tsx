"use client";

import { useCallback, useEffect, useState } from "react";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { CheckCircle2, ShieldAlert, XCircle, User, Stethoscope, Brain, Clock, AlertTriangle, Calendar } from "lucide-react";

const TYPE_LABELS: Record<string, string> = {
  emergency_escalation: "Emergency Escalation",
  urgent_symptoms: "Urgent Symptoms",
  late_cancellation: "Late Cancellation",
  vip_request: "VIP Request",
  manual_doctor_assignment: "Manual Doctor Assignment",
  double_booking: "Double Booking",
  low_confidence: "Low AI Confidence",
  appointment_booking: "Appointment Booking",
  other: "Other",
};

const TYPE_VARIANT: Record<string, "destructive" | "warning" | "default" | "secondary"> = {
  emergency_escalation: "destructive",
  urgent_symptoms: "destructive",
  late_cancellation: "warning",
  vip_request: "default",
  double_booking: "warning",
  low_confidence: "warning",
};

const STATUS_VARIANT: Record<string, "success" | "destructive" | "warning"> = {
  pending: "warning",
  approved: "success",
  rejected: "destructive",
};

export function ApprovalQueue() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  const [target, setTarget] = useState<any | null>(null);
  const [decision, setDecision] = useState<"approve" | "reject">("approve");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = showHistory ? await api.approvals.list() : await api.approvals.pending();
      setRequests(data);
    } catch {
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, [showHistory]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  function openDecision(request: any, kind: "approve" | "reject") {
    setTarget(request);
    setDecision(kind);
    setComment("");
  }

  async function submitDecision() {
    if (!target) return;
    setSubmitting(true);
    try {
      const action = decision === "approve" ? api.approvals.approve : api.approvals.reject;
      await action(target.id, comment || undefined);
      toast.success(decision === "approve" ? "Request approved" : "Request rejected");
      setTarget(null);
      await load();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const pendingCount = requests.filter((r) => r.status === "pending").length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-600" />
          <h2 className="text-xl font-semibold">Approval Queue</h2>
          {pendingCount > 0 && <Badge variant="warning">{pendingCount} pending</Badge>}
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowHistory((v) => !v)}>
          {showHistory ? "Show Pending Only" : "Show All (Audit)"}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="space-y-2 p-4">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>Doctor Requested</TableHead>
                  <TableHead>Appointment Time</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>AI Confidence</TableHead>
                  <TableHead>Escalation Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground">
                      {showHistory ? "No approval requests yet" : "No requests awaiting review"}
                    </TableCell>
                  </TableRow>
                )}
                {requests.map((r) => {
                  const action = r.requested_action || {};
                  const doctorName = action.doctor_name || "—";
                  const apptTime = action.scheduled_at
                    ? format(new Date(action.scheduled_at), "MMM d, yyyy h:mm a")
                    : "—";

                  return (
                    <TableRow key={r.id}>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span>{r.patient_name || "—"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <Stethoscope className="h-4 w-4 text-muted-foreground" />
                          <span>{doctorName}</span>
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{apptTime}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-48 truncate" title={r.ai_summary || r.reason || ""}>
                        <Badge variant={TYPE_VARIANT[r.request_type] || "secondary"} className="whitespace-nowrap">
                          {TYPE_LABELS[r.request_type] || r.request_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <Brain className={`h-4 w-4 ${r.ai_confidence != null && r.ai_confidence < 0.8 ? "text-red-500" : "text-green-500"}`} />
                          <span className={r.ai_confidence != null && r.ai_confidence < 0.8 ? "text-red-600 font-medium" : ""}>
                            {r.ai_confidence != null ? `${Math.round(r.ai_confidence * 100)}%` : "—"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-40 truncate" title={r.reason || ""}>
                        <div className="flex items-center gap-1.5">
                          <AlertTriangle className="h-4 w-4 text-amber-500" />
                          <span>{r.reason || "—"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[r.status] || "default"}>{r.status}</Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-4 w-4" />
                          <span>{format(new Date(r.created_at), "MMM d, h:mm a")}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {r.status === "pending" ? (
                          <div className="flex justify-end gap-2">
                            <Button size="sm" onClick={() => openDecision(r, "approve")}>
                              <CheckCircle2 className="mr-1 h-4 w-4" /> Approve
                            </Button>
                            <Button size="sm" variant="destructive" onClick={() => openDecision(r, "reject")}>
                              <XCircle className="mr-1 h-4 w-4" /> Reject
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground" title={r.reviewer_comment || ""}>
                            {r.reviewer_comment ? `"${r.reviewer_comment}"` : "—"}
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!target} onOpenChange={(open) => !open && setTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {decision === "approve" ? "Approve Request" : "Reject Request"}
            </DialogTitle>
          </DialogHeader>
          {target && (
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">
                    {TYPE_LABELS[target.request_type] || target.request_type}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">Reason:</span> {target.reason || "—"}</p>
                  <p><span className="text-muted-foreground">AI Summary:</span> {target.ai_summary || "—"}</p>
                  {target.ai_confidence != null && (
                    <p>
                      <span className="text-muted-foreground">AI Confidence:</span>{" "}
                      {Math.round(target.ai_confidence * 100)}%
                    </p>
                  )}
                  {target.requested_action?.action && (
                    <p>
                      <span className="text-muted-foreground">On approval:</span>{" "}
                      {target.requested_action.action.replace("_", " ")}
                      {target.requested_action.scheduled_at
                        ? ` — ${format(new Date(target.requested_action.scheduled_at), "MMM d, yyyy h:mm a")}`
                        : ""}
                    </p>
                  )}
                  {target.requested_action?.doctor_id && (
                    <p>
                      <span className="text-muted-foreground">Doctor ID:</span>{" "}
                      <span className="font-mono text-xs">{target.requested_action.doctor_id.slice(0, 8)}...</span>
                    </p>
                  )}
                </CardContent>
              </Card>
              <div className="space-y-2">
                <Label htmlFor="reviewer_comment">Comment (optional)</Label>
                <Input
                  id="reviewer_comment"
                  placeholder="Add a note for the audit trail…"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setTarget(null)}>
                  Cancel
                </Button>
                <Button
                  variant={decision === "reject" ? "destructive" : "default"}
                  disabled={submitting}
                  onClick={submitDecision}
                >
                  {submitting ? "Saving…" : decision === "approve" ? "Confirm Approval" : "Confirm Rejection"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
