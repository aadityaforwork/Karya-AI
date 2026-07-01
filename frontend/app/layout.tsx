import "./globals.css";
import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import Chrome from "../components/Chrome";
import { AuthProvider } from "../lib/auth";

// Inter — a crisp, neutral sans for body; Fraunces — a premium high-contrast
// serif (with italics) for display headings. Clean, editorial, legible.
const sans = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const serif = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
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
