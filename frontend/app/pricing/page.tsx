"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Plan } from "../../lib/types";
import { Check } from "../../components/icons";

export default function PricingPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    api.plans().then((r) => setPlans(r.plans)).catch(() => {});
  }, []);

  return (
    <div className="page">
      <div className="lead center">
        <h1>Pricing that scales with the work</h1>
        <p>Every plan runs on the same cost-aware engine. You only pay for the seats and skills you use.</p>
      </div>

      <div className="plans">
        {plans.map((p) => (
          <div className={`plancard ${p.id === "pro" ? "featured" : ""}`} key={p.id}>
            <div className="pname plancard-title">{p.name} {p.id === "pro" && <span className="badge mint tight">popular</span>}</div>
            <div className="pprice">${p.price_usd}<span>/mo</span></div>
            <div className="ptag">{p.tagline}</div>
            <div className="featlist">
              {p.features.map((f) => <div className="feat" key={f}><span className="ic"><Check size={13} /></span>{f}</div>)}
            </div>
            <a className={`btn ${p.id === "free" ? "ghost" : ""}`} href={user ? "/billing" : "/signup"}>
              {user ? (user.plan === p.id ? "Current plan" : `Choose ${p.name}`) : p.price_usd === 0 ? "Start free" : `Get ${p.name}`}
            </a>
          </div>
        ))}
      </div>

      <p className="finemuted">
        Payments are mocked in this build. Choosing a plan switches you instantly so you can explore every tier.
      </p>
    </div>
  );
}
