import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <p className="text-gray-600 mb-8">Page not found</p>
      <Link href="/" className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
        Go Home
      </Link>
    </main>
  );
}
