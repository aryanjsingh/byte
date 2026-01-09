'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [focusedField, setFocusedField] = useState<string | null>(null);
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
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4">
            {/* Animated Background */}
            <div className="animated-bg" />
            
            {/* Floating Orbs */}
            <motion.div
                animate={{ 
                    y: [0, -30, 0],
                    x: [0, 20, 0],
                    scale: [1, 1.1, 1]
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-500/20 rounded-full blur-3xl"
            />
            <motion.div
                animate={{ 
                    y: [0, 20, 0],
                    x: [0, -30, 0],
                    scale: [1, 1.2, 1]
                }}
                transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/15 rounded-full blur-3xl"
            />

            <motion.main
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-[420px] relative z-10"
            >
                <div className="glass-card rounded-3xl p-8 sm:p-10 shadow-2xl">
                    {/* Gradient Border Effect */}
                    <div className="absolute inset-0 rounded-3xl p-[1px] pointer-events-none">
                        <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/20 via-transparent to-purple-500/20" />
                    </div>

                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="flex flex-col items-center mb-8 relative"
                    >
                        <motion.div
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            className="relative mb-5"
                        >
                            <div className="size-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-2xl glow-gradient">
                                <span className="material-symbols-outlined text-[32px]">auto_awesome</span>
                            </div>
                            <motion.div
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                                className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-600/30 blur-xl -z-10"
                            />
                        </motion.div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Welcome back</h1>
                        <p className="text-sm text-white/50 mt-2 text-center">
                            Sign in to continue to Byte AI
                        </p>
                    </motion.div>

                    {/* Form */}
                    <form className="space-y-5" onSubmit={handleSubmit}>
                        {/* Email Field */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <label className="block text-sm font-medium text-white/70 mb-2" htmlFor="email">
                                Email address
                            </label>
                            <div className={`relative rounded-xl transition-all duration-300 ${
                                focusedField === 'email' ? 'ring-2 ring-blue-500/50' : ''
                            }`}>
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <span className={`material-symbols-outlined text-[20px] transition-colors ${
                                        focusedField === 'email' ? 'text-blue-400' : 'text-white/30'
                                    }`}>mail</span>
                                </div>
                                <input
                                    className="block w-full pl-12 pr-4 py-3.5 rounded-xl glass-input text-white placeholder-white/30 text-sm"
                                    id="email"
                                    placeholder="name@company.com"
                                    required
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    onFocus={() => setFocusedField('email')}
                                    onBlur={() => setFocusedField(null)}
                                />
                            </div>
                        </motion.div>

                        {/* Password Field */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-sm font-medium text-white/70" htmlFor="password">
                                    Password
                                </label>
                                <a className="text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors" href="#">
                                    Forgot password?
                                </a>
                            </div>
                            <div className={`relative rounded-xl transition-all duration-300 ${
                                focusedField === 'password' ? 'ring-2 ring-blue-500/50' : ''
                            }`}>
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <span className={`material-symbols-outlined text-[20px] transition-colors ${
                                        focusedField === 'password' ? 'text-blue-400' : 'text-white/30'
                                    }`}>lock</span>
                                </div>
                                <input
                                    className="block w-full pl-12 pr-4 py-3.5 rounded-xl glass-input text-white placeholder-white/30 text-sm"
                                    id="password"
                                    placeholder="••••••••"
                                    required
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    onFocus={() => setFocusedField('password')}
                                    onBlur={() => setFocusedField(null)}
                                />
                            </div>
                        </motion.div>

                        {/* Error Message */}
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                            >
                                <span className="material-symbols-outlined text-[18px]">error</span>
                                {error}
                            </motion.div>
                        )}

                        {/* Submit Button */}
                        <motion.button
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            type="submit"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <motion.div
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    className="size-5 border-2 border-white/30 border-t-white rounded-full"
                                />
                            ) : (
                                <>
                                    Sign in
                                    <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                                </>
                            )}
                        </motion.button>
                    </form>

                    {/* Divider */}
                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-white/10"></div>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="px-3 bg-[#12121a] text-white/30 font-medium">Or continue with</span>
                        </div>
                    </div>

                    {/* Social Buttons */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                        className="grid grid-cols-2 gap-3"
                    >
                        {[
                            { name: 'Google', icon: 'G' },
                            { name: 'GitHub', icon: 'GH' }
                        ].map((provider) => (
                            <motion.button
                                key={provider.name}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl glass-input text-white/70 hover:text-white text-sm font-medium transition-all"
                            >
                                <span className="font-bold">{provider.icon}</span>
                                {provider.name}
                            </motion.button>
                        ))}
                    </motion.div>

                    {/* Sign Up Link */}
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.7 }}
                        className="mt-8 text-center text-sm text-white/50"
                    >
                        Don't have an account?{' '}
                        <Link
                            href="/signup"
                            className="font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                        >
                            Sign up
                        </Link>
                    </motion.p>
                </div>

                {/* Footer */}
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.8 }}
                    className="mt-6 text-center text-xs text-white/20"
                >
                    © 2025 Byte AI. All rights reserved.
                </motion.p>
            </motion.main>
        </div>
    );
}
