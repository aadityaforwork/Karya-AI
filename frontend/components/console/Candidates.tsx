"use client";

import { useState } from "react";
import type { RunCandidate } from "../../lib/types";
import type { ScreenedView } from "../../lib/useKarya";
import { Check, Cross } from "../icons";

function langBadge(lang: string) {
  return lang ? <span className="badge slate mono tight">{lang}</span> : null;
}

function RichCard({ c }: { c: RunCandidate }) {
  const [open, setOpen] = useState(false);
  const verified = c.claims.filter((x) => x.status === "verified");
  return (
    <div className="cand">
      <div className="row" onClick={() => setOpen((o) => !o)}>
        <div>
          <div className="nm">
            {c.name}
            {langBadge(c.language)}
            {c.is_finalist && <span className="badge mint tight">finalist</span>}
          </div>
          <div className="meta">{c.location} · {verified.length} proven claims · {open ? "hide" : "show"} evidence</div>
        </div>
        <span className={`fit ${c.verdict}`}>{Math.round(c.fit_score * 100)}%</span>
      </div>
      {open && (
        <div className="detail">
          {c.claims.map((cl, i) => (
            <div key={i} className={`claim ${cl.status === "verified" ? "ok" : "no"}`}>
              <span className="ic">{cl.status === "verified" ? <Check /> : <Cross />}</span>
              <div>
                <div>{cl.text}</div>
                <div className="ev">
                  {cl.evidence.length > 0 ? (
                    cl.evidence.map((e) => (
                      <span key={e.n}><span className="ln mono">L{e.n}</span>{e.text}</span>
                    ))
                  ) : (
                    <em>{cl.reason}</em>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LiteCard({ c }: { c: ScreenedView }) {
  return (
    <div className="cand">
      <div className="row static">
        <div>
          <div className="nm">{c.name}{langBadge(c.language)}</div>
          <div className="meta">{c.verified.length} proven · {c.rejected.length} rejected</div>
        </div>
        <span className={`fit ${c.verdict}`}>{Math.round(c.fit * 100)}%</span>
      </div>
      {(c.verified.length > 0 || c.rejected.length > 0) && (
        <div className="detail">
          {c.verified.slice(0, 3).map((t, i) => (
            <div key={`v${i}`} className="claim ok"><span className="ic"><Check /></span><div>{t}</div></div>
          ))}
          {c.rejected.slice(0, 2).map((t, i) => (
            <div key={`r${i}`} className="claim no"><span className="ic"><Cross /></span><div>{t}</div></div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Candidates({ rich, screened }: { rich?: RunCandidate[]; screened?: ScreenedView[] }) {
  const hasRich = rich && rich.length > 0;
  const hasLite = screened && screened.length > 0;
  if (!hasRich && !hasLite) return null;
  return (
    <div className="card">
      <div className="hd"><h3>Candidates</h3></div>
      <div className="bd">
        {hasRich
          ? rich!.map((c) => <RichCard key={c.candidate_id} c={c} />)
          : screened!.map((c) => <LiteCard key={c.candidate_id} c={c} />)}
      </div>
    </div>
  );
}
