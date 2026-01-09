"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface ScanResult {
    content: string;
    verdict: string;
    confidence: number;
    red_flags: string[];
    analysis: string;
    scan_id: number;
}

interface HistoryItem {
    id: number;
    input: string;
    output: string;
    extra_data: { red_flags: string[]; confidence: number };
    created_at: string;
}

export default function FakeNewsPage() {
    const { data: session } = useSession();
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ScanResult | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [showHistory, setShowHistory] = useState(false);

    const token = (session as any)?.accessToken;

    useEffect(() => {
        if (token) fetchHistory();
    }, [token]);

    const fetchHistory = async () => {
        try {
            const res = await fetch("http://localhost:8000/tools/history/fake_news?limit=10", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(data.items);
            }
        } catch (e) { console.error(e); }
    };

    const handleAnalyze = async () => {
        if (!content.trim() || !token) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("http://localhost:8000/tools/fake-news-check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ content }),
            });

            if (res.ok) {
                const data = await res.json();
                setResult(data);
                fetchHistory();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const getVerdictStyle = (verdict: string) => {
        switch (verdict) {
            case "likely_fake": return { color: "text-red-400", bg: "bg-red-500/20", icon: "dangerous", label: "Likely Fake" };
            case "likely_real": return { color: "text-green-400", bg: "bg-green-500/20", icon: "verified", label: "Likely Real" };
            default: return { color: "text-yellow-400", bg: "bg-yellow-500/20", icon: "help", label: "Uncertain" };
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-white/10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 rounded-lg hover:bg-white/5 text-white/60 hover:text-white transition-all">
                        <span className="material-symbols-outlined">arrow_back</span>
                    </Link>
                    <div className="flex items-center gap-3">
                        <div className="size-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-2xl">fact_check</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Fake News Detector</h1>
                            <p className="text-sm text-white/50">Analyze content for misinformation indicators</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-3xl mx-auto space-y-6">
                    {/* Input Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <label className="block text-sm font-medium text-white/70 mb-3">
                            Paste news headline or article text
                        </label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="BREAKING: You won't believe what happened! Share before it gets deleted..."
                            className="w-full h-40 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-orange-500/50 focus:outline-none transition-all resize-none"
                        />
                        <div className="flex justify-end mt-4">
                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !content.trim()}
                                className="px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-red-600 text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
                            >
                                {loading ? (
                                    <span className="material-symbols-outlined animate-spin">progress_activity</span>
                                ) : (
                                    <span className="material-symbols-outlined">search</span>
                                )}
                                Analyze
                            </button>
                        </div>
                    </div>

                    {/* Result Section */}
                    <AnimatePresence>
                        {result && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="glass-card rounded-2xl p-6"
                            >
                                {(() => {
                                    const style = getVerdictStyle(result.verdict);
                                    return (
                                        <>
                                            <div className="flex items-center gap-4 mb-6">
                                                <div className={`size-20 rounded-full flex items-center justify-center ${style.bg}`}>
                                                    <span className={`material-symbols-outlined text-4xl ${style.color}`}>
                                                        {style.icon}
                                                    </span>
                                                </div>
                                                <div className="flex-1">
                                                    <p className={`text-2xl font-bold ${style.color}`}>{style.label}</p>
                                                    <p className="text-sm text-white/50">
                                                        Confidence: {Math.round(result.confidence * 100)}%
                                                    </p>
                                                    <div className="flex items-center gap-1 mt-1">
                                                        <span className="material-symbols-outlined text-blue-400 text-xs">psychology</span>
                                                        <span className="text-xs text-blue-400">ML Model Analysis</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="p-4 rounded-xl bg-white/5 mb-4">
                                                <p className="text-white/80">{result.analysis}</p>
                                            </div>

                                            {result.red_flags.length > 0 && (
                                                <div>
                                                    <h4 className="text-sm font-medium text-white/70 mb-2 flex items-center gap-2">
                                                        <span className="material-symbols-outlined text-red-400 text-base">flag</span>
                                                        Red Flags Detected
                                                    </h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {result.red_flags.map((flag, idx) => (
                                                            <span key={idx} className="px-3 py-1 rounded-full text-sm bg-red-500/20 text-red-400 border border-red-500/30">
                                                                {flag}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </>
                                    );
                                })()}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* History Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <button onClick={() => setShowHistory(!showHistory)} className="flex items-center justify-between w-full">
                            <div className="flex items-center gap-2">
                                <span className="material-symbols-outlined text-white/50">history</span>
                                <span className="font-medium text-white">Analysis History</span>
                            </div>
                            <span className={`material-symbols-outlined text-white/50 transition-transform ${showHistory ? "rotate-180" : ""}`}>
                                expand_more
                            </span>
                        </button>

                        <AnimatePresence>
                            {showHistory && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="mt-4 space-y-2">
                                        {history.length === 0 ? (
                                            <p className="text-center text-white/40 py-4">No analysis history yet</p>
                                        ) : (
                                            history.map((item) => {
                                                const style = getVerdictStyle(item.output);
                                                return (
                                                    <div
                                                        key={item.id}
                                                        className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer"
                                                        onClick={() => setContent(item.input)}
                                                    >
                                                        <div className="flex items-center justify-between mb-1">
                                                            <span className={`text-sm font-medium ${style.color}`}>{style.label}</span>
                                                            <span className="text-xs text-white/30">
                                                                {new Date(item.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        <p className="text-sm text-white/50 truncate">{item.input}</p>
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );
}
