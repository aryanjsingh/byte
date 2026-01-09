import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSession } from 'next-auth/react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Reasoning,
    ReasoningContent,
    ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import { Tool, ToolContent, ToolHeader, ToolOutput } from "@/components/ai-elements/tool";

interface Message {
    role: 'user' | 'assistant';
    content: string;
    thinking?: string;
    mode?: 'simple' | 'turbo';
    tool_calls?: string[];
    toolInvocations?: Array<{
        id: string;
        name: string;
        args?: any;
        result?: string;
        status: 'calling' | 'completed' | 'failed';
    }>;
    isNew?: boolean;
    isStreaming?: boolean;
    imageData?: string;
    imageMimeType?: string;
    images?: Array<{
        url: string;
        thumbnail?: string;
        title?: string;
    }>;
    generatedImage?: {
        base64: string;
        mimeType: string;
        prompt: string;
    };
}

interface MessageBubbleProps {
    message: Message;
    index?: number;
}

const TIP_TITLES = ["Security Tip", "Byte Guard", "Cyber Defense", "Shield Up", "Safety Protocol"];

const BlockquoteRenderer = ({ children, ...props }: any) => {
    const title = useMemo(() => TIP_TITLES[Math.floor(Math.random() * TIP_TITLES.length)], []);
    const [isOpen, setIsOpen] = useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="my-6 glass-card rounded-xl overflow-hidden cursor-pointer group"
            onClick={() => setIsOpen(!isOpen)}
        >
            <div className="p-4 flex items-center gap-3 border-l-4 border-amber-500">
                <span className="material-symbols-outlined text-amber-400 text-[24px]">shield</span>
                <div className="flex-1 flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-400 uppercase tracking-widest">{title}</span>
                    <motion.span
                        animate={{ rotate: isOpen ? 180 : 0 }}
                        className="material-symbols-outlined text-amber-400 text-[20px]"
                    >
                        expand_more
                    </motion.span>
                </div>
            </div>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 pl-[52px]">
                            <blockquote className="text-amber-200/80 font-medium leading-relaxed" {...props}>
                                {children}
                            </blockquote>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default function MessageBubble({ message, index = 0 }: MessageBubbleProps) {
    const isUser = message.role === 'user';
    const { data: session } = useSession();
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [copied, setCopied] = useState(false);
    const audioRef = React.useRef<HTMLAudioElement | null>(null);

    const handleSpeak = async () => {
        // If already speaking, stop it
        if (isSpeaking) {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.currentTime = 0;
                audioRef.current = null;
            }
            // Also cancel any browser speech synthesis
            window.speechSynthesis?.cancel();
            setIsSpeaking(false);
            return;
        }

        setIsSpeaking(true);
        try {
            const token = (session as any)?.accessToken;
            const response = await fetch("http://localhost:8000/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
                body: JSON.stringify({ text: message.content })
            });
            if (!response.ok) throw new Error("TTS failed");
            const data = await response.json();
            if (data.audio) {
                const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
                audioRef.current = audio;
                audio.onended = () => {
                    setIsSpeaking(false);
                    audioRef.current = null;
                };
                audio.play();
            } else {
                setIsSpeaking(false);
            }
        } catch (e) {
            setIsSpeaking(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (isUser) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20, x: 20 }}
                animate={{ opacity: 1, y: 0, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="flex flex-row-reverse gap-4"
            >
                <div
                    className="size-10 shrink-0 rounded-xl bg-cover bg-center ring-2 ring-white/10"
                    style={{ backgroundImage: 'url("https://api.dicebear.com/7.x/initials/svg?seed=U&backgroundColor=6366f1")' }}
                />
                <div className="flex flex-col items-end gap-2 max-w-[80%]">
                    <span className="text-xs font-semibold text-white/40 uppercase tracking-wide">You</span>
                    <motion.div
                        whileHover={{ scale: 1.01 }}
                        className="message-user px-5 py-4 rounded-2xl rounded-tr-md shadow-lg"
                    >
                        {message.imageData && message.imageMimeType && (
                            <img
                                src={`data:${message.imageMimeType};base64,${message.imageData}`}
                                alt="Uploaded"
                                className="max-w-sm rounded-lg mb-3 border border-white/10"
                            />
                        )}
                        {message.content && (
                            <p className="text-white text-[15px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
                        )}
                    </motion.div>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.05 }}
            className="flex gap-4 relative"
        >
            {/* Animated Line */}
            <div className="absolute left-[19px] top-[48px] bottom-8 w-[2px] bg-gradient-to-b from-blue-500/50 via-purple-500/30 to-transparent animate-stream" style={{ backgroundSize: '100% 200%' }} />

            {/* Avatar */}
            <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="relative z-10"
            >
                <div className="size-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg glow-blue">
                    <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                </div>
            </motion.div>

            <div className="flex flex-col gap-3 max-w-[85%] flex-1">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">Byte</span>
                    {message.mode === 'turbo' && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30"
                        >
                            <span className="material-symbols-outlined text-[12px] text-blue-400">bolt</span>
                            <span className="text-[10px] font-bold text-blue-400 uppercase">Turbo</span>
                        </motion.span>
                    )}
                    {/* Speaker Button */}
                    <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={handleSpeak}
                        className={`p-1.5 rounded-lg transition-all ${isSpeaking
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                            }`}
                        title="Speak"
                    >
                        <span className="material-symbols-outlined text-[14px]">{isSpeaking ? 'volume_up' : 'volume_mute'}</span>
                    </motion.button>
                </div>

                {/* Thinking/Reasoning */}
                {message.thinking && message.thinking.trim() && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mb-2"
                    >
                        <Reasoning className="w-full" isStreaming={message.isStreaming || false} defaultOpen={false}>
                            <ReasoningTrigger />
                            <ReasoningContent>{message.thinking}</ReasoningContent>
                        </Reasoning>
                    </motion.div>
                )}

                {/* Tool Invocations */}
                <AnimatePresence>
                    {message.toolInvocations?.filter(tool => {
                        const hiddenTools = ['cybersecurity_knowledge_search', 'risk_management_framework_query', 'image_search', 'image_gen'];
                        return !hiddenTools.includes(tool.name);
                    }).map((tool, idx) => {
                        let toolState: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' = 'input-streaming';
                        if (tool.status === 'calling') toolState = 'input-available';
                        if (tool.status === 'completed') toolState = 'output-available';
                        if (tool.status === 'failed') toolState = 'output-error';

                        return (
                            <motion.div
                                key={tool.id || idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="mb-4"
                            >
                                {/* Styled collapsible with blue theme */}
                                <div className="rounded-xl bg-blue-500/10 border border-blue-500/20 overflow-hidden">
                                    <Tool defaultOpen={true}>
                                        <ToolHeader type="tool-call" title={tool.name} state={toolState} />
                                        <ToolContent>
                                            {tool.result && (
                                                <div className="p-4 bg-blue-500/5">
                                                    <div className="text-sm text-white/80 whitespace-pre-wrap font-mono">
                                                        {/* Parse and format the result nicely */}
                                                        {tool.result.split('\n').map((line, i) => {
                                                            // Highlight key metrics
                                                            if (line.includes('Malicious:')) {
                                                                const count = line.match(/\d+/)?.[0] || '0';
                                                                const isRisky = parseInt(count) > 0;
                                                                return (
                                                                    <div key={i} className={`flex items-center gap-2 py-1 ${isRisky ? 'text-red-400' : 'text-green-400'}`}>
                                                                        <span className="material-symbols-outlined text-[14px]">{isRisky ? 'error' : 'check_circle'}</span>
                                                                        <span className="font-semibold">{line}</span>
                                                                    </div>
                                                                );
                                                            }
                                                            if (line.includes('Suspicious:')) {
                                                                const count = line.match(/\d+/)?.[0] || '0';
                                                                const isRisky = parseInt(count) > 0;
                                                                return (
                                                                    <div key={i} className={`flex items-center gap-2 py-1 ${isRisky ? 'text-amber-400' : 'text-green-400'}`}>
                                                                        <span className="material-symbols-outlined text-[14px]">{isRisky ? 'warning' : 'check_circle'}</span>
                                                                        <span className="font-semibold">{line}</span>
                                                                    </div>
                                                                );
                                                            }
                                                            if (line.includes('Harmless:') || line.includes('Undetected:')) {
                                                                return (
                                                                    <div key={i} className="flex items-center gap-2 py-1 text-white/60">
                                                                        <span className="material-symbols-outlined text-[14px]">info</span>
                                                                        <span>{line}</span>
                                                                    </div>
                                                                );
                                                            }
                                                            if (line.includes('Link:')) {
                                                                const url = line.replace('Link:', '').trim();
                                                                return (
                                                                    <div key={i} className="flex items-center gap-2 py-2 mt-2 border-t border-white/10">
                                                                        <span className="material-symbols-outlined text-[14px] text-blue-400">open_in_new</span>
                                                                        <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline text-xs">
                                                                            View Full Report on VirusTotal
                                                                        </a>
                                                                    </div>
                                                                );
                                                            }
                                                            if (line.includes('Report for')) {
                                                                return (
                                                                    <div key={i} className="text-white/90 font-semibold pb-2 border-b border-white/10 mb-2">
                                                                        {line}
                                                                    </div>
                                                                );
                                                            }
                                                            return line ? <div key={i} className="py-0.5">{line}</div> : null;
                                                        })}
                                                    </div>
                                                </div>
                                            )}
                                        </ToolContent>
                                    </Tool>
                                </div>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>

                {/* Message Content */}
                <motion.div
                    whileHover={{ scale: 1.005 }}
                    className="message-assistant p-6 rounded-2xl rounded-tl-md shadow-xl"
                >
                    <div className="prose prose-sm prose-invert max-w-none text-white/80
                        prose-p:leading-7 prose-p:mb-4
                        prose-headings:text-white prose-headings:font-bold
                        prose-strong:text-white prose-strong:font-semibold
                        prose-code:bg-white/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-blue-300 prose-code:text-sm
                        prose-pre:bg-black/30 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl
                        prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                        prose-ul:space-y-2 prose-li:text-white/70">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                ul: ({ node, ...props }) => (
                                    <div className="my-4 p-4 glass-subtle rounded-xl border-l-2 border-blue-500/50">
                                        <ul className="space-y-3 list-none" {...props} />
                                    </div>
                                ),
                                ol: ({ node, ...props }) => (
                                    <div className="my-4 p-4 glass-subtle rounded-xl border-l-2 border-purple-500/50">
                                        <ol className="list-decimal pl-4 space-y-3" {...props} />
                                    </div>
                                ),
                                li: ({ node, children, ...props }) => (
                                    <li className="flex gap-3 text-[15px] leading-relaxed" {...props}>
                                        <span className="text-blue-400 mt-1">•</span>
                                        <span className="flex-1 text-white/70">{children}</span>
                                    </li>
                                ),
                                blockquote: BlockquoteRenderer,
                                p: ({ node, children, ...props }) => (
                                    <p className="text-[15px] leading-7 text-white/80" {...props}>{children}</p>
                                ),
                                code: ({ node, className, children, ...props }) => {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !match ? (
                                        <code className="bg-white/10 px-1.5 py-0.5 rounded text-sm font-mono text-blue-300" {...props}>
                                            {children}
                                        </code>
                                    ) : (
                                        <code className={className} {...props}>{children}</code>
                                    );
                                }
                            }}
                        >
                            {message.content.replace(/\]\s+\(/g, '](')}
                        </ReactMarkdown>

                        {/* Streaming Cursor */}
                        {message.isStreaming && (
                            <motion.span
                                animate={{ opacity: [1, 0] }}
                                transition={{ duration: 0.8, repeat: Infinity }}
                                className="inline-block w-2 h-5 bg-blue-400 ml-1 align-middle rounded-sm"
                            />
                        )}
                    </div>

                    {/* Image Grid from image_search tool */}
                    {message.images && message.images.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-6 pt-6 border-t border-white/10"
                        >
                            <div className="text-sm text-white/50 mb-3 font-medium">Related Images:</div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {message.images.slice(0, 4).map((img, idx) => (
                                    <motion.a
                                        key={idx}
                                        href={img.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="group relative overflow-hidden rounded-xl glass-card border border-white/10 hover:border-blue-500/50 transition-all duration-300"
                                        whileHover={{ scale: 1.01, y: -2 }}
                                        whileTap={{ scale: 0.99 }}
                                    >
                                        <div className="relative overflow-hidden bg-black/20">
                                            <img
                                                src={img.url}
                                                alt={img.title || `Image ${idx + 1}`}
                                                className="w-full h-auto max-h-[300px] object-contain group-hover:scale-105 transition-transform duration-500"
                                                loading="lazy"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3">
                                                <span className="text-white text-sm line-clamp-2">{img.title}</span>
                                            </div>
                                            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                                <span className="material-symbols-outlined text-white text-[16px] bg-black/50 rounded-full p-1.5">
                                                    open_in_new
                                                </span>
                                            </div>
                                        </div>
                                    </motion.a>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Generated Image from image_gen tool */}

                    {message.generatedImage && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="mt-6 pt-6 border-t border-white/10"
                        >
                            <div className="flex items-center gap-2 text-sm text-purple-400 mb-3 font-medium">
                                <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
                                AI Generated Image
                            </div>
                            <div className="relative group rounded-xl overflow-hidden border-2 border-purple-500/30 hover:border-purple-500/60 transition-all duration-300 shadow-lg shadow-purple-500/10">
                                <img
                                    src={`data:${message.generatedImage.mimeType};base64,${message.generatedImage.base64}`}
                                    alt={message.generatedImage.prompt || "AI Generated"}
                                    className="w-full rounded-xl"
                                />
                                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                    <p className="text-white text-sm font-medium line-clamp-2">
                                        {message.generatedImage.prompt}
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    )}

                </motion.div>
            </div>
        </motion.div>
    );
}
