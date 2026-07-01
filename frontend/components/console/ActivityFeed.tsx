"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { PLANE_COLOR, type KaryaEvent, type Plane } from "../../lib/types";

const PLANES: Plane[] = ["interface", "orchestration", "execution", "trust", "state"];

export default function ActivityFeed({ events, autoscroll = true }: { events: KaryaEvent[]; autoscroll?: boolean }) {
  const [off, setOff] = useState<Set<Plane>>(new Set());
  const ref = useRef<HTMLDivElement>(null);

  const shown = useMemo(() => events.filter((e) => !off.has(e.plane)), [events, off]);

  useEffect(() => {
    if (autoscroll) ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [shown.length, autoscroll]);

  const toggle = (p: Plane) =>
    setOff((s) => {
      const n = new Set(s);
      n.has(p) ? n.delete(p) : n.add(p);
      return n;
    });

  return (
    <div className="card">
      <div className="hd">
        <h3>Live activity</h3>
        <div className="feed-tools">
          {PLANES.map((p) => (
            <button key={p} className={`filter ${off.has(p) ? "" : "on"}`} onClick={() => toggle(p)} style={{ color: off.has(p) ? undefined : PLANE_COLOR[p] }}>
              {p}
            </button>
          ))}
        </div>
      </div>
      <div className="feed" ref={ref}>
        {shown.length === 0 && <div className="empty">Describe a hiring outcome and watch the workers run it, step by step.</div>}
        {shown.map((e) => (
          <div key={e.seq} className={`evt l-${e.level}`} style={{ borderLeftColor: PLANE_COLOR[e.plane] }}>
            <span className="pl mono" style={{ color: PLANE_COLOR[e.plane] }}>{e.plane}</span>
            <span className="tx">{e.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
