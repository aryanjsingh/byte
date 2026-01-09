"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface ScanResult {
    target: string;
    target_type: string;
    is_safe: boolean;
    risk_level: string;
    details: {
        summary?: string;
        raw_result?: string;
        malicious_count?: number;
        suspicious_count?: number;
        virustotal_report?: string;
    };
    scan_id: number;
}

interface HistoryItem {
    id: number;
    input: string;
    output: string;
    extra_data: { risk_level: string; is_safe: boolean };
    created_at: string;
}

export default function URLCheckerPage() {
    const { data: session } = useSession();
    const [target, setTarget] = useState("");
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
            const res = await fetch("http://localhost:8000/tools/history/url_checker?limit=10", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(data.items);
            }
        } catch (e) { console.error(e); }
    };

    const handleScan = async () => {
        if (!target.trim() || !token) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("http://localhost:8000/tools/url-check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ target: target.trim() }),
            });

            if (res.ok) {
                const data = await res.json();
                setResult(data);
                fetchHistory();
            } else {
                const err = await res.json();
                alert(err.detail || "Scan failed");
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
            case "medium": return "text-orange-400 bg-orange-500/20 border-orange-500/30";
            case "high": return "text-red-400 bg-red-500/20 border-red-500/30";
            case "critical": return "text-red-500 bg-red-600/20 border-red-600/30";
            default: return "text-gray-400 bg-gray-500/20 border-gray-500/30";
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
                        <div className="size-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-2xl">link</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">URL / IP Checker</h1>
                            <p className="text-sm text-white/50">Scan URLs and IP addresses for security threats</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-3xl mx-auto space-y-6">
                    {/* Input Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <label className="block text-sm font-medium text-white/70 mb-3">Enter URL or IP Address</label>
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={target}
                                onChange={(e) => setTarget(e.target.value)}
                                placeholder="https://example.com or 192.168.1.1"
                                className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-blue-500/50 focus:outline-none transition-all"
                                onKeyDown={(e) => e.key === "Enter" && handleScan()}
                            />
                            <button
                                onClick={handleScan}
                                disabled={loading || !target.trim()}
                                className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
                            >
                                {loading ? (
                                    <span className="material-symbols-outlined animate-spin">progress_activity</span>
                                ) : (
                                    <span className="material-symbols-outlined">search</span>
                                )}
                                Scan
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
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">Scan Result</h3>
                                        <p className="text-sm text-white/50">{result.target}</p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(result.risk_level)}`}>
                                        {result.risk_level.toUpperCase()}
                                    </span>
                                </div>

                                <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 mb-4">
                                    <div className={`size-16 rounded-full flex items-center justify-center ${result.is_safe ? "bg-green-500/20" : "bg-red-500/20"}`}>
                                        <span className={`material-symbols-outlined text-3xl ${result.is_safe ? "text-green-400" : "text-red-400"}`}>
                                            {result.is_safe ? "verified_user" : "gpp_bad"}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <p className={`text-xl font-bold ${result.is_safe ? "text-green-400" : "text-red-400"}`}>
                                            {result.is_safe ? "Safe" : "Potentially Dangerous"}
                                        </p>
                                        <p className="text-sm text-white/50">Type: {result.target_type.toUpperCase()}</p>
                                        {(result.details.malicious_count !== undefined || result.details.suspicious_count !== undefined) && (
                                            <div className="flex gap-3 mt-2">
                                                {result.details.malicious_count !== undefined && (
                                                    <span className="text-xs text-red-400">
                                                        🚨 {result.details.malicious_count} malicious
                                                    </span>
                                                )}
                                                {result.details.suspicious_count !== undefined && (
                                                    <span className="text-xs text-yellow-400">
                                                        ⚠️ {result.details.suspicious_count} suspicious
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {result.details.summary && (
                                    <div className="p-4 rounded-xl bg-white/5 mb-4">
                                        <p className="text-sm text-white/70 whitespace-pre-wrap">{result.details.summary}</p>
                                    </div>
                                )}

                                {result.details.virustotal_report && (
                                    <details className="p-4 rounded-xl bg-white/5 cursor-pointer">
                                        <summary className="text-sm font-medium text-white/70 cursor-pointer">
                                            View Full VirusTotal Report
                                        </summary>
                                        <pre className="text-xs text-white/50 mt-3 whitespace-pre-wrap font-mono">
                                            {result.details.virustotal_report}
                                        </pre>
                                    </details>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* History Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <button
                            onClick={() => setShowHistory(!showHistory)}
                            className="flex items-center justify-between w-full"
                        >
                            <div className="flex items-center gap-2">
                                <span className="material-symbols-outlined text-white/50">history</span>
                                <span className="font-medium text-white">Scan History</span>
                                <span className="text-sm text-white/40">({history.length})</span>
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
                                            <p className="text-center text-white/40 py-4">No scan history yet</p>
                                        ) : (
                                            history.map((item) => (
                                                <div
                                                    key={item.id}
                                                    className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer"
                                                    onClick={() => setTarget(item.input)}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <span className={`material-symbols-outlined ${item.extra_data.is_safe ? "text-green-400" : "text-red-400"}`}>
                                                            {item.extra_data.is_safe ? "check_circle" : "warning"}
                                                        </span>
                                                        <span className="text-sm text-white/80 truncate max-w-[300px]">{item.input}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className={`text-xs px-2 py-1 rounded ${getRiskColor(item.extra_data.risk_level)}`}>
                                                            {item.extra_data.risk_level}
                                                        </span>
                                                        <span className="text-xs text-white/30">
                                                            {new Date(item.created_at).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))
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
