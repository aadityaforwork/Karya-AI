"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "../lib/auth";
import MarketingHeader from "./MarketingHeader";
import Nav from "./Nav";

const PUBLIC = ["/", "/pricing"];
const AUTH_PAGES = ["/login", "/signup"];

export default function Chrome({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const { user, loading } = useAuth();
  const router = useRouter();

  const isAuthPage = AUTH_PAGES.includes(path);
  const isPublic = PUBLIC.includes(path);
  const isApp = !isAuthPage && !isPublic;

  useEffect(() => {
    if (isApp && !loading && !user) router.replace("/login");
  }, [isApp, loading, user, router]);

  if (isAuthPage) return <>{children}</>;
  if (isPublic) return <><MarketingHeader />{children}</>;

  // app routes: gated
  if (loading || !user) {
    return <div className="empty" style={{ paddingTop: 120 }}>Loading your workspace…</div>;
  }
  return <><Nav />{children}</>;
}
