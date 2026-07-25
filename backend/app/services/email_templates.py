"""Professional HTML email templates for appointment notifications.

Every template uses a single reusable base with healthcare branding.
"""

# ruff: noqa: E501 — HTML/CSS lines are unavoidably long


def _base_html(body: str, clinic_name: str = "Healthcare Clinic",
               clinic_address: str = "", clinic_phone: str = "",
               clinic_email: str = "") -> str:
    address_line = f"<p>{clinic_address}</p>" if clinic_address else ""
    phone_line = f"<p>Phone: <a href='tel:{clinic_phone}' style='color:#2563eb;text-decoration:none;'>{clinic_phone}</a></p>" if clinic_phone else ""
    email_line = f"<p>Email: <a href='mailto:{clinic_email}' style='color:#2563eb;text-decoration:none;'>{clinic_email}</a></p>" if clinic_email else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{clinic_name}</title>
  <style>
    body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f8; -webkit-text-size-adjust: 100%; }}
    .container {{ max-width: 560px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 32px 40px 24px; text-align: center; }}
    .header .logo {{ font-size: 28px; font-weight: 700; color: #ffffff; margin: 0; letter-spacing: 0.5px; }}
    .header .tagline {{ color: #bfdbfe; font-size: 13px; margin-top: 4px; }}
    .body {{ padding: 32px 40px; color: #1f2937; font-size: 15px; line-height: 1.6; }}
    .body p {{ margin: 0 0 16px; }}
    .details {{ background: #f8fafc; border-radius: 8px; padding: 20px 24px; margin: 16px 0 24px; border: 1px solid #e2e8f0; }}
    .details table {{ width: 100%; border-collapse: collapse; }}
    .details td {{ padding: 8px 0; border-bottom: 1px solid #e2e8f0; font-size: 14px; vertical-align: top; }}
    .details td:first-child {{ color: #64748b; width: 38%; white-space: nowrap; }}
    .details td:last-child {{ font-weight: 600; color: #0f172a; }}
    .details tr:last-child td {{ border-bottom: none; }}
    .arrow-row td {{ border-bottom: none; padding: 4px 0; }}
    .arrow-row td:last-child {{ font-size: 20px; color: #2563eb; }}
    .badge {{ display: inline-block; padding: 4px 14px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
    .badge-green {{ background: #dcfce7; color: #166534; }}
    .badge-red {{ background: #fee2e2; color: #991b1b; }}
    .badge-amber {{ background: #fef3c7; color: #92400e; }}
    .badge-blue {{ background: #dbeafe; color: #1e40af; }}
    .button {{ display: inline-block; padding: 10px 24px; border-radius: 6px; background: #2563eb; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; }}
    .button:hover {{ background: #1d4ed8; }}
    .footer {{ padding: 24px 40px; text-align: center; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; background: #f8fafc; }}
    .footer p {{ margin: 4px 0; }}
    .footer a {{ color: #2563eb; text-decoration: none; }}
    .emergency-banner {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px 20px; margin: 16px 0 24px; }}
    .emergency-banner p {{ color: #991b1b; font-size: 14px; margin: 0; }}
    @media only screen and (max-width: 600px) {{ .container {{ margin: 16px; }} .header {{ padding: 24px 20px 16px; }} .body {{ padding: 24px 20px; }} .footer {{ padding: 16px 20px; }} .details td:first-child {{ width: 32%; }} }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">🩺 {clinic_name}</div>
      <p class="tagline">Your Health, Our Priority</p>
    </div>
    <div class="body">
      {body}
    </div>
    <div class="footer">
      <p><strong>{clinic_name}</strong></p>
      {address_line}
      {phone_line}
      {email_line}
      <p style="margin-top:8px;font-size:11px;color:#cbd5e1;">
        This is an automated message from {clinic_name}. Please do not reply directly to this email.
      </p>
      <p style="font-size:10px;color:#cbd5e1;">
        &copy; {clinic_name} &mdash; All rights reserved.
      </p>
    </div>
  </div>
</body>
</html>"""


def _clinic_kwargs(clinic_name: str = "Healthcare Clinic",
                   clinic_address: str = "", clinic_phone: str = "",
                   clinic_email: str = "") -> dict:
    return {
        "clinic_name": clinic_name,
        "clinic_address": clinic_address,
        "clinic_phone": clinic_phone,
        "clinic_email": clinic_email,
    }


# ---------------------------------------------------------------------------
# 1. Appointment Confirmation
# ---------------------------------------------------------------------------

def confirmation_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    appointment_id: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Confirmed"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-green">confirmed</span>.</p>
    <div class="details">
      <table>
        <tr><td>Patient</td><td>{patient_name}</td></tr>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Appointment ID</td><td style="font-family:monospace;font-size:13px;">{appointment_id[:8]}...</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p><strong>Arrival Instructions:</strong> Please arrive <strong>10 minutes early</strong> to complete check-in before your appointment.</p>
    <p style="color:#64748b;font-size:13px;">Thank you for choosing <strong>{clinic_name}</strong>.</p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 2. Appointment Cancellation
# ---------------------------------------------------------------------------

def cancellation_email(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reason: str = "",
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Cancelled"
    reason_html = f"<tr><td>Cancellation Reason</td><td>{reason}</td></tr>" if reason else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-red">cancelled</span>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        {reason_html}
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>If this was a mistake or you would like to rebook, please contact the clinic directly.</p>
    <p style="color:#64748b;font-size:13px;">We hope to serve you again soon.<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 3. Appointment Rescheduled
# ---------------------------------------------------------------------------

def reschedule_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    old_date: str,
    old_time: str,
    new_date: str,
    new_time: str,
    appointment_id: str,
    reason: str = "",
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Rescheduled"
    reason_html = f"<tr><td>Reason</td><td>{reason}</td></tr>" if reason else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-amber">rescheduled</span>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        {reason_html}
      </table>
      <table style="margin-top:8px;">
        <tr class="arrow-row"><td style="color:#991b1b;">Previous</td><td style="color:#991b1b;">{old_date} at {old_time}</td></tr>
        <tr class="arrow-row"><td style="color:#166534;">New</td><td style="color:#166534;font-weight:700;">{new_date} at {new_time}</td></tr>
        <tr><td>Appointment ID</td><td style="font-family:monospace;font-size:13px;">{appointment_id[:8]}...</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please arrive <strong>10 minutes early</strong> for your new appointment time.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 4. Reminder Email (24 Hours)
# ---------------------------------------------------------------------------

def reminder_24h_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Reminder"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>This is a friendly reminder that you have an appointment <strong>tomorrow</strong>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Location</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p><strong>Reminder Instructions:</strong></p>
    <ul style="color:#1f2937;font-size:14px;padding-left:20px;">
      <li>Please arrive <strong>10 minutes early</strong> for check-in.</li>
      <li>Bring your identification and insurance card.</li>
      <li>If you need to reschedule or cancel, please contact us at least 24 hours in advance.</li>
    </ul>
    <p style="color:#64748b;font-size:13px;">We look forward to seeing you.<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 5. Reminder Email (1 Hour)
# ---------------------------------------------------------------------------

def reminder_1h_email(
    patient_name: str,
    doctor_name: str,
    appointment_time: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Upcoming Appointment Reminder"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment is coming up <strong>in about 1 hour</strong>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please proceed to the clinic at your earliest convenience.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 6. HITL Pending Review
# ---------------------------------------------------------------------------

def hitl_under_review_email(
    patient_name: str,
    reason: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Request Under Review"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment request has been submitted and is currently <span class="badge badge-amber">under review</span> by our clinical staff.</p>
    <div class="details">
      <table>
        <tr><td>Status</td><td><span class="badge badge-amber">Pending Review</span></td></tr>
        <tr><td>Reason for Review</td><td>{reason}</td></tr>
        <tr><td>Expected Follow-up</td><td>Our team will review your request and notify you of the decision shortly.</td></tr>
      </table>
    </div>
    <p>If you have any questions, please contact the clinic directly.</p>
    <p style="color:#64748b;font-size:13px;">Thank you for your patience,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 7. HITL Approved
# ---------------------------------------------------------------------------

def hitl_approved_email(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Approved"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment request has been <span class="badge badge-green">approved</span> by our staff.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please arrive <strong>10 minutes early</strong> for your appointment.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 8. HITL Rejected
# ---------------------------------------------------------------------------

def hitl_rejected_email(
    patient_name: str,
    reason: str | None,
    reviewer_comment: str | None,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Appointment Request Update"
    comment_html = f"<tr><td>Staff Note</td><td>{reviewer_comment}</td></tr>" if reviewer_comment else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>After careful review, your appointment request was <span class="badge badge-red">not approved</span>.</p>
    <div class="details">
      <table>
        <tr><td>Reason</td><td>{reason or "Not specified"}</td></tr>
        {comment_html}
      </table>
    </div>
    <p><strong>Next Steps:</strong> Please contact the clinic directly and our staff will be happy to assist you with alternative arrangements.</p>
    <p style="color:#64748b;font-size:13px;">We apologize for any inconvenience,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# 9. Emergency Escalation
# ---------------------------------------------------------------------------

def emergency_escalation_email(
    patient_name: str,
    transcript: str,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    subject = "Emergency Request Received"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your request has been received and <span class="badge badge-red">escalated</span> to our clinical staff.</p>
    <div class="emergency-banner">
      <p><strong>If this is a life-threatening emergency, please call your local emergency services immediately.</strong></p>
    </div>
    <div class="details">
      <table>
        <tr><td>Status</td><td><span class="badge badge-red">Escalated</span></td></tr>
        <tr><td>What You Said</td><td style="font-style:italic;">"{transcript}"</td></tr>
      </table>
    </div>
    <p>A member of our clinical team will review your request and follow up as soon as possible.</p>
    <p style="color:#64748b;font-size:13px;">Stay safe,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# Staff notification: approval requested
# ---------------------------------------------------------------------------

def approval_requested_email(
    staff_name: str,
    patient_name: str,
    request_type: str,
    reason: str,
    ai_summary: str,
    ai_confidence: float | None = None,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    confidence_html = f"<tr><td>AI Confidence</td><td>{ai_confidence:.0%}</td></tr>" if ai_confidence is not None else ""
    subject = "Action Required: Approval Request Pending"
    body = f"""
    <p>Dear <strong>{staff_name}</strong>,</p>
    <p>A patient request needs <span class="badge badge-amber">human review</span> before it can proceed.</p>
    <div class="details">
      <table>
        <tr><td>Patient</td><td>{patient_name}</td></tr>
        <tr><td>Request Type</td><td><span class="badge badge-blue">{request_type}</span></td></tr>
        <tr><td>Reason Flagged</td><td>{reason}</td></tr>
        <tr><td>AI Summary</td><td>{ai_summary}</td></tr>
        {confidence_html}
      </table>
    </div>
    <p>Please review this request in the front desk dashboard's approval queue.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


# ---------------------------------------------------------------------------
# Generic approval decision (used by approval_service approve/reject)
# ---------------------------------------------------------------------------

def approval_granted_email(
    patient_name: str,
    request_type: str,
    comment: str | None,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    comment_row = f"<tr><td>Staff Note</td><td>{comment}</td></tr>" if comment else ""
    subject = "Your Request Has Been Approved"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your request has been <span class="badge badge-green">approved</span> by our staff.</p>
    <div class="details">
      <table>
        <tr><td>Request Type</td><td>{request_type}</td></tr>
        {comment_row}
      </table>
    </div>
    <p>If any action was pending on this request, it has now been carried out. Contact us with any questions.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))


def approval_rejected_email(
    patient_name: str,
    request_type: str,
    comment: str | None,
    clinic_name: str = "Healthcare Clinic",
    clinic_phone: str = "",
    clinic_address: str = "",
    clinic_email: str = "",
) -> tuple[str, str]:
    comment_row = f"<tr><td>Staff Note</td><td>{comment}</td></tr>" if comment else ""
    subject = "Update on Your Request"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>After review, your request was <span class="badge badge-red">not approved</span>.</p>
    <div class="details">
      <table>
        <tr><td>Request Type</td><td>{request_type}</td></tr>
        {comment_row}
      </table>
    </div>
    <p>Please contact the clinic directly and our staff will be happy to assist you.</p>
    <p style="color:#64748b;font-size:13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body, **_clinic_kwargs(clinic_name, clinic_address, clinic_phone, clinic_email))