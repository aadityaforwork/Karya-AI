"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../lib/auth";

export default function SignupPage() {
  const { signup } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!email.trim() || password.length < 6) {
      setErr("Enter an email and a password of at least 6 characters.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await signup(email.trim(), password, name.trim());
      router.replace("/app");
    } catch (e: any) {
      setErr(e?.message || "Signup failed");
      setBusy(false);
    }
  };

  return (
    <div className="authwrap">
      <div className="authcard">
        <a className="brand" href="/"><span className="mark">का</span>Karya</a>
        <h1>Start free</h1>
        <div className="sub">One workspace, the hiring skill, no card needed.</div>
        <div className="authform">
          {err && <div className="autherr">{err}</div>}
          <div><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Optional" /></div>
          <div><label>Email</label><input value={email} onChange={(e) => setEmail(e.target.value)} /></div>
          <div><label>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} /></div>
          <button className="btn" disabled={busy} onClick={submit}>{busy ? "Creating…" : "Create account"}</button>
        </div>
        <div className="authalt">Already have an account? <a href="/login">Log in</a></div>
      </div>
    </div>
  );
}
