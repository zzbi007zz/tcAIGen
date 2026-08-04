import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BDD Test Case Generator",
  description: "Generate Gherkin test cases from BA documents with quality proof",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
