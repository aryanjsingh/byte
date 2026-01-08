"use client";

import ChatInterface from '@/components/chat/ChatInterface';
import { useEffect } from 'react';

export default function Home() {
  // Simple Dark Mode Toggle Script Injection or Logic
  // The provided code added a manual button via script. I will recreate that button properly in React here.

  useEffect(() => {
    // Check local storage or system preference in a real app
    // For now, default to dark is handled in layout.
  }, []);

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark');
  };

  return (
    <>
      <ChatInterface />

      {/* Floating Dark Mode Toggle */}
      <button
        onClick={toggleDarkMode}
        className="fixed top-4 right-4 z-50 p-3 rounded-full bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark shadow-xl text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-all md:hidden"
        title="Toggle Light Mode"
      >
        <span className="material-symbols-outlined">contrast</span>
      </button>

      {/* Desktop Toggle */}
      <button
        onClick={toggleDarkMode}
        className="fixed bottom-4 right-4 z-50 p-3 rounded-full bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark shadow-xl text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-all hidden md:flex"
        title="Toggle Light Mode"
      >
        <span className="material-symbols-outlined">contrast</span>
      </button>
    </>
  );
}
