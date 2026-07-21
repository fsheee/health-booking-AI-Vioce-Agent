import { type NextRequest, NextResponse } from "next/server";

const publicPaths = ["/", "/login", "/signup"];

export function middleware(req: NextRequest) {
  const token = req.cookies.get("access_token")?.value;
  const { pathname } = req.nextUrl;

  if (pathname === "/" || pathname.startsWith("/login") || pathname.startsWith("/signup")) {
    if (token && pathname === "/login") {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
    return NextResponse.next();
  }

  if (!token) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
