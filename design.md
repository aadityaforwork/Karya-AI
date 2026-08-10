# Design — Karya

A locked design system for this app. Every page redesign reads this file before
emitting code. Do not regenerate per page — extend or amend this file when the
system needs to grow.

## Genre
atmospheric

## Macrostructure family
- Marketing pages (`/`, `/pricing`, `/how-it-works`): Marquee Hero base, with
  `/how-it-works` varying to Narrative Workflow (its 5 planes are genuinely
  ordinal — the one page allowed numbered stages).
- App pages (`/app`, `/roles`, `/roles/[id]`, `/talent`, `/approvals`,
  `/playground`, `/billing`, `/settings`): Workbench. Function carries the
  page; no enrichment.
- Auth pages (`/login`, `/signup`): Workbench family, quiet knob — single
  card on the bare canvas, no chrome.

## Theme — Midnight, jade variant
- `--paper`      oklch(16% 0.02 275)
- `--paper-2`    oklch(20% 0.021 275)
- `--paper-3`    oklch(24% 0.022 275)
- `--well`       oklch(13% 0.018 275)
- `--ink`        oklch(95% 0.008 275)
- `--ink-2`      oklch(78% 0.010 275)
- `--muted`      oklch(62% 0.012 275)
- `--faint`      oklch(48% 0.012 275)
- `--line`       oklch(27% 0.016 275)
- `--line-2`     oklch(34% 0.018 275)
- `--accent`     oklch(78% 0.17 165)   (jade)
- `--accent-2`   oklch(68% 0.16 165)
- `--accent-ink` oklch(18% 0.04 165)
- `--accent-dim` oklch(30% 0.05 165)
- `--focus`      oklch(84% 0.15 165)

Axes: paper-band dark · display classical-serif · accent-hue chromatic-other (jade).

**The on-shift rule.** `--accent` marks live/active state only — a run in
flight, an open SSE stream, a pending approval, the selected filter, focus.
It is not decorative brand colour. Keeps accent coverage under 5% per
viewport without policing it, and gives jade a job on an agent platform.

**Elevation is by lightness, never shadow.** The whole depth language is
`--well` → `--paper` → `--paper-2` → `--paper-3`. No glow shadows on dark
surfaces — that is a critical anti-pattern on dark canvases.

**Status tokens keep their existing names**, re-derived for dark (hue held,
lightness lifted to ~78%, `-bg` pairs become ~24% L / 0.04 C tints):
`--green --sky --amber --rose --teal --slate` (+ `-bg` pairs), and the
`--mint`/`--mint-bg` legacy alias. `lib/useSkills.ts` (`SKILL_ACCENT`),
`lib/types.ts` (`PLANE_COLOR`), and `lib/ui.ts` (`statusBadge()`) return
these names as raw strings at runtime — renaming any of them breaks colour
silently in JS, not at build time. Never rename these.

## Typography
- Display: **Instrument Serif**, weight 400 only, style normal (roman only)
- Body:    **Instrument Sans**, weight 400/500/600 (variable, wght 400–700)
- Mono:    **IBM Plex Mono**, weight 400/500 — a real voice, not a fallback:
  every cost figure, model-tier count, run ID, percentage, and `L#` evidence
  citation renders in mono with `font-variant-numeric: tabular-nums`. It also
  carries the whole small-caps label register (`.label`, `.pill`, panel
  headers, `.who` speaker tags) at `--track-label`.
- Display tracking: `--track-display: -0.022em`. Label tracking: `+0.12em`.
- Type scale anchor: `--text-display: clamp(2.6rem, 5.4vw + 0.9rem, 5rem)`
- Root size stays 14px (this app's density is correct; do not change it)
- Headline size-by-length: 21–50 chars → `--text-display`; 51–90 chars cap
  at `--text-display-s`; >90 chars rewrite shorter or cap at `--text-4xl`.

**Instrument Serif ships one weight.** Every display element resets to
`font-weight: 400` and sets `font-synthesis-weight: none` — hierarchy comes
from size, measure and colour. Asking the browser to fake 700 smears a
high-contrast serif, which is exactly what the face is here to avoid. The
shared rule lives at the top of `globals.css` (`.brand, .hero h1, .mtitle,
…`); add new display elements to that selector list rather than re-declaring
`font-family` locally.

**Loader variables are a separate namespace.** `next/font` writes
`--f-display` / `--f-sans` / `--f-mono` on `<html>`; `tokens.css` maps those
into `--font-display` / `--font-sans` / `--font-mono` with fallback stacks.
Never point a loader at the token name it feeds: `--font-sans:
var(--font-sans, …)` is a cyclic reference, resolves to
invalid-at-computed-value-time, and silently drops the entire app to the
browser's default serif. That bug shipped once already.

Bricolage Grotesque and Inter are dropped — Bricolage's weighty display
register fought the restraint the product's copy is making, and Inter is the
most on-distribution UI sans there is. Fraunces (two themes ago) stays
dropped.

## Spacing
4-point named scale (`--space-3xs` … `--space-3xl`), values in `tokens.css`.
Pages use named tokens, never raw px.

## Radius
Four tiers only: `--radius-pill: 999px` · `--radius-card: 14px` ·
`--radius-control: 10px` · `--radius-tag: 6px`.

## Motion
- Easings: `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`, plus `--ease-in-out`,
  `--ease-in`. Never the browser default `ease`.
- Durations: `--dur-fast: 120ms` · `--dur-short: 240ms`.
- **Three primitives, hard cap:**
  1. `fade-rise` — one orchestrated entrance, first paint only (hero + first
     section). Not scroll-triggered.
  2. `lift` — hover/focus: `translateY(-1px)` + surface steps
     `--paper-2` → `--paper-3` + border to `--line-2`. No glow shadow.
  3. `bar-fill` — width transition on funnel / tier / usage bars only.
- Reduced-motion fallback: all three primitives collapse to a ≤150ms
  opacity crossfade.
- Focus rings appear instantly — never in a transition list.

## Microinteractions stance
- Silent success; toasts only for failures/async effects not visible on screen.
- Hover tooltip delay 800ms · focus delay 0ms.
- Optimistic update + undo over confirm dialogs, where applicable.

## CTA voice
- Primary CTA: solid ink-on-paper pill/slab fill (`--ink`-equivalent →
  `--paper-3` + `--ink` text on dark), press = `translateY(1px)`.
- Secondary CTA: ghost/outline, border `--line-2`, hover border + text to
  `--accent`.
- Labels are short verbs. No CTA label ever wraps to two lines.

## Per-page allowances
- Marketing pages MAY use enrichment: grain (always-on, whole app) + one
  contained jade bloom, hero only, Tier-A pure CSS/SVG.
- App pages MUST NOT use additional enrichment beyond the whole-app grain —
  function carries the page.
- `/how-it-works` MAY use numbered stages (1.0 → 5.0) — the one legitimate
  ordinal exception.

## What pages MUST share
- The `का` wordmark/mark.
- The accent colour and its on-shift-only placement.
- Display + body + mono fonts.
- The CTA voice (shape, radius, padding rhythm, press behaviour).
- Grain overlay, mounted once at the root layout.
- Elevation-by-lightness as the only depth device.

## What pages MAY differ on
- Macrostructure within the page-type family.
- Nav archetype: N5 Floating pill (marketing) vs N3 Side rail (app shell) —
  these are deliberately different surfaces (logged-out vs logged-in).
- Footer archetype: Ft5 Statement (marketing) vs Ft2 Inline single line (app).

## Signature moves
1. **Grain** — one fixed `<feTurbulence>` SVG overlay, ~0.035 opacity,
   `pointer-events: none`, `position: fixed`, mounted once app-wide.
2. **Elevation by lightness** — see Theme above.
3. **One contained hero bloom** — soft jade radial, low chroma,
   fixed-attached, no animation, `/` only.
4. **Recessed kanban wells** — `/roles/[id]` stage columns sit at `--well`
   (below the page); cards float at `--paper-2`.
5. **The side rail** — the app shell nav is vertical (N3), not a horizontal
   bar; the marketing nav stays a floating pill (N5) — the two surfaces
   read as deliberately distinct registers (public vs signed-in).
6. **Alternating alignment on `/`** — the hero and the closing statement are
   centred (marquee register); every section between them is left-aligned
   off a full-width hairline (`.mhead`, editorial register). One section
   (the grounded-reply transcript) takes the `.aside` split — head in a
   20rem column, artifact beside it — so the stacked-head rhythm breaks
   once. Uniform centring is what made the previous pass read as a
   template; do not restore it.
7. **Hairline division over boxes** — the landing's pillars and steps are
   divided by 1px rules, not wrapped in cards. Cards are the app's
   vocabulary; the marketing page is typeset.

## Exports

Drop-in formats for re-using this design system in other projects.

### tokens.css
See `frontend/app/tokens.css` — the canonical, complete token file this
project imports. Mirrored below for portability.

```css
:root {
  --paper:      oklch(16% 0.02 275);
  --paper-2:    oklch(20% 0.021 275);
  --paper-3:    oklch(24% 0.022 275);
  --well:       oklch(13% 0.018 275);
  --ink:        oklch(95% 0.008 275);
  --ink-2:      oklch(78% 0.010 275);
  --muted:      oklch(62% 0.012 275);
  --faint:      oklch(48% 0.012 275);
  --line:       oklch(27% 0.016 275);
  --line-2:     oklch(34% 0.018 275);
  --accent:     oklch(78% 0.17 165);
  --accent-2:   oklch(68% 0.16 165);
  --accent-ink: oklch(18% 0.04 165);
  --accent-dim: oklch(30% 0.05 165);
  --focus:      oklch(84% 0.15 165);

  /* --f-* are written by the font loader; never alias a token to itself */
  --font-display: var(--f-display), "Instrument Serif", ui-serif, Georgia, serif;
  --font-sans:    var(--f-sans), "Instrument Sans", ui-sans-serif, system-ui, sans-serif;
  --font-mono:    var(--f-mono), "IBM Plex Mono", ui-monospace, monospace;

  --track-display: -0.022em;
  --track-label:    0.12em;

  --space-3xs: 0.25rem;  --space-2xs: 0.5rem;  --space-xs: 0.75rem;
  --space-sm:  1rem;     --space-md:  1.5rem;  --space-lg: 2rem;
  --space-xl:  3rem;     --space-2xl: 4.5rem;  --space-3xl: 7rem;

  --text-display:   clamp(2.6rem, 5.4vw + 0.9rem, 5rem);
  --text-display-s: clamp(1.9rem, 3.2vw + 0.9rem, 3rem);

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 120ms; --dur-short: 240ms;

  --radius-pill: 999px; --radius-card: 14px;
  --radius-control: 10px; --radius-tag: 6px;
}
```

### Tailwind v4 `@theme`
```css
@theme {
  --color-paper:   oklch(16% 0.02 275);
  --color-ink:     oklch(95% 0.008 275);
  --color-accent:  oklch(78% 0.17 165);
  --font-display:  "Instrument Serif", serif;
  --font-sans:     "Instrument Sans", sans-serif;
  --spacing-md:    1.5rem;
  --text-md:       1.125rem;
  --ease-out:      cubic-bezier(0.16, 1, 0.3, 1);
}
```

### DTCG `tokens.json`
```json
{
  "color": {
    "paper":  { "$value": "oklch(16% 0.02 275)", "$type": "color" },
    "ink":    { "$value": "oklch(95% 0.008 275)", "$type": "color" },
    "accent": { "$value": "oklch(78% 0.17 165)", "$type": "color" }
  },
  "font": {
    "display": { "$value": "Instrument Serif", "$type": "fontFamily" },
    "body":    { "$value": "Instrument Sans", "$type": "fontFamily" }
  },
  "space": {
    "md": { "$value": "1.5rem", "$type": "dimension" }
  }
}
```

### shadcn/ui CSS variables
```css
:root {
  --background:         16% 0.02 275;
  --foreground:         95% 0.008 275;
  --primary:            78% 0.17 165;
  --primary-foreground: 18% 0.04 165;
  --muted:              62% 0.012 275;
  --border:             27% 0.016 275;
  --input:               27% 0.016 275;
  --ring:               84% 0.15 165;
  --radius:             14px;
}
```

## Provenance

Written by a Hallmark multi-page redesign, 2026-08-10. Replaces "clean white
premium" (light, Fraunces + Inter, antique-gold accent), which replaced the
original "Noir & Gold luxury" theme. Both prior themes were find-and-replace
colour swaps on the same structure; this system exists so the next visual
change is a token edit here, not a third rewrite.

Amended 2026-08-11 by a Hallmark `redesign` of `/`. Colour, macrostructure
family, nav and footer archetypes are unchanged. What changed: the type
system (Bricolage Grotesque + Inter + JetBrains Mono → Instrument Serif +
Instrument Sans + IBM Plex Mono, moving the display axis from grotesk-sans
to classical-serif), the landing's section rhythm (signature moves 6 and 7),
and two mobile fixes — the marketing nav wraps into two rows inside the pill
below 46rem (its CTA previously overflowed the pill and was unreachable),
and the hero stat row collapses to labelled rows below 40rem. The cyclic
`--font-*` self-alias documented under Typography was the reason the whole
app had been rendering in the browser's default serif.
