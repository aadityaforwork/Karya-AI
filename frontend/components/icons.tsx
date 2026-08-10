// One hand-rolled SVG icon set, one stroke voice throughout — no icon
// library. Mixing stroke voices (a library icon beside a hand-built one)
// is the icon-set tell; see design.md.
type P = { size?: number; className?: string };

const base = (size: number) => ({
  width: size, height: size, viewBox: "0 0 24 24", fill: "none",
  stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const,
});

export function Check({ size = 14, className }: P) {
  return <svg {...base(size)} className={className}><path d="M20 6 9 17l-5-5" /></svg>;
}
export function Cross({ size = 14, className }: P) {
  return <svg {...base(size)} className={className}><path d="M18 6 6 18M6 6l12 12" /></svg>;
}
export function ArrowRight({ size = 15, className }: P) {
  return <svg {...base(size)} className={className}><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
}
export function Plus({ size = 15, className }: P) {
  return <svg {...base(size)} className={className}><path d="M12 5v14M5 12h14" /></svg>;
}
export function Shield({ size = 14, className }: P) {
  return <svg {...base(size)} className={className}><path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z" /><path d="M9.5 12l1.8 1.8 3.2-3.6" /></svg>;
}
export function Send({ size = 14, className }: P) {
  return <svg {...base(size)} className={className}><path d="M22 2 11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" /></svg>;
}

/* ---- side-rail set ---- */
export function Home({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><path d="M3 11.5 12 4l9 7.5" /><path d="M5.5 10v9a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1v-4h4v4a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1v-9" /></svg>;
}
export function Grid({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><rect x="3.5" y="3.5" width="7" height="7" rx="1.2" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.2" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.2" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.2" /></svg>;
}
export function Users({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><circle cx="9" cy="8" r="3.3" /><path d="M2.7 20c.7-3.4 3.2-5.4 6.3-5.4s5.6 2 6.3 5.4" /><path d="M15.5 5c1.6.3 2.8 1.7 2.8 3.4 0 1.7-1.2 3.1-2.8 3.4" /><path d="M17.3 14.8c2.4.5 4.2 2.3 4.7 5.2" /></svg>;
}
export function Inbox({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><path d="M3.5 12.5h5l1.3 2.4h4.4l1.3-2.4h5" /><path d="M5.2 5.5h13.6l2.2 7v6a1.3 1.3 0 0 1-1.3 1.3H4.3A1.3 1.3 0 0 1 3 18.5v-6l2.2-7z" /></svg>;
}
export function Play({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><path d="M6 4.5v15l13-7.5-13-7.5z" /></svg>;
}
export function Book({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><path d="M4 5.2C4 4.3 4.7 3.7 5.6 3.8c2 .2 4.6 1 6.4 2.4 1.8-1.4 4.4-2.2 6.4-2.4.9-.1 1.6.5 1.6 1.4v13c0 .8-.6 1.4-1.4 1.5-2.1.2-4.7 1-6.6 2.4-1.9-1.4-4.5-2.2-6.6-2.4-.8-.1-1.4-.7-1.4-1.5v-13z" /><path d="M12 6.2v14" /></svg>;
}
export function Cog({ size = 16, className }: P) {
  return <svg {...base(size)} className={className}><circle cx="12" cy="12" r="3.2" /><path d="M12 3.5v2.2M12 18.3v2.2M20.5 12h-2.2M5.7 12H3.5M17.8 6.2l-1.6 1.6M7.8 16.2l-1.6 1.6M17.8 17.8l-1.6-1.6M7.8 7.8 6.2 6.2" /></svg>;
}
export function Menu({ size = 18, className }: P) {
  return <svg {...base(size)} className={className}><path d="M4 6.5h16M4 12h16M4 17.5h16" /></svg>;
}
