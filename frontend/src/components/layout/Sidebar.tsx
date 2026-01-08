"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';

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
        <aside className="hidden md:flex w-[260px] flex-col justify-between bg-pl-sidebar-light dark:bg-pl-sidebar border-r border-pl-border-light dark:border-pl-border flex-shrink-0 transition-colors duration-200 z-20">
            <div className="flex flex-col h-full">
                <div className="p-4">
                    <div className="flex items-center gap-3 mb-6 px-1">
                        <div className="size-7 rounded bg-pl-brand flex items-center justify-center text-white shadow-sm ring-1 ring-inset ring-black/5 dark:ring-white/10">
                            <span className="material-symbols-outlined text-[18px]">bubble_chart</span>
                        </div>
                        <div>
                            <h1 className="text-pl-text-dark dark:text-white text-xs font-bold leading-none tracking-wide uppercase">Foundry AI</h1>
                            <p className="text-pl-text-med dark:text-pl-brand text-[9px] font-semibold mt-0.5 uppercase tracking-wider">Enterprise v4.2</p>
                        </div>
                    </div>
                    <Link href="/" className="flex items-center gap-3 w-full px-3 py-2.5 rounded bg-pl-brand hover:bg-pl-brand-hover dark:bg-pl-brand dark:hover:bg-blue-600 text-white transition-all shadow-sm hover:shadow-md border border-transparent dark:border-white/10 group">
                        <span className="material-symbols-outlined text-[18px]">add</span>
                        <span className="text-xs font-semibold tracking-wide uppercase">New Analysis</span>
                    </Link>
                </div>

                <nav className="flex-1 px-2 overflow-y-auto space-y-0.5 custom-scrollbar">
                    <div className="text-[9px] font-bold text-pl-text-sub dark:text-zinc-500 uppercase tracking-widest mb-2 px-3 mt-1">Workspaces</div>

                    {threads.map((thread) => (
                        <div key={thread.id} className="relative group/item">
                            <Link
                                href={`/c/${thread.id}`}
                                className={`flex items-center gap-3 w-full px-3 py-2 rounded transition-all group ${pathname === `/c/${thread.id}`
                                    ? 'bg-blue-50 dark:bg-white/5 text-pl-brand dark:text-pl-text-primary border-l-2 border-pl-brand'
                                    : 'hover:bg-slate-50 dark:hover:bg-white/5 text-pl-text-med dark:text-pl-text-secondary border-l-2 border-transparent hover:border-slate-300 dark:hover:border-white/10'
                                    }`}
                            >
                                <span className={`material-symbols-outlined text-[16px] transition-colors ${pathname === `/c/${thread.id}`
                                    ? 'text-pl-brand dark:text-pl-text-primary'
                                    : 'group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary'
                                    }`}>chat</span>
                                <span className={`text-xs font-semibold truncate flex-1 transition-colors ${pathname === `/c/${thread.id}`
                                    ? 'text-pl-brand dark:text-pl-text-primary'
                                    : 'group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary'
                                    }`}>
                                    {thread.title || "New Thread"}
                                </span>
                            </Link>

                            {/* Menu Button */}
                            <button
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setActiveMenuId(activeMenuId === thread.id ? null : thread.id);
                                }}
                                className={`absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-slate-200 dark:hover:bg-white/10 text-pl-text-sub hover:text-pl-text-dark dark:hover:text-white transition-colors ${activeMenuId === thread.id ? 'opacity-100' : 'opacity-0 group-hover/item:opacity-100'}`}
                            >
                                <span className="material-symbols-outlined text-[16px]">more_vert</span>
                            </button>

                            {/* Dropdown Menu */}
                            {activeMenuId === thread.id && (
                                <>
                                    <div
                                        className="fixed inset-0 z-40"
                                        onClick={() => setActiveMenuId(null)}
                                    />
                                    <div className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-pl-panel border border-slate-200 dark:border-pl-border rounded shadow-lg z-50 py-1">
                                        <button
                                            onClick={async (e) => {
                                                e.stopPropagation();
                                                const token = (session as any)?.accessToken;
                                                try {
                                                    const res = await fetch(`http://localhost:8000/chat/threads/${thread.id}`, {
                                                        method: 'DELETE',
                                                        headers: { Authorization: `Bearer ${token}` }
                                                    });
                                                    if (res.ok) {
                                                        setThreads(prev => prev.filter(t => t.id !== thread.id));
                                                        if (pathname === `/c/${thread.id}`) {
                                                            // Redirect if current thread deleted (optional, handled by nextjs link mostly but better explicit)
                                                            // For now just letting user navigate manually or state update
                                                        }
                                                    }
                                                } catch (err) {
                                                    console.error("Failed to delete thread", err);
                                                }
                                                setActiveMenuId(null);
                                            }}
                                            className="w-full text-left px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                                        >
                                            <span className="material-symbols-outlined text-[14px]">delete</span>
                                            Delete
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}

                    <div className="text-[9px] font-bold text-pl-text-sub dark:text-zinc-500 uppercase tracking-widest mb-2 px-3 mt-6">System</div>

                    <button className="flex items-center gap-3 w-full px-3 py-2 rounded hover:bg-slate-50 dark:hover:bg-white/5 text-pl-text-med dark:text-pl-text-secondary transition-all group">
                        <span className="material-symbols-outlined text-[16px] group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary transition-colors">history</span>
                        <span className="text-xs font-medium group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary transition-colors">Logs</span>
                    </button>

                    <button className="flex items-center gap-3 w-full px-3 py-2 rounded hover:bg-slate-50 dark:hover:bg-white/5 text-pl-text-med dark:text-pl-text-secondary transition-all group">
                        <span className="material-symbols-outlined text-[16px] group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary transition-colors">settings</span>
                        <span className="text-xs font-medium group-hover:text-pl-text-dark dark:group-hover:text-pl-text-primary transition-colors">Configuration</span>
                    </button>
                </nav>

                <div className="p-3 border-t border-pl-border-light dark:border-pl-border bg-pl-sidebar-light dark:bg-pl-sidebar">
                    <button className="flex w-full items-center justify-center gap-2 rounded h-8 px-4 bg-slate-50 dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 text-pl-text-dark dark:text-pl-text-primary text-xs font-bold transition-all border border-slate-200 dark:border-white/5 group mb-3">
                        <span className="material-symbols-outlined text-[16px] text-pl-text-sub dark:text-amber-500 group-hover:dark:text-amber-400 transition-colors">verified_user</span>
                        PRO LICENSE
                    </button>
                    {session?.user && (
                        <div className="flex items-center gap-3 px-1">
                            <div className="relative">
                                <div
                                    className="size-8 rounded bg-cover bg-center ring-1 ring-slate-200 dark:ring-white/10"
                                    style={{ backgroundImage: `url("${session?.user?.image || 'https://lh3.googleusercontent.com/aida-public/AB6AXuCnFv1hUmYikd9v3Vft-6ANUDVN14pzvc6PGW67q2ozvhAuPmX0fIyG4-Vi-tWbdNBayHUbFMR3ERVJtRLnyVBuswUx4xUNE2GOzUKmEUQD1MU-tJwksL0L4iq86qPKiYjPt3B5wknX1qF2o9V5mw6etO8NONHG__XL3RMVndMMSSezSZBL5kJDezyhpheLqfnPJhTxeEwrdWRBqiiGwF3ppy5Yx4TXqZCN52wOPLD1vowW_y4oBJYihhWMblzhCStzuGKgRLe2Wag'}")` }}
                                ></div>
                                <div className="absolute -bottom-0.5 -right-0.5 size-2.5 bg-green-500 rounded-sm border border-white dark:border-pl-sidebar"></div>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold text-pl-text-dark dark:text-pl-text-primary truncate">{session?.user?.name || 'Jane Doe'}</p>
                                <p className="text-[10px] text-pl-text-med dark:text-pl-text-secondary truncate">{session?.user?.email || 'jane@foundry.ai'}</p>
                            </div>
                            <button className="text-pl-text-sub hover:text-pl-text-med dark:hover:text-white p-1 rounded hover:bg-slate-100 dark:hover:bg-white/5 transition-colors">
                                <span className="material-symbols-outlined text-[18px]">more_vert</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}
