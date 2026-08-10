import "./tokens.css";
import "./globals.css";
import type { Metadata } from "next";
import { Instrument_Sans, Instrument_Serif, IBM_Plex_Mono } from "next/font/google";
import Chrome from "../components/Chrome";
import Grain from "../components/Grain";
import { AuthProvider } from "../lib/auth";

// Instrument Serif — display. One weight (400), roman only; a classical
// high-contrast face that reads as composed rather than shouted on a dark
// ground. Size and colour carry the hierarchy, never synthesised bold.
// Instrument Sans — body. Its sans companion: slightly narrow, real
// tabular figures, holds at this app's 14px density where a wider grotesk
// would not. IBM Plex Mono — the technical voice: every cost figure, run
// ID, tier count and L# citation. See design.md § Typography.
//
// These three loader variables are DELIBERATELY named --f-* rather than
// --font-*: tokens.css maps them into --font-display / --font-sans /
// --font-mono with a real fallback stack. Pointing the loader at the token
// name directly makes the token self-referential (`--font-sans:
// var(--font-sans, …)`), which is a cyclic reference — it resolves to
// invalid-at-computed-value-time and silently drops the whole page to the
// browser's default serif. Keep the two namespaces separate.
const sans = Instrument_Sans({ subsets: ["latin"], variable: "--f-sans", display: "swap" });
const display = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--f-display",
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--f-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Karya · an AI workforce",
  description: "Describe an outcome. A team of AI workers does the job, cheaply, with proof, in any language.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable} ${mono.variable}`}>
      <body>
        <Grain />
        <AuthProvider>
          <div className="shell">
            <Chrome>{children}</Chrome>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
