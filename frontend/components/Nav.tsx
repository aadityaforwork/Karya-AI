"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

const LINKS = [
  { href: "/app", label: "Home" },
  { href: "/roles", label: "Workspaces" },
  { href: "/talent", label: "Talent" },
  { href: "/approvals", label: "Approvals", badge: true },
  { href: "/playground", label: "Playground" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/settings", label: "Settings" },
];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const tick = () => api.approvalsQueue().then((r) => setPending(r.approvals.length)).catch(() => {});
    tick();
    const t = setInterval(tick, 4000);
    return () => clearInterval(t);
  }, []);

  const isActive = (href: string) => (href === "/app" ? pathname === "/app" : pathname.startsWith(href));
  const signOut = () => { logout(); router.replace("/"); };

  return (
    <nav className="nav">
      <a className="brand" href="/app"><span className="mark">का</span>Karya</a>
      <div className="links">
        {LINKS.map((l) => (
          <a key={l.href} href={l.href} className={isActive(l.href) ? "active" : ""}>
            {l.label}
            {l.badge && pending > 0 && <span className="navbadge">{pending}</span>}
          </a>
        ))}
      </div>
      <span className="spacer" />
      <div className="acct">
        <a className="plan" href="/billing">{user?.plan || "free"}</a>
        <span className="who">{user?.name || user?.email}</span>
        <span className="out" onClick={signOut}>Log out</span>
      </div>
    </nav>
  );
}
