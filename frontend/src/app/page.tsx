import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900">
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-900/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-xl font-bold text-white">
            <span className="text-blue-400">Healthcare</span> AI
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/login"
              className="rounded-lg border border-blue-400/40 px-5 py-2 text-sm font-medium text-blue-300 hover:bg-blue-500/10"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-blue-500 px-5 py-2 text-sm font-medium text-white hover:bg-blue-600"
            >
              Sign Up
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative mx-auto max-w-6xl px-6 pt-32 pb-40 text-center">
        {/* Glow effect */}
        <div className="absolute inset-x-0 top-20 mx-auto h-72 w-72 rounded-full bg-blue-500/20 blur-[100px]" />

        <h1 className="relative text-5xl font-extrabold tracking-tight text-white sm:text-6xl">
          Healthcare AI{" "}
          <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Voice Agent
          </span>
        </h1>
        <p className="relative mx-auto mt-6 max-w-2xl text-lg text-blue-200/80">
          Multi-tenant SaaS platform for clinics and healthcare providers.
          AI-powered voice agent for appointment booking, patient management, and reminders.
        </p>
        <div className="relative mt-10 flex items-center justify-center gap-4">
          <Link
            href="/signup"
            className="rounded-lg bg-gradient-to-r from-blue-500 to-cyan-400 px-8 py-3 text-base font-semibold text-white shadow-lg shadow-blue-500/30 hover:from-blue-600 hover:to-cyan-500"
          >
            Get Started Free
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-white/20 bg-white/5 px-8 py-3 text-base font-semibold text-white backdrop-blur-sm hover:bg-white/10"
          >
            Sign In
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-white/10 bg-slate-800/50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold text-white">Everything you need</h2>
          <p className="mx-auto mt-4 max-w-xl text-center text-blue-300/70">
            Manage your clinic efficiently with our integrated platform.
          </p>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              title="AI Voice Agent"
              desc="Patients can book appointments, check availability, and get reminders using natural speech."
            />
            <FeatureCard
              title="Appointment Management"
              desc="Full calendar management with availability checking, scheduling, and automated reminders."
            />
            <FeatureCard
              title="Patient Management"
              desc="Comprehensive patient profiles with medical history, emergency contacts, and search."
            />
            <FeatureCard
              title="Multi-Tenant"
              desc="Organization-based isolation with role-based access control for admins, doctors, and staff."
            />
            <FeatureCard
              title="Smart Reminders"
              desc="Automated appointment, follow-up, and medication reminders via SMS, email, or voice."
            />
            <FeatureCard
              title="Emergency Escalation"
              desc="AI detects emergency keywords and instantly escalates to human staff with full context."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-slate-900 py-12">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-xs text-blue-300/50">
            This application is for informational and administrative purposes only.
            It does not provide medical advice, diagnosis, or treatment.
            If you are experiencing a medical emergency, call 911 immediately.
          </p>
          <p className="mt-4 text-xs text-blue-300/40">
            &copy; {new Date().getFullYear()} Healthcare AI Voice Agent. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-left shadow-sm backdrop-blur-sm transition hover:border-blue-400/30 hover:bg-white/10">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-blue-200/60">{desc}</p>
    </div>
  );
}
