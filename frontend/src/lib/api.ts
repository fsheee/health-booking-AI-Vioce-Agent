const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string>),
  };
  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  auth: {
    login: (email: string, password: string, role?: string) =>
      request<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, ...(role ? { role } : {}) }),
      }),
    signup: (email: string, password: string, full_name: string, org_slug: string, role: string, specialization?: string) =>
      request<{ access_token: string }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name, org_slug, role, ...(specialization ? { specialization } : {}) }),
      }),
    me: () => request<{ id: string; email: string; full_name: string; role: string; org_id: string }>("/auth/me"),
  },
  patients: {
    list: (search?: string) =>
      request<any[]>("/patients" + (search ? `?search=${search}` : "")),
    create: (data: any) =>
      request<any>("/patients", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => request<any>(`/patients/${id}`),
    getMe: () => request<any>("/patients/me"),
    update: (id: string, data: any) =>
      request<any>(`/patients/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  },
  appointments: {
    list: () => request<any[]>("/appointments"),
    listMy: () => request<any[]>("/appointments/my"),
    create: (data: any) =>
      request<any>("/appointments", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => request<any>(`/appointments/${id}`),
    update: (id: string, data: any) =>
      request<any>(`/appointments/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    cancel: (id: string) =>
      request<any>(`/appointments/${id}`, { method: "DELETE" }),
    reschedule: (id: string, data: { scheduled_at: string; reason?: string }) =>
      request<any>(`/appointments/${id}/reschedule`, { method: "PUT", body: JSON.stringify(data) }),
  },
  doctors: {
    list: () => request<any[]>("/doctors"),
    get: (id: string) => request<any>(`/doctors/${id}`),
    getAvailability: (id: string, date: string) =>
      request<any[]>(`/doctors/${id}/availability?date=${date}`),
  },
  approvals: {
    list: (status?: string) =>
      request<any[]>("/approvals" + (status ? `?status=${status}` : "")),
    pending: () => request<any[]>("/approvals/pending"),
    get: (id: string) => request<any>(`/approvals/${id}`),
    approve: (id: string, comment?: string) =>
      request<any>(`/approvals/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ comment: comment || null }),
      }),
    reject: (id: string, comment?: string) =>
      request<any>(`/approvals/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ comment: comment || null }),
      }),
  },
  voice: {
    startSession: (patient_id: string) =>
      request<any>("/voice/sessions", {
        method: "POST",
        body: JSON.stringify({ patient_id }),
      }),
    process: (session_id: string, audio_base64: string) =>
      request<any>("/voice/process", {
        method: "POST",
        body: JSON.stringify({ session_id, audio_base64 }),
      }),
    listSessions: () => request<any[]>("/voice/sessions"),
    getSession: (id: string) => request<any>(`/voice/sessions/${id}`),
  },
};
