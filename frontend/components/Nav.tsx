"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Home, Grid, Users, Inbox, Play, Book, Cog, Menu, Cross } from "./icons";

const LINKS = [
  { href: "/app", label: "Home", icon: Home },
  { href: "/roles", label: "Workspaces", icon: Grid },
  { href: "/talent", label: "Talent", icon: Users },
  { href: "/approvals", label: "Approvals", icon: Inbox, badge: true },
  { href: "/playground", label: "Playground", icon: Play },
  { href: "/how-it-works", label: "How it works", icon: Book },
  { href: "/settings", label: "Settings", icon: Cog },
];

// N3 side rail — the app shell's nav. Deliberately a different register
// from the marketing N5 floating pill: this is the signed-in workbench,
// not the public front door. Collapses to a top bar + slide-out sheet
// below 60rem. See design.md § Nav and footer voice.
export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [pending, setPending] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const tick = () => api.approvalsQueue().then((r) => setPending(r.approvals.length)).catch(() => {});
    tick();
    const t = setInterval(tick, 4000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => { setOpen(false); }, [pathname]);

  const isActive = (href: string) => (href === "/app" ? pathname === "/app" : pathname.startsWith(href));
  const signOut = () => { logout(); router.replace("/"); };

  const rail = (
    <nav className={`rail${open ? " open" : ""}`}>
      <a className="brand" href="/app"><span className="mark">का</span>Karya</a>
      <div className="rail-links">
        {LINKS.map((l) => {
          const Icon = l.icon;
          const active = isActive(l.href);
          return (
            <a key={l.href} href={l.href} className={`rail-link${active ? " active" : ""}`}>
              <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Icon size={16} />{l.label}
              </span>
              {l.badge && pending > 0 && <span className="rail-badge">{pending}</span>}
            </a>
          );
        })}
      </div>
      <div className="rail-foot">
        <a className="rail-plan" href="/billing">{user?.plan || "free"}</a>
        <span className="rail-who">{user?.name || user?.email}</span>
        <span className="rail-out" onClick={signOut}>Log out</span>
      </div>
    </nav>
  );

  return (
    <>
      <div className="rail-topbar">
        <button aria-label="Open menu" onClick={() => setOpen((v) => !v)}>
          {open ? <Cross size={18} /> : <Menu size={18} />}
        </button>
        <a className="brand" href="/app" style={{ fontSize: 16 }}><span className="mark">का</span>Karya</a>
        <span style={{ width: 44 }} />
      </div>
      {rail}
    </>
  );
}
