import "./globals.css";
import type { Metadata } from "next";
import { Jost, Cormorant_Garamond } from "next/font/google";
import Chrome from "../components/Chrome";
import { AuthProvider } from "../lib/auth";

// Jost — a refined geometric sans for body; Cormorant Garamond — a high-contrast
// couture serif for display. The "Noir & Gold" pairing.
const sans = Jost({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const serif = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Karya · an AI workforce",
  description: "Describe an outcome. A team of AI workers does the job, cheaply, with proof, in any language.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable}`}>
      <body>
        <AuthProvider>
          <div className="shell">
            <Chrome>{children}</Chrome>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
