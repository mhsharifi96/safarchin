import type { Metadata } from "next";
import { Vazirmatn, Bricolage_Grotesque } from "next/font/google";
import "leaflet/dist/leaflet.css";
import "@neshan-maps-platform/leaflet/dist/leaflet.css";
import "./globals.css";

import { AuthProvider } from "@/context/AuthContext";
import Header from "@/components/layout/Header";

const vazirmatn = Vazirmatn({
  variable: "--font-vazirmatn",
  subsets: ["arabic", "latin"],
});

const bricolageGrotesque = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

export const metadata: Metadata = {
  title: "سفرچین | برنامه‌ریز هوشمند سفر",
  description: "سفرچین به شما کمک می‌کند سفر ایده‌آل خود را با کمک هوش مصنوعی برنامه‌ریزی کنید.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="fa"
      dir="rtl"
      className={`${vazirmatn.variable} ${bricolageGrotesque.variable} h-full antialiased`}
    >
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-surface text-on-surface font-sans">
        <AuthProvider>
          <Header />
          <main className="flex-1">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
