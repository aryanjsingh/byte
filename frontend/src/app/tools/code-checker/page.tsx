"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface Vulnerability {
    name: string;
    severity: string;
    description: string;
    fix: string;
    line: number;
    code_snippet: string;
}

interface ScanResult {
    vulnerabilities: Vulnerability[];
    risk_level: string;
    total_issues: number;
    suggestions: string[];
    scan_id: number;
}

interface HistoryItem {
    id: number;
    input: string;
    extra_data: { language: string; vulnerabilities: Vulnerability[] };
    created_at: string;
}

const LANGUAGES = [
    { id: "python", name: "Python", icon: "🐍" },
    { id: "javascript", name: "JavaScript", icon: "📜" },
];

export default function CodeCheckerPage() {
    const { data: session } = useSession();
    const [code, setCode] = useState("");
    const [language, setLanguage] = useState("python");
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
            const res = await fetch("http://localhost:8000/tools/history/code_checker?limit=10", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                console.log("Code checker history:", data);
                setHistory(data.items);
            } else {
                console.error("Failed to fetch history:", res.status);
            }
        } catch (e) { 
            console.error("History fetch error:", e); 
        }
    };

    const handleScan = async () => {
        if (!code.trim() || !token) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("http://localhost:8000/tools/code-check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ code, language }),
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

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case "critical": return "text-red-500 bg-red-500/20 border-red-500/30";
            case "high": return "text-orange-400 bg-orange-500/20 border-orange-500/30";
            case "medium": return "text-yellow-400 bg-yellow-500/20 border-yellow-500/30";
            case "low": return "text-blue-400 bg-blue-500/20 border-blue-500/30";
            default: return "text-gray-400 bg-gray-500/20 border-gray-500/30";
        }
    };

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case "critical": return "error";
            case "high": return "warning";
            case "medium": return "info";
            case "low": return "help";
            default: return "help";
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
                        <div className="size-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-2xl">code_blocks</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Code Snippet Checker</h1>
                            <p className="text-sm text-white/50">Analyze code for security vulnerabilities</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Input Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <label className="text-sm font-medium text-white/70">Paste your code</label>
                            <div className="flex gap-2">
                                {LANGUAGES.map((lang) => (
                                    <button
                                        key={lang.id}
                                        onClick={() => setLanguage(lang.id)}
                                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                            language === lang.id
                                                ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                                                : "bg-white/5 text-white/50 hover:text-white/80"
                                        }`}
                                    >
                                        {lang.icon} {lang.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <textarea
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                            placeholder={`# Paste your ${language} code here...\npassword = "admin123"\neval(user_input)`}
                            className="w-full h-64 px-4 py-3 rounded-xl bg-[#1e1e2e] border border-white/10 text-white font-mono text-sm placeholder-white/30 focus:border-purple-500/50 focus:outline-none transition-all resize-none"
                        />
                        <div className="flex justify-end mt-4">
                            <button
                                onClick={handleScan}
                                disabled={loading || !code.trim()}
                                className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-600 text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
                            >
                                {loading ? (
                                    <span className="material-symbols-outlined animate-spin">progress_activity</span>
                                ) : (
                                    <span className="material-symbols-outlined">security</span>
                                )}
                                Analyze Code
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
                                {/* Summary */}
                                <div className="glass-card rounded-2xl p-6">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`size-16 rounded-full flex items-center justify-center ${
                                                result.total_issues === 0 ? "bg-green-500/20" : "bg-red-500/20"
                                            }`}>
                                                <span className={`material-symbols-outlined text-3xl ${
                                                    result.total_issues === 0 ? "text-green-400" : "text-red-400"
                                                }`}>
                                                    {result.total_issues === 0 ? "verified_user" : "gpp_bad"}
                                                </span>
                                            </div>
                                            <div>
                                                <p className="text-2xl font-bold text-white">{result.total_issues} Issues Found</p>
                                                <p className="text-sm text-white/50">
                                                    Risk Level: <span className={getSeverityColor(result.risk_level).split(" ")[0]}>{result.risk_level.toUpperCase()}</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Vulnerabilities */}
                                {result.vulnerabilities.length > 0 && (
                                    <div className="glass-card rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-red-400">bug_report</span>
                                            Vulnerabilities Detected
                                        </h3>
                                        <div className="space-y-3">
                                            {result.vulnerabilities.map((vuln, idx) => (
                                                <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/10">
                                                    <div className="flex items-start justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <span className={`material-symbols-outlined ${getSeverityColor(vuln.severity).split(" ")[0]}`}>
                                                                {getSeverityIcon(vuln.severity)}
                                                            </span>
                                                            <span className="font-medium text-white">{vuln.name}</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className={`text-xs px-2 py-1 rounded border ${getSeverityColor(vuln.severity)}`}>
                                                                {vuln.severity.toUpperCase()}
                                                            </span>
                                                            <span className="text-xs text-white/40">Line {vuln.line}</span>
                                                        </div>
                                                    </div>
                                                    <p className="text-sm text-white/60 mb-2">{vuln.description}</p>
                                                    <code className="block text-xs bg-red-500/10 text-red-300 px-3 py-2 rounded-lg mb-2 font-mono">
                                                        {vuln.code_snippet}
                                                    </code>
                                                    <div className="flex items-start gap-2 text-sm">
                                                        <span className="material-symbols-outlined text-green-400 text-base">lightbulb</span>
                                                        <span className="text-green-400">{vuln.fix}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* History Section */}
                    <div className="glass-card rounded-2xl p-6">
                        <button onClick={() => setShowHistory(!showHistory)} className="flex items-center justify-between w-full">
                            <div className="flex items-center gap-2">
                                <span className="material-symbols-outlined text-white/50">history</span>
                                <span className="font-medium text-white">Scan History</span>
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
                                            history.map((item) => {
                                                const extraData = item.extra_data || {};
                                                const language = extraData.language || "unknown";
                                                const vulnCount = extraData.vulnerabilities?.length || 0;
                                                
                                                return (
                                                    <div
                                                        key={item.id}
                                                        className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer"
                                                        onClick={() => setCode(item.input)}
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-sm text-white/60">{language}</span>
                                                                <span className="text-xs text-white/40">
                                                                    {vulnCount} issues
                                                                </span>
                                                            </div>
                                                            <span className="text-xs text-white/30">
                                                                {new Date(item.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        <code className="text-xs text-white/50 truncate block mt-1 font-mono">
                                                            {item.input.slice(0, 60)}...
                                                        </code>
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
