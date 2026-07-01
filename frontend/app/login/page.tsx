"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("demo@karya.ai");
  const [password, setPassword] = useState("demo1234");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setErr("");
    try {
      await login(email.trim(), password);
      router.replace("/app");
    } catch (e: any) {
      setErr(e?.message || "Login failed");
      setBusy(false);
    }
  };

  return (
    <div className="authwrap">
      <div className="authcard">
        <a className="brand" href="/"><span className="mark">का</span>Karya</a>
        <h1>Welcome back</h1>
        <div className="sub">Log in to your AI workforce.</div>
        <div className="authform">
          {err && <div className="autherr">{err}</div>}
          <div><label>Email</label><input value={email} onChange={(e) => setEmail(e.target.value)} /></div>
          <div><label>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} /></div>
          <button className="btn" disabled={busy} onClick={submit}>{busy ? "Logging in…" : "Log in"}</button>
        </div>
        <div className="demohint">Demo account is prefilled. Just hit Log in.</div>
        <div className="authalt">New here? <a href="/signup">Create an account</a></div>
      </div>
    </div>
  );
}
