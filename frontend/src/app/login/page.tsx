'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const res = await signIn('credentials', {
                redirect: false,
                email,
                password,
            });

            if (res?.error) {
                setError('Invalid credentials');
            } else {
                router.push('/');
            }
        } catch (err) {
            setError('An unexpected error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-background-light dark:bg-background-dark text-zinc-900 dark:text-zinc-200 font-display transition-colors duration-200 selection:bg-zinc-700 selection:text-white flex items-center justify-center min-h-screen relative overflow-hidden">
            {/* Background blur effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-zinc-200 dark:bg-zinc-800/20 blur-[120px]"></div>
                <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-zinc-300 dark:bg-zinc-900/40 blur-[100px]"></div>
            </div>

            <main className="w-full max-w-[420px] mx-4 relative z-10">
                <div className="bg-surface-light dark:bg-surface-darker border border-border-light dark:border-border-dark rounded-2xl shadow-2xl p-8 sm:p-10 backdrop-blur-sm">
                    {/* Header */}
                    <div className="flex flex-col items-center mb-8">
                        <div className="size-12 rounded-xl bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 mb-4 shadow-lg ring-1 ring-zinc-900/10 dark:ring-zinc-100/20">
                            <span className="material-symbols-outlined text-[28px]">smart_toy</span>
                        </div>
                        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">Welcome back</h1>
                        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2 text-center leading-relaxed">
                            Enter your credentials to access your workspace
                        </p>
                    </div>

                    {/* Form */}
                    <form className="space-y-5" onSubmit={handleSubmit}>
                        {/* Email Field */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5" htmlFor="email">
                                Email address
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <span className="material-symbols-outlined text-zinc-400 text-[20px]">mail</span>
                                </div>
                                <input
                                    className="block w-full pl-10 pr-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-500 focus:border-transparent transition-all"
                                    id="email"
                                    placeholder="name@company.com"
                                    required
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div>
                            <div className="flex items-center justify-between mb-1.5">
                                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300" htmlFor="password">
                                    Password
                                </label>
                                <a className="text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors" href="#">
                                    Forgot password?
                                </a>
                            </div>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <span className="material-symbols-outlined text-zinc-400 text-[20px]">lock</span>
                                </div>
                                <input
                                    className="block w-full pl-10 pr-3 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-500 focus:border-transparent transition-all"
                                    id="password"
                                    placeholder="••••••••"
                                    required
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="text-red-500 dark:text-red-400 text-sm text-center bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                                {error}
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-semibold text-sm hover:bg-zinc-800 dark:hover:bg-white/90 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                            type="submit"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Signing in...' : 'Sign in'}
                            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                        </button>
                    </form>

                    {/* Sign Up Link */}
                    <div className="mt-8 pt-6 border-t border-zinc-100 dark:border-zinc-800 text-center">
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                            Don't have an account?{' '}
                            <Link
                                href="/signup"
                                className="font-semibold text-zinc-900 dark:text-zinc-100 hover:underline decoration-2 decoration-zinc-900/20 dark:decoration-zinc-100/20 underline-offset-2 transition-colors"
                            >
                                Sign up
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-zinc-400 dark:text-zinc-600">
                        © 2024 AI Assistant Inc.
                    </p>
                </div>
            </main>
        </div>
    );
}
