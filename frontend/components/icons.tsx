type P = { size?: number; className?: string };

const base = (size: number) => ({
  width: size, height: size, viewBox: "0 0 24 24", fill: "none",
  stroke: "currentColor", strokeWidth: 2.2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const,
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
