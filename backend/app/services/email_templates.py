"""Professional HTML email templates for appointment notifications."""


def _base_html(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f8; }}
    .container {{ max-width: 560px; margin: 40px auto; background: #ffffff; border-radius: 12px;
      overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    .header {{ background: #2563eb; padding: 32px 40px 24px; text-align: center; }}
    .header h1 {{ color: #ffffff; margin: 0; font-size: 22px; font-weight: 600; letter-spacing: 0.3px; }}
    .header .clinic {{ color: #bfdbfe; font-size: 13px; margin-top: 4px; }}
    .body {{ padding: 32px 40px; color: #1f2937; font-size: 15px; line-height: 1.6; }}
    .body p {{ margin: 0 0 16px; }}
    .details {{ background: #f8fafc; border-radius: 8px; padding: 20px 24px; margin: 16px 0 24px; }}
    .details table {{ width: 100%; border-collapse: collapse; }}
    .details td {{ padding: 8px 0; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
    .details td:first-child {{ color: #64748b; width: 38%; }}
    .details td:last-child {{ font-weight: 600; color: #0f172a; }}
    .details tr:last-child td {{ border-bottom: none; }}
    .footer {{ padding: 20px 40px; text-align: center; color: #94a3b8; font-size: 12px;
      border-top: 1px solid #e2e8f0; }}
    .footer p {{ margin: 4px 0; }}
    .badge {{ display: inline-block; padding: 4px 14px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
    .badge-green {{ background: #dcfce7; color: #166534; }}
    .badge-red {{ background: #fee2e2; color: #991b1b; }}
    .badge-amber {{ background: #fef3c7; color: #92400e; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Healthcare Clinic</h1>
      <p class="clinic">Your Health, Our Priority</p>
    </div>
    <div class="body">
      {body}
    </div>
    <div class="footer">
      <p>Healthcare Clinic &mdash; Providing quality care since 2024</p>
      <p>If you have any questions, please contact your clinic.</p>
    </div>
  </div>
</body>
</html>"""


def confirmation_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    appointment_id: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Confirmed"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-green">confirmed</span>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Appointment ID</td><td style="font-family: monospace;">{appointment_id[:8]}...</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please arrive 10 minutes before your scheduled time. If you need to reschedule or cancel, please contact us.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def reminder_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    appointment_id: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Reminder"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>This is a friendly reminder about your upcoming appointment.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please arrive 10 minutes before your scheduled time. If you need to reschedule or cancel, please contact us.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def cancellation_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Cancelled"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-red">cancelled</span>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td>Date</td><td>{appointment_date}</td></tr>
        <tr><td>Time</td><td>{appointment_time}</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>If this was a mistake or you would like to rebook, please contact us.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def approval_requested_email(
    staff_name: str,
    patient_name: str,
    request_type: str,
    reason: str,
    ai_summary: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Action Required: Approval Request Pending"
    body = f"""
    <p>Dear <strong>{staff_name}</strong>,</p>
    <p>A patient request needs <span class="badge badge-amber">human review</span> before it can proceed.</p>
    <div class="details">
      <table>
        <tr><td>Patient</td><td>{patient_name}</td></tr>
        <tr><td>Request Type</td><td>{request_type}</td></tr>
        <tr><td>Reason Flagged</td><td>{reason}</td></tr>
        <tr><td>AI Summary</td><td>{ai_summary}</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please review this request in the front desk dashboard's approval queue.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def approval_granted_email(
    patient_name: str,
    request_type: str,
    comment: str | None,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Your Request Has Been Approved"
    comment_row = f"<tr><td>Staff Note</td><td>{comment}</td></tr>" if comment else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your request has been <span class="badge badge-green">approved</span> by our staff.</p>
    <div class="details">
      <table>
        <tr><td>Request Type</td><td>{request_type}</td></tr>
        {comment_row}
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>If any action was pending on this request, it has now been carried out. Contact us with any questions.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def reschedule_email(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    old_date: str,
    old_time: str,
    new_date: str,
    new_time: str,
    appointment_id: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Rescheduled"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment has been <span class="badge badge-amber">rescheduled</span>.</p>
    <div class="details">
      <table>
        <tr><td>Doctor</td><td>{doctor_name}</td></tr>
        <tr><td>Specialization</td><td>{specialization}</td></tr>
        <tr><td style="color: #991b1b;">Previous Date</td><td style="color: #991b1b;">{old_date} at {old_time}</td></tr>
        <tr><td style="color: #166534;">New Date</td>
          <td style="color: #166534; font-weight: 700;">{new_date}<br>at {new_time}</td></tr>
        <tr><td>Appointment ID</td><td style="font-family: monospace;">{appointment_id[:8]}...</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please arrive 10 minutes before your new scheduled time.</p>
    <p>If you need to reschedule again or cancel, please contact us.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def hitl_under_review_email(
    patient_name: str,
    reason: str,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Request Under Review"
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>Your appointment request has been submitted and is currently</p>
    <p><span class="badge badge-amber">under review</span> by our staff.</p>
    <div class="details">
      <table>
        <tr><td>Reason for Review</td><td>{reason}</td></tr>
        <tr><td>Current Status</td><td>Pending Review</td></tr>
        <tr><td>Expected Follow-up</td><td>Our team will review your request and notify you of the decision.</td></tr>
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>If you have any questions, please contact the clinic directly.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def hitl_approved_email(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str = "Healthcare Clinic",
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
    <p>Please arrive 10 minutes before your scheduled time.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def hitl_rejected_email(
    patient_name: str,
    reason: str | None,
    reviewer_comment: str | None,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Appointment Request Rejected"
    comment_html = f"<tr><td>Staff Note</td><td>{reviewer_comment}</td></tr>" if reviewer_comment else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>After review, your appointment request was <span class="badge badge-red">not approved</span>.</p>
    <div class="details">
      <table>
        <tr><td>Rejection Reason</td><td>{reason or "Not specified"}</td></tr>
        {comment_html}
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please contact the clinic directly at <strong>{clinic_name}</strong></p>
    <p>and our staff will be happy to assist you with alternative arrangements.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)


def approval_rejected_email(
    patient_name: str,
    request_type: str,
    comment: str | None,
    clinic_name: str = "Healthcare Clinic",
) -> tuple[str, str]:
    subject = "Update on Your Request"
    comment_row = f"<tr><td>Staff Note</td><td>{comment}</td></tr>" if comment else ""
    body = f"""
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>After review, your request was <span class="badge badge-red">not approved</span>.</p>
    <div class="details">
      <table>
        <tr><td>Request Type</td><td>{request_type}</td></tr>
        {comment_row}
        <tr><td>Clinic</td><td>{clinic_name}</td></tr>
      </table>
    </div>
    <p>Please contact the clinic directly and our staff will be happy to assist you.</p>
    <p style="color: #64748b; font-size: 13px;">Thank you,<br><strong>{clinic_name}</strong></p>
    """
    return subject, _base_html(body)
