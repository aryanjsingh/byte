"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatThread {
    id: string;
    title: string;
    updated_at: string;
}

export default function Sidebar() {
    const { data: session } = useSession();
    const params = useParams();
    const pathname = usePathname();
    const [threads, setThreads] = useState<ChatThread[]>([]);
    const [mounted, setMounted] = useState(false);
    const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
    const [hoveredThread, setHoveredThread] = useState<string | null>(null);

    useEffect(() => setMounted(true), []);

    useEffect(() => {
        if (session?.user) {
            const fetchThreads = async () => {
                try {
                    const token = (session as any).accessToken;
                    const res = await fetch('http://localhost:8000/chat/threads', {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    if (res.ok) {
                        const data = await res.json();
                        setThreads(data);
                    }
                } catch (e) { console.error(e); }
            };

            fetchThreads();
            const interval = setInterval(fetchThreads, 5000);
            return () => clearInterval(interval);
        }
    }, [session]);

    if (!mounted) return null;
    if (pathname?.startsWith('/login') || pathname?.startsWith('/signup')) return null;

    return (
        <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
            className="hidden md:flex w-[280px] flex-col justify-between glass-strong flex-shrink-0 z-20 relative overflow-hidden"
        >
            {/* Gradient Accent Line */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />

            {/* Subtle Glow Effect */}
            <div className="absolute -top-20 -left-20 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col h-full relative z-10">
                {/* Logo Section */}
                <div className="p-5">
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="flex items-center gap-3 mb-6"
                    >
                        <div className="relative">
                            <div className="size-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg glow-blue">
                                <span className="material-symbols-outlined text-[22px]">auto_awesome</span>
                            </div>
                            <div className="absolute -bottom-1 -right-1 size-3 bg-green-500 rounded-full border-2 border-[#12121a]" />
                        </div>
                        <div>
                            <h1 className="text-white text-sm font-bold tracking-wide">BYTE AI</h1>
                        </div>
                    </motion.div>

                    {/* New Chat Button */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.3 }}
                    >
                        <Link
                            href="/"
                            className="group flex items-center gap-3 w-full px-4 py-3 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10"
                        >
                            <div className="size-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white group-hover:scale-110 transition-transform duration-300">
                                <span className="material-symbols-outlined text-[18px]">add</span>
                            </div>
                            <span className="text-sm font-semibold text-white/90 group-hover:text-white">New Chat</span>
                        </Link>
                    </motion.div>
                </div>

                {/* Threads List */}
                <nav className="flex-1 px-3 overflow-y-auto space-y-1 custom-scrollbar">
                    <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 px-2 flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">history</span>
                        Recent Chats
                    </div>

                    <AnimatePresence>
                        {threads.map((thread, index) => (
                            <motion.div
                                key={thread.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ delay: index * 0.05 }}
                                className="relative group/item"
                                onMouseEnter={() => setHoveredThread(thread.id)}
                                onMouseLeave={() => setHoveredThread(null)}
                            >
                                <Link
                                    href={`/c/${thread.id}`}
                                    className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl transition-all duration-300 ${pathname === `/c/${thread.id}`
                                        ? 'bg-white/10 text-white border border-white/10'
                                        : 'hover:bg-white/5 text-white/60 hover:text-white/90 border border-transparent'
                                        } ${hoveredThread === thread.id ? 'pr-10' : ''}`}
                                >
                                    <span className={`material-symbols-outlined text-[18px] transition-all duration-300 ${pathname === `/c/${thread.id}`
                                        ? 'text-blue-400'
                                        : 'text-white/40 group-hover/item:text-white/60'
                                        }`}>
                                        chat_bubble
                                    </span>
                                    <span className="text-sm font-medium truncate flex-1">
                                        {thread.title || "New Thread"}
                                    </span>

                                    {/* Active Indicator */}
                                    {pathname === `/c/${thread.id}` && (
                                        <motion.div
                                            layoutId="activeIndicator"
                                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-400 to-purple-500 rounded-r-full"
                                        />
                                    )}
                                </Link>

                                {/* Delete Button */}
                                <AnimatePresence>
                                    {hoveredThread === thread.id && (
                                        <motion.button
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.8 }}
                                            onClick={async (e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                const token = (session as any)?.accessToken;
                                                try {
                                                    const res = await fetch(`http://localhost:8000/chat/threads/${thread.id}`, {
                                                        method: 'DELETE',
                                                        headers: { Authorization: `Bearer ${token}` }
                                                    });
                                                    if (res.ok) {
                                                        setThreads(prev => prev.filter(t => t.id !== thread.id));
                                                    }
                                                } catch (err) {
                                                    console.error("Failed to delete thread", err);
                                                }
                                            }}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">delete</span>
                                        </motion.button>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {/* Tools Section */}
                    <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 px-2 mt-8 flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">extension</span>
                        Tools
                    </div>

                    {[
                        { icon: 'quiz', label: 'Quiz Mode', href: '/tools/quiz' },
                        { icon: 'code_blocks', label: 'Code Snippet Checker', href: '/tools/code-checker' },
                        { icon: 'fact_check', label: 'Fake News Detector', href: '/tools/fake-news' },
                        { icon: 'link', label: 'URL Checker/IP Checker', href: '/tools/url-checker' },
                        { icon: 'shield', label: 'Toxicity Checker', href: '/tools/toxicity-checker' },
                    ].map((item, index) => (
                        <motion.div
                            key={item.label}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 + index * 0.05 }}
                        >
                            <Link
                                href={item.href}
                                className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl hover:bg-white/5 text-white/50 hover:text-white/80 transition-all duration-300 group ${
                                    pathname === item.href ? 'bg-white/10 text-white' : ''
                                }`}
                            >
                                <span className={`material-symbols-outlined text-[18px] group-hover:text-blue-400 transition-colors ${
                                    pathname === item.href ? 'text-blue-400' : ''
                                }`}>{item.icon}</span>
                                <span className="text-sm font-medium">{item.label}</span>
                            </Link>
                        </motion.div>
                    ))}
                </nav>

                {/* User Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="p-4 border-t border-white/5"
                >
                    {session?.user && (
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div
                                    className="size-10 rounded-xl bg-cover bg-center ring-2 ring-white/10"
                                    style={{ backgroundImage: `url("${session?.user?.image || `https://api.dicebear.com/7.x/initials/svg?seed=${session?.user?.name || 'U'}&backgroundColor=6366f1`}")` }}
                                />
                                <div className="absolute -bottom-0.5 -right-0.5 size-3 bg-green-500 rounded-full border-2 border-[#12121a]" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-white truncate">{session?.user?.name || 'User'}</p>
                                <p className="text-xs text-white/40 truncate">{session?.user?.email}</p>
                            </div>
                            <button className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white/80 transition-all">
                                <span className="material-symbols-outlined text-[18px]">more_vert</span>
                            </button>
                        </div>
                    )}
                </motion.div>
            </div>
        </motion.aside>
    );
}
