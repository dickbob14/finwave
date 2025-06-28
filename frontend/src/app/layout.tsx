import type { Metadata } from "next";
import { Navigation } from "@/components/navigation";
import { ToastProvider } from "@/components/ui/use-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinWave - AI-Powered Financial Analytics",
  description: "Transform your financial reporting with real-time insights, board-ready reports, and intelligent forecasting",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-sans">
        <ToastProvider>
          <Navigation />
          <main className="min-h-screen bg-gray-50">
            {children}
          </main>
        </ToastProvider>
      </body>
    </html>
  );
}
