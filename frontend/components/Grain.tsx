// The one texture move that separates a dark theme from a dark canvas.
// Pure SVG feTurbulence, fixed over the whole app, paints once. No asset,
// no library, no per-page mounting — see design.md § Signature moves.
export default function Grain() {
  return (
    <svg className="grain" aria-hidden="true" focusable="false">
      <filter id="karya-grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#karya-grain)" />
    </svg>
  );
}
