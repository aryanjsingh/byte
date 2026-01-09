import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "next-auth/react";
import Sidebar from "@/components/layout/Sidebar";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter"
});

export const metadata: Metadata = {
  title: "Byte AI - Intelligent Assistant",
  description: "Next-generation AI assistant with advanced capabilities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="theme-color" content="#0a0a0f" />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        <link 
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" 
          rel="stylesheet" 
        />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        {/* Animated Background */}
        <div className="animated-bg" />
        
        <SessionProvider>
          <div className="flex h-screen overflow-hidden relative">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0 h-screen w-full relative">
              {children}
            </div>
          </div>
        </SessionProvider>
      </body>
    </html>
  );
}
