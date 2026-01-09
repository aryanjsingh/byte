'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function SignupPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [focusedField, setFocusedField] = useState<string | null>(null);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            const res = await fetch('http://localhost:8000/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name }),
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

    const inputFields = [
        { id: 'name', label: 'Full Name', type: 'text', icon: 'person', placeholder: 'John Doe', value: name, onChange: setName },
        { id: 'email', label: 'Email address', type: 'email', icon: 'mail', placeholder: 'you@example.com', value: email, onChange: setEmail },
        { id: 'password', label: 'Password', type: 'password', icon: 'lock', placeholder: '••••••••', value: password, onChange: setPassword },
        { id: 'confirm', label: 'Confirm Password', type: 'password', icon: 'lock_reset', placeholder: '••••••••', value: confirmPassword, onChange: setConfirmPassword },
    ];

    return (
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 py-10">
            {/* Animated Background */}
            <div className="animated-bg" />
            
            {/* Floating Orbs */}
            <motion.div
                animate={{ 
                    y: [0, -40, 0],
                    x: [0, 30, 0],
                    scale: [1, 1.15, 1]
                }}
                transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-1/3 left-1/5 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl"
            />
            <motion.div
                animate={{ 
                    y: [0, 30, 0],
                    x: [0, -40, 0],
                    scale: [1, 1.2, 1]
                }}
                transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                className="absolute bottom-1/3 right-1/5 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl"
            />
            <motion.div
                animate={{ 
                    y: [0, -20, 0],
                    scale: [1, 1.1, 1]
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-3xl"
            />

            <motion.main
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-[440px] relative z-10"
            >
                <div className="glass-card rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden">
                    {/* Animated Gradient Border */}
                    <div className="absolute inset-0 rounded-3xl p-[1px] pointer-events-none overflow-hidden">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-[-50%] bg-[conic-gradient(from_0deg,transparent,#3b82f6,transparent,#8b5cf6,transparent)]"
                            style={{ opacity: 0.3 }}
                        />
                    </div>

                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="flex flex-col items-center mb-8 relative"
                    >
                        <motion.div
                            whileHover={{ scale: 1.05, rotate: -5 }}
                            className="relative mb-5"
                        >
                            <div className="size-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white shadow-2xl glow-purple">
                                <span className="material-symbols-outlined text-[32px]">rocket_launch</span>
                            </div>
                            <motion.div
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                                className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/30 to-pink-600/30 blur-xl -z-10"
                            />
                        </motion.div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Create your account</h1>
                        <p className="text-sm text-white/50 mt-2 text-center max-w-xs">
                            Join Byte AI and unlock the power of intelligent assistance
                        </p>
                    </motion.div>

                    {/* Form */}
                    <form className="space-y-4" onSubmit={handleSubmit}>
                        {inputFields.map((field, index) => (
                            <motion.div
                                key={field.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3 + index * 0.1 }}
                            >
                                <label className="block text-sm font-medium text-white/70 mb-2" htmlFor={field.id}>
                                    {field.label}
                                </label>
                                <div className={`relative rounded-xl transition-all duration-300 ${
                                    focusedField === field.id ? 'ring-2 ring-purple-500/50' : ''
                                }`}>
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                        <span className={`material-symbols-outlined text-[20px] transition-colors ${
                                            focusedField === field.id ? 'text-purple-400' : 'text-white/30'
                                        }`}>{field.icon}</span>
                                    </div>
                                    <input
                                        className="block w-full pl-12 pr-4 py-3.5 rounded-xl glass-input text-white placeholder-white/30 text-sm"
                                        id={field.id}
                                        placeholder={field.placeholder}
                                        required
                                        type={field.type}
                                        value={field.value}
                                        onChange={(e) => field.onChange(e.target.value)}
                                        onFocus={() => setFocusedField(field.id)}
                                        onBlur={() => setFocusedField(null)}
                                    />
                                </div>
                            </motion.div>
                        ))}

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
                            transition={{ delay: 0.6 }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-600 text-white font-semibold text-sm shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-6"
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
                                    Create Account
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
                        transition={{ delay: 0.7 }}
                        className="grid grid-cols-2 gap-3"
                    >
                        {[
                            { name: 'Google', icon: 'G', gradient: 'hover:from-red-500/10 hover:to-yellow-500/10' },
                            { name: 'GitHub', icon: 'GH', gradient: 'hover:from-gray-500/10 hover:to-gray-400/10' }
                        ].map((provider) => (
                            <motion.button
                                key={provider.name}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                type="button"
                                className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl glass-input text-white/70 hover:text-white text-sm font-medium transition-all bg-gradient-to-r from-transparent to-transparent ${provider.gradient}`}
                            >
                                <span className="font-bold">{provider.icon}</span>
                                {provider.name}
                            </motion.button>
                        ))}
                    </motion.div>

                    {/* Login Link */}
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.8 }}
                        className="mt-8 text-center text-sm text-white/50"
                    >
                        Already have an account?{' '}
                        <Link
                            href="/login"
                            className="font-semibold text-purple-400 hover:text-purple-300 transition-colors"
                        >
                            Sign in
                        </Link>
                    </motion.p>
                </div>

                {/* Footer */}
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.9 }}
                    className="mt-6 text-center text-xs text-white/20"
                >
                    By signing up, you agree to our Terms of Service and Privacy Policy
                </motion.p>
            </motion.main>
        </div>
    );
}
