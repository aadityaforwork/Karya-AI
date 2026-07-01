"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import { STAGE_LABEL, type Skill, type Stage } from "./types";

export function useSkills() {
  const [skills, setSkills] = useState<Record<string, Skill>>({});
  useEffect(() => {
    api.skills().then((r) => setSkills(Object.fromEntries(r.skills.map((s) => [s.id, s])))).catch(() => {});
  }, []);
  return skills;
}

export function stageLabel(skill: Skill | undefined, stage: string): string {
  return skill?.stage_labels?.[stage] || STAGE_LABEL[stage as Stage] || stage;
}

export const SKILL_ACCENT: Record<string, string> = {
  mint: "var(--mint)", sky: "var(--sky)", amber: "var(--amber)", teal: "var(--teal)", slate: "var(--slate)",
};
