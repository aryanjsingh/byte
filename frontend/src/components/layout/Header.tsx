"use client";

import React from 'react';
import { signOut } from 'next-auth/react';
import { motion } from 'framer-motion';

interface HeaderProps {
    title?: string;
}

export default function Header({ title }: HeaderProps) {
    const handleLogout = async () => {
        await signOut({ callbackUrl: '/login' });
    };

    return (
        <motion.header
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
            className="flex items-center justify-between px-4 sm:px-6 glass-subtle sticky top-0 z-20 min-h-[56px] pt-[env(safe-area-inset-top)]"
        >
            {/* Left Section */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 flex-1 max-w-[200px] sm:max-w-2xl">
                    <span className="material-symbols-outlined text-blue-400 text-[16px] sm:text-[18px] flex-shrink-0">auto_awesome</span>
                    <span className="text-xs sm:text-sm font-medium text-white/80 truncate">{title || "New"}</span>
                </div>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-1 sm:gap-2">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleLogout}
                    className="flex items-center justify-center size-9 sm:size-10 text-white/60 hover:text-white hover:bg-white/5 rounded-xl transition-all group"
                    title="Logout"
                >
                    <span className="material-symbols-outlined text-[20px] group-hover:text-red-400 transition-colors">logout</span>
                </motion.button>
            </div>
        </motion.header>
    );
}
