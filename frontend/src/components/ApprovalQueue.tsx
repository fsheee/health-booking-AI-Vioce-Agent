"use client";

import { useCallback, useEffect, useState } from "react";
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
import { CheckCircle2, ShieldAlert, XCircle } from "lucide-react";

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

  // Decision dialog state
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
    // The AI queues requests in the background — keep the list fresh.
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
              {[1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Reason Flagged</TableHead>
                  <TableHead>AI Summary</TableHead>
                  <TableHead>Requested</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      {showHistory ? "No approval requests yet" : "No requests awaiting review"}
                    </TableCell>
                  </TableRow>
                )}
                {requests.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>
                      <Badge variant={TYPE_VARIANT[r.request_type] || "secondary"}>
                        {TYPE_LABELS[r.request_type] || r.request_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-56 truncate" title={r.reason || ""}>
                      {r.reason || "—"}
                    </TableCell>
                    <TableCell className="max-w-64 truncate" title={r.ai_summary || ""}>
                      {r.ai_summary || "—"}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                      {new Date(r.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[r.status] || "default"}>{r.status}</Badge>
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
                ))}
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
                        ? ` — ${new Date(target.requested_action.scheduled_at).toLocaleString()}`
                        : ""}
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
