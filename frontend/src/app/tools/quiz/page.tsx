"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface Question {
    id: number;
    question: string;
    options: string[];
    category: string;
}

interface QuizResult {
    question_id: number;
    question: string;
    selected: number;
    correct: number;
    is_correct: boolean;
    explanation: string;
    correct_answer: string;
}

interface Category {
    id: string;
    name: string;
    description: string;
    icon: string;
}

interface HistoryItem {
    id: number;
    category: string;
    score: number;
    correct: number;
    total: number;
    created_at: string;
}

type QuizState = "select" | "playing" | "results";

export default function QuizPage() {
    const { data: session } = useSession();
    const [state, setState] = useState<QuizState>("select");
    const [categories, setCategories] = useState<Category[]>([]);
    const [selectedCategory, setSelectedCategory] = useState("mixed");
    const [questions, setQuestions] = useState<Question[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState<{ question_id: number; selected: number }[]>([]);
    const [results, setResults] = useState<QuizResult[]>([]);
    const [score, setScore] = useState({ correct: 0, total: 0, percentage: 0 });
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [startTime, setStartTime] = useState(0);
    const [quizId, setQuizId] = useState<string | null>(null);
    const [isAiGenerated, setIsAiGenerated] = useState(false);

    const token = (session as any)?.accessToken;

    useEffect(() => {
        if (token) {
            fetchCategories();
            fetchHistory();
        }
    }, [token]);

    const fetchCategories = async () => {
        try {
            const res = await fetch("http://localhost:8000/tools/quiz/categories", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setCategories(data.categories);
            }
        } catch (e) { console.error(e); }
    };

    const fetchHistory = async () => {
        try {
            const res = await fetch("http://localhost:8000/tools/quiz/history?limit=10", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(data.attempts);
            }
        } catch (e) { console.error(e); }
    };

    const startQuiz = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/tools/quiz/start", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ category: selectedCategory, num_questions: 5 }),
            });

            if (res.ok) {
                const data = await res.json();
                setQuestions(data.questions);
                setCurrentIndex(0);
                setAnswers([]);
                setStartTime(Date.now());
                setQuizId(data.quiz_id || null);
                setIsAiGenerated(data.ai_generated || false);
                setState("playing");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const selectAnswer = (optionIndex: number) => {
        const question = questions[currentIndex];
        setAnswers([...answers, { question_id: question.id, selected: optionIndex }]);

        if (currentIndex < questions.length - 1) {
            setTimeout(() => setCurrentIndex(currentIndex + 1), 300);
        } else {
            submitQuiz([...answers, { question_id: question.id, selected: optionIndex }]);
        }
    };

    const submitQuiz = async (finalAnswers: { question_id: number; selected: number }[]) => {
        setLoading(true);
        const timeTaken = Math.round((Date.now() - startTime) / 1000);

        try {
            const res = await fetch("http://localhost:8000/tools/quiz/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ 
                    answers: finalAnswers, 
                    time_taken_seconds: timeTaken,
                    quiz_id: quizId  // Pass quiz_id for AI-generated quizzes
                }),
            });

            if (res.ok) {
                const data = await res.json();
                setResults(data.results);
                setScore({
                    correct: data.correct_answers,
                    total: data.total_questions,
                    percentage: data.score_percentage,
                });
                setState("results");
                fetchHistory();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const resetQuiz = () => {
        setState("select");
        setQuestions([]);
        setAnswers([]);
        setResults([]);
        setCurrentIndex(0);
        setQuizId(null);
        setIsAiGenerated(false);
    };

    const getCategoryIcon = (icon: string) => {
        const icons: Record<string, string> = {
            shuffle: "shuffle",
            phishing: "phishing",
            bug_report: "bug_report",
            psychology: "psychology",
            currency_rupee: "currency_rupee",
            gavel: "gavel",
        };
        return icons[icon] || "quiz";
    };

    const getScoreColor = (pct: number) => {
        if (pct >= 80) return "text-green-400";
        if (pct >= 60) return "text-yellow-400";
        return "text-red-400";
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
                        <div className="size-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-2xl">quiz</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Cybersecurity Quiz</h1>
                            <p className="text-sm text-white/50">Test your security awareness</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-3xl mx-auto">
                    <AnimatePresence mode="wait">
                        {/* Category Selection */}
                        {state === "select" && (
                            <motion.div
                                key="select"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-6"
                            >
                                <div className="glass-card rounded-2xl p-6">
                                    <h2 className="text-lg font-semibold text-white mb-4">Choose a Category</h2>
                                    <div className="grid grid-cols-2 gap-3">
                                        {categories.map((cat) => (
                                            <button
                                                key={cat.id}
                                                onClick={() => setSelectedCategory(cat.id)}
                                                className={`p-4 rounded-xl text-left transition-all ${
                                                    selectedCategory === cat.id
                                                        ? "bg-green-500/20 border-2 border-green-500/50"
                                                        : "bg-white/5 border-2 border-transparent hover:bg-white/10"
                                                }`}
                                            >
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className="material-symbols-outlined text-green-400">
                                                        {getCategoryIcon(cat.icon)}
                                                    </span>
                                                    <span className="font-medium text-white">{cat.name}</span>
                                                </div>
                                                <p className="text-xs text-white/50">{cat.description}</p>
                                            </button>
                                        ))}
                                    </div>
                                    <button
                                        onClick={startQuiz}
                                        disabled={loading}
                                        className="w-full mt-6 px-6 py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                                    >
                                        {loading ? (
                                            <span className="material-symbols-outlined animate-spin">progress_activity</span>
                                        ) : (
                                            <span className="material-symbols-outlined">play_arrow</span>
                                        )}
                                        Start Quiz
                                    </button>
                                </div>

                                {/* History */}
                                {history.length > 0 && (
                                    <div className="glass-card rounded-2xl p-6">
                                        <h3 className="text-sm font-medium text-white/70 mb-4 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-base">history</span>
                                            Recent Attempts
                                        </h3>
                                        <div className="space-y-2">
                                            {history.slice(0, 5).map((item) => (
                                                <div key={item.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                                                    <div>
                                                        <span className="text-sm text-white capitalize">{item.category}</span>
                                                        <span className="text-xs text-white/40 ml-2">
                                                            {item.correct}/{item.total} correct
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className={`text-sm font-bold ${getScoreColor(item.score)}`}>
                                                            {Math.round(item.score)}%
                                                        </span>
                                                        <span className="text-xs text-white/30">
                                                            {new Date(item.created_at).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* Quiz Playing */}
                        {state === "playing" && questions[currentIndex] && (
                            <motion.div
                                key={`question-${currentIndex}`}
                                initial={{ opacity: 0, x: 50 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -50 }}
                                className="glass-card rounded-2xl p-6"
                            >
                                {/* Progress */}
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-white/50">
                                            Question {currentIndex + 1} of {questions.length}
                                        </span>
                                        {isAiGenerated && (
                                            <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 text-xs flex items-center gap-1">
                                                <span className="material-symbols-outlined text-xs">auto_awesome</span>
                                                AI Generated
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex gap-1">
                                        {questions.map((_, idx) => (
                                            <div
                                                key={idx}
                                                className={`w-8 h-1 rounded-full ${
                                                    idx < currentIndex ? "bg-green-500" : idx === currentIndex ? "bg-blue-500" : "bg-white/20"
                                                }`}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Question */}
                                <h2 className="text-xl font-semibold text-white mb-6">
                                    {questions[currentIndex].question}
                                </h2>

                                {/* Options */}
                                <div className="space-y-3">
                                    {questions[currentIndex].options.map((option, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => selectAnswer(idx)}
                                            className="w-full p-4 rounded-xl bg-white/5 border border-white/10 text-left text-white hover:bg-white/10 hover:border-blue-500/50 transition-all flex items-center gap-3"
                                        >
                                            <span className="size-8 rounded-full bg-white/10 flex items-center justify-center text-sm font-medium">
                                                {String.fromCharCode(65 + idx)}
                                            </span>
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* Results */}
                        {state === "results" && (
                            <motion.div
                                key="results"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="space-y-6"
                            >
                                {/* Score Card */}
                                <div className="glass-card rounded-2xl p-8 text-center">
                                    <div className={`text-6xl font-bold mb-2 ${getScoreColor(score.percentage)}`}>
                                        {Math.round(score.percentage)}%
                                    </div>
                                    <p className="text-white/60 mb-4">
                                        You got {score.correct} out of {score.total} questions correct
                                    </p>
                                    <div className="flex justify-center gap-4">
                                        <button
                                            onClick={resetQuiz}
                                            className="px-6 py-3 rounded-xl bg-white/10 text-white hover:bg-white/20 transition-all"
                                        >
                                            Try Again
                                        </button>
                                        <button
                                            onClick={() => { setSelectedCategory("mixed"); resetQuiz(); }}
                                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:opacity-90 transition-all"
                                        >
                                            New Quiz
                                        </button>
                                    </div>
                                </div>

                                {/* Detailed Results */}
                                <div className="glass-card rounded-2xl p-6">
                                    <h3 className="text-lg font-semibold text-white mb-4">Review Answers</h3>
                                    <div className="space-y-4">
                                        {results.map((r, idx) => (
                                            <div key={idx} className={`p-4 rounded-xl ${r.is_correct ? "bg-green-500/10 border border-green-500/20" : "bg-red-500/10 border border-red-500/20"}`}>
                                                <div className="flex items-start gap-3 mb-2">
                                                    <span className={`material-symbols-outlined ${r.is_correct ? "text-green-400" : "text-red-400"}`}>
                                                        {r.is_correct ? "check_circle" : "cancel"}
                                                    </span>
                                                    <p className="text-white font-medium">{r.question}</p>
                                                </div>
                                                {!r.is_correct && (
                                                    <p className="text-sm text-white/60 ml-8 mb-2">
                                                        Correct answer: <span className="text-green-400">{r.correct_answer}</span>
                                                    </p>
                                                )}
                                                <p className="text-sm text-white/50 ml-8 p-3 rounded-lg bg-white/5">
                                                    💡 {r.explanation}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
