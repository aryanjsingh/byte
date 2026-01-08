'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignupPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validate password match
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            const res = await fetch('http://localhost:8000/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (res.ok) {
                router.push('/login');
            } else {
                const data = await res.json();
                setError(data.detail || 'Signup failed');
            }
        } catch (err) {
            setError("Connection failed");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-background-light dark:bg-background-dark text-zinc-900 dark:text-zinc-200 font-display transition-colors duration-200 selection:bg-zinc-700 selection:text-white flex items-center justify-center min-h-screen">
            <div className="w-full max-w-[440px] px-6 py-10 sm:px-10 bg-surface-light dark:bg-surface-darker rounded-3xl shadow-2xl border border-zinc-200 dark:border-zinc-800/60 relative overflow-hidden mx-4">
                {/* Top gradient line */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-zinc-400 dark:via-zinc-600 to-transparent opacity-20"></div>

                {/* Header */}
                <div className="flex flex-col items-center mb-8">
                    <div className="size-14 rounded-2xl bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 mb-5 shadow-lg shadow-zinc-900/10 dark:shadow-none">
                        <span className="material-symbols-outlined text-[32px]">smart_toy</span>
                    </div>
                    <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">Create your account</h1>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2 text-center max-w-xs">
                        Start chatting with the AI Assistant today and boost your productivity.
                    </p>
                </div>

                {/* Form */}
                <form className="space-y-5" onSubmit={handleSubmit}>
                    {/* Email Field */}
                    <div>
                        <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5 ml-1" htmlFor="email">
                            Email address
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-400">
                                <span className="material-symbols-outlined text-[20px]">mail</span>
                            </div>
                            <input
                                className="block w-full pl-11 pr-4 py-3 rounded-xl border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:border-zinc-500 focus:ring-zinc-500 dark:focus:ring-zinc-600 dark:focus:border-zinc-600 sm:text-sm shadow-sm transition-all"
                                id="email"
                                name="email"
                                placeholder="you@example.com"
                                required
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Password Field */}
                    <div>
                        <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5 ml-1" htmlFor="password">
                            Password
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-400">
                                <span className="material-symbols-outlined text-[20px]">lock</span>
                            </div>
                            <input
                                className="block w-full pl-11 pr-4 py-3 rounded-xl border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:border-zinc-500 focus:ring-zinc-500 dark:focus:ring-zinc-600 dark:focus:border-zinc-600 sm:text-sm shadow-sm transition-all"
                                id="password"
                                name="password"
                                placeholder="••••••••"
                                required
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Confirm Password Field */}
                    <div>
                        <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5 ml-1" htmlFor="confirm-password">
                            Confirm Password
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-400">
                                <span className="material-symbols-outlined text-[20px]">lock_reset</span>
                            </div>
                            <input
                                className="block w-full pl-11 pr-4 py-3 rounded-xl border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:border-zinc-500 focus:ring-zinc-500 dark:focus:ring-zinc-600 dark:focus:border-zinc-600 sm:text-sm shadow-sm transition-all"
                                id="confirm-password"
                                name="confirm-password"
                                placeholder="••••••••"
                                required
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
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
                    <div className="pt-2">
                        <button
                            className="group w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-zinc-900/10 dark:shadow-none text-sm font-bold text-white dark:text-zinc-900 bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-zinc-900 dark:focus:ring-offset-zinc-900 transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                            type="submit"
                            disabled={isLoading}
                        >
                            <span>{isLoading ? 'Creating account...' : 'Sign Up'}</span>
                            <span className="material-symbols-outlined text-[18px] transition-transform group-hover:translate-x-1">arrow_forward</span>
                        </button>
                    </div>
                </form>

                {/* Social Login Divider */}
                <div className="mt-8">
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-zinc-200 dark:border-zinc-700/50"></div>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase tracking-wide">
                            <span className="px-3 bg-white dark:bg-surface-darker text-zinc-400 dark:text-zinc-500 font-medium">Or continue with</span>
                        </div>
                    </div>

                    {/* Social Login Buttons */}
                    <div className="mt-6 grid grid-cols-2 gap-3">
                        <button
                            className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800/30 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 hover:text-zinc-900 dark:hover:text-zinc-100 transition-all"
                            type="button"
                            onClick={() => setError('Google sign-in coming soon!')}
                        >
                            <svg aria-hidden="true" className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"></path>
                            </svg>
                            <span className="text-sm font-semibold">Google</span>
                        </button>
                        <button
                            className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800/30 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 hover:text-zinc-900 dark:hover:text-zinc-100 transition-all"
                            type="button"
                            onClick={() => setError('GitHub sign-in coming soon!')}
                        >
                            <svg aria-hidden="true" className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                                <path clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" fillRule="evenodd"></path>
                            </svg>
                            <span className="text-sm font-semibold">GitHub</span>
                        </button>
                    </div>
                </div>

                {/* Login Link */}
                <p className="mt-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
                    Already have an account?{' '}
                    <Link
                        href="/login"
                        className="font-bold text-zinc-900 dark:text-zinc-100 hover:text-zinc-700 dark:hover:text-white hover:underline transition-all"
                    >
                        Log in
                    </Link>
                </p>
            </div>
        </div>
    );
}
