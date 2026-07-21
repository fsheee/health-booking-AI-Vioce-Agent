"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [orgSlug, setOrgSlug] = useState("");
  const [role, setRole] = useState("patient");
  const [specialization, setSpecialization] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      const { access_token } = await api.auth.signup(
        email,
        password,
        fullName,
        orgSlug,
        role,
        specialization || undefined
      );
      localStorage.setItem("access_token", access_token);
      document.cookie = `access_token=${access_token}; path=/`;
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-center">Sign Up</h1>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <input
          type="text"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full rounded border p-2"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border p-2"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border p-2"
          required
        />
        <input
          type="text"
          placeholder="Organization Slug"
          value={orgSlug}
          onChange={(e) => setOrgSlug(e.target.value)}
          className="w-full rounded border p-2"
          required
        />
        <div className="space-y-1">
          <label htmlFor="role" className="text-sm text-gray-600">
            I am a
          </label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full rounded border p-2 bg-white"
            required
          >
            <option value="patient">Patient</option>
            <option value="doctor">Doctor</option>
            <option value="front_desk">Front Desk</option>
          </select>
        </div>
        {role === "doctor" && (
          <div className="space-y-1">
            <label htmlFor="specialization" className="text-sm text-gray-600">
              Specialization
            </label>
            <select
              id="specialization"
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
              className="w-full rounded border p-2 bg-white"
              required
            >
              <option value="">Select specialization</option>
              <option value="Cardiology">Cardiology</option>
              <option value="Dermatology">Dermatology</option>
              <option value="Neurology">Neurology</option>
              <option value="General Physician">General Physician</option>
            </select>
          </div>
        )}
        <button
          type="submit"
          className="w-full rounded bg-blue-600 p-2 text-white hover:bg-blue-700"
        >
          Sign Up
        </button>
        <p className="text-sm text-center text-gray-500">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 underline">
            Login
          </Link>
        </p>
      </form>
    </main>
  );
}
