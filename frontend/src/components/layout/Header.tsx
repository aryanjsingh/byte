"use client";

import React from 'react';
import { signOut } from 'next-auth/react';

export default function Header() {
    const handleLogout = async () => {
        await signOut({ callbackUrl: '/login' });
    };

    return (
        <header className="h-14 flex items-center justify-between px-4 sm:px-6 border-b border-pl-border-light dark:border-pl-border bg-white/90 dark:bg-pl-bg/90 backdrop-blur-md sticky top-0 z-20">
            <div className="flex items-center gap-3">
                <button className="md:hidden p-2 -ml-2 text-pl-text-med dark:text-pl-text-secondary hover:bg-slate-100 dark:hover:bg-white/5 rounded">
                    <span className="material-symbols-outlined">menu</span>
                </button>
                <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-pl-brand dark:text-pl-brand text-[20px]">hub</span>
                    <h2 className="text-pl-text-dark dark:text-pl-text-primary text-sm font-bold tracking-tight">Quantum Computing / Session 4</h2>
                    <span className="hidden sm:inline-flex px-1.5 py-0.5 rounded-sm bg-blue-50 dark:bg-pl-brand/10 text-[9px] font-bold text-pl-brand border border-blue-100 dark:border-pl-brand/20 uppercase tracking-wide">
                        Model v4
                    </span>
                </div>
            </div>
            <div className="flex items-center gap-1">
                <button className="flex items-center gap-1.5 px-2 py-1.5 text-pl-text-med dark:text-pl-text-secondary hover:text-pl-text-dark dark:hover:text-pl-text-primary hover:bg-slate-100 dark:hover:bg-white/5 rounded transition-all" title="Export">
                    <span className="material-symbols-outlined text-[18px]">download</span>
                </button>
                <div className="w-px h-4 bg-slate-200 dark:bg-pl-border mx-1"></div>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 px-2 py-1.5 text-pl-text-med dark:text-pl-text-secondary hover:text-pl-text-dark dark:hover:text-pl-text-primary hover:bg-slate-100 dark:hover:bg-white/5 rounded transition-all"
                    title="More / Logout"
                >
                    <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                </button>
            </div>
        </header>
    );
}
