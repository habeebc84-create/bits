import type { Metadata } from "next";
import Nav from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIGNAL HUNTER X — Autonomous Financial Intelligence",
  description: "Don't summarize the market. Discover what it's missing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
