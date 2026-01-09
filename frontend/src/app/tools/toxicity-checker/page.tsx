"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface ToxicityResult {
    toxicity: number;
    severe_toxicity: number;
    obscene: number;
    threat: number;
    insult: number;
    identity_attack: number;
    risk_level: string;
    assessment: string;
    scan_id: number;
}

interface HistoryItem {
    id: number;
    input: string;
    extra_data: { risk_level: string; max_score: number };
    created_at: string;
}

export default function ToxicityCheckerPage() {
    const { data: session } = useSession();
    const [text, setText] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ToxicityResult | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [showHistory, setShowHistory] = useState(false);

    const token = (session as any)?.accessToken;

    useEffect(() => {
        if (token) fetchHistory();
    }, [token]);

    const fetchHistory = async () => {
        try {
            const res = await fetch("http://localhost:8000/tools/history/toxicity_checker?limit=10", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(data.items);
            }
        } catch (e) { console.error(e); }
    };

    const handleAnalyze = async () => {
        if (!text.trim() || !token) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("http://localhost:8000/tools/toxicity-check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ text }),
            });

            if (res.ok) {
                const data = await res.json();
                setResult(data);
                fetchHistory();
            } else {
                const err = await res.json();
                alert(err.detail || "Analysis failed");
            }
        } catch (e) {
            console.error(e);
            alert("Network error");
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case "safe": return "text-green-400 bg-green-500/20 border-green-500/30";
            case "low": return "text-yellow-400 bg-yellow-500/20 border-yellow-500/30";
            case "moderate": return "text-orange-400 bg-orange-500/20 border-orange-500/30";
            case "high": return "text-red-400 bg-red-500/20 border-red-500/30";
            default: return "text-gray-400 bg-gray-500/20 border-gray-500/30";
        }
    };

    const getCategoryIcon = (category: string) => {
        const icons: Record<string, string> = {
            toxicity: "warning",
            severe_toxicity: "dangerous",
            obscene: "block",
            threat: "gpp_bad",
            insult: "sentiment_very_dissatisfied",
            identity_attack: "report",
        };
        return icons[category] || "info";
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
                        <div className="size-12 rounded-xl bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-2xl">shield</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Toxicity Checker</h1>
                            <p className="text-sm text-white/50">Detect toxic, offensive, and harmful content</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Input Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <label className="block text-sm font-medium text-white/70 mb-3">
                            Enter text to analyze for toxicity
                        </label>
                        <textarea
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Type or paste text here to check for toxic content, hate speech, threats, insults, etc..."
                            className="w-full h-40 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-red-500/50 focus:outline-none transition-all resize-none"
                        />
                        <div className="flex justify-between items-center mt-4">
                            <span className="text-xs text-white/40">{text.length} characters</span>
                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !text.trim()}
                                className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-pink-600 text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
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
                                className="space-y-4"
                            >
                                {/* Summary Card */}
                                <div className="glass-card rounded-2xl p-6">
                                    <div className="flex items-center justify-between mb-6">
                                        <h3 className="text-lg font-semibold text-white">Analysis Result</h3>
                                        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(result.risk_level)}`}>
                                            {result.risk_level.toUpperCase()}
                                        </span>
                                    </div>

                                    <div className="p-4 rounded-xl bg-white/5 mb-4">
                                        <p className="text-white/80">{result.assessment}</p>
                                    </div>
                                </div>

                                {/* Detailed Scores */}
                                <div className="glass-card rounded-2xl p-6">
                                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-red-400">analytics</span>
                                        Toxicity Breakdown
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { key: 'toxicity', label: 'Toxicity', value: result.toxicity },
                                            { key: 'severe_toxicity', label: 'Severe Toxicity', value: result.severe_toxicity },
                                            { key: 'obscene', label: 'Obscene', value: result.obscene },
                                            { key: 'threat', label: 'Threat', value: result.threat },
                                            { key: 'insult', label: 'Insult', value: result.insult },
                                            { key: 'identity_attack', label: 'Identity Attack', value: result.identity_attack },
                                        ].map((item) => (
                                            <div key={item.key} className="p-4 rounded-xl bg-white/5">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="material-symbols-outlined text-red-400 text-sm">
                                                        {getCategoryIcon(item.key)}
                                                    </span>
                                                    <span className="text-sm font-medium text-white/70">{item.label}</span>
                                                </div>
                                                <div className="flex items-end gap-2">
                                                    <span className={`text-2xl font-bold ${
                                                        item.value > 0.7 ? 'text-red-400' :
                                                        item.value > 0.5 ? 'text-orange-400' :
                                                        item.value > 0.3 ? 'text-yellow-400' :
                                                        'text-green-400'
                                                    }`}>
                                                        {Math.round(item.value * 100)}%
                                                    </span>
                                                </div>
                                                {/* Progress bar */}
                                                <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all duration-500 ${
                                                            item.value > 0.7 ? 'bg-red-500' :
                                                            item.value > 0.5 ? 'bg-orange-500' :
                                                            item.value > 0.3 ? 'bg-yellow-500' :
                                                            'bg-green-500'
                                                        }`}
                                                        style={{ width: `${item.value * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
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
                                                const extraData = item.extra_data || {};
                                                const riskLevel = extraData.risk_level || "unknown";
                                                const maxScore = extraData.max_score || 0;
                                                
                                                return (
                                                    <div
                                                        key={item.id}
                                                        className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer"
                                                        onClick={() => setText(item.input)}
                                                    >
                                                        <div className="flex items-center justify-between mb-1">
                                                            <span className={`text-xs px-2 py-1 rounded ${getRiskColor(riskLevel)}`}>
                                                                {riskLevel}
                                                            </span>
                                                            <span className="text-xs text-white/30">
                                                                {new Date(item.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        <p className="text-sm text-white/50 truncate mt-1">{item.input}</p>
                                                        <span className="text-xs text-white/40">Max score: {Math.round(maxScore * 100)}%</span>
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
