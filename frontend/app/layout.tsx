import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PathPilot AI - Your Career Path, Personalized by AI",
  description:
    "AI-powered career guidance platform that analyzes your skills, interests, and goals to recommend personalized career paths with actionable roadmaps.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
