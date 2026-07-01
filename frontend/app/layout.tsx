import "./globals.css";
import type { Metadata } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import Chrome from "../components/Chrome";
import { AuthProvider } from "../lib/auth";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const serif = Instrument_Serif({ subsets: ["latin"], weight: "400", variable: "--font-serif", display: "swap" });

export const metadata: Metadata = {
  title: "Karya · an AI workforce",
  description: "Describe an outcome. A team of AI workers does the job, cheaply, with proof, in any language.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${serif.variable}`}>
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
