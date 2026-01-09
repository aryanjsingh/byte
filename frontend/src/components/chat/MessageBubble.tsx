import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSession } from 'next-auth/react';
import {
    Reasoning,
    ReasoningContent,
    ReasoningTrigger,
} from "@/components/ai-elements/reasoning";

import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";

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
}

interface MessageBubbleProps {
    message: Message;
}

const TIP_TITLES = [
    "Security Tip",
    "Byte Guard",
    "Cyber Defense",
    "Shield Up",
    "Safety Protocol",
    "Byte Insight",
    "Cyber Wisdom",
    "Defense Tactic"
];

const BlockquoteRenderer = ({ children, ...props }: any) => {
    // Use useMemo to generate title once and keep it stable
    const title = React.useMemo(() => TIP_TITLES[Math.floor(Math.random() * TIP_TITLES.length)], []);
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div
            className="my-6 bg-amber-50 dark:bg-amber-900/10 border-l-4 border-amber-500 dark:border-amber-600 rounded-r-sm shadow-md relative overflow-hidden transition-all duration-300 hover:bg-amber-100/50 dark:hover:bg-amber-900/20 cursor-pointer group"
            onClick={() => setIsOpen(!isOpen)}
        >
            <div className={`absolute top-0 right-0 w-24 h-24 bg-amber-100 dark:bg-amber-800/10 rounded-bl-full opacity-30 transition-transform duration-500 ${isOpen ? 'scale-150' : 'scale-100'}`}></div>

            <div className="p-4 flex items-center gap-3 relative z-10">
                <span className="material-symbols-outlined text-amber-600 dark:text-amber-500 text-[24px] shrink-0">shield</span>
                <div className="flex-1 flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-700 dark:text-amber-500 uppercase tracking-widest">{title}</span>
                    <span className={`material-symbols-outlined text-amber-600 dark:text-amber-500 text-[20px] transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}>
                        expand_more
                    </span>
                </div>
            </div>

            <div
                className={`grid transition-all duration-300 ease-in-out ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}
            >
                <div className="overflow-hidden">
                    <div className="px-5 pb-5 pt-0 pl-[52px]">
                        <blockquote className="text-amber-900 dark:text-amber-200 font-semibold leading-relaxed m-0" {...props}>
                            {children}
                        </blockquote>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';
    const { data: session } = useSession();
    const [isSpeaking, setIsSpeaking] = useState(false);

    const handleSpeak = async () => {
        if (isSpeaking) return;

        setIsSpeaking(true);
        try {
            const token = (session as any)?.accessToken;
            // Clean content for speech (remove markdown basics if needed, but simpler is fine)
            // Just sending raw content for now, backend Piper handles some punctuation
            const response = await fetch("http://localhost:8000/tts", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ text: message.content })
            });

            if (!response.ok) throw new Error("TTS failed");

            const data = await response.json();
            if (data.audio) {
                const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
                audio.onended = () => setIsSpeaking(false);
                audio.play();
            } else {
                setIsSpeaking(false);
            }
        } catch (e) {
            console.error("TTS Error:", e);
            setIsSpeaking(false);
        }
    };

    if (isUser) {
        return (
            <div className="flex flex-row-reverse gap-4 group">
                <div
                    className="size-8 shrink-0 rounded-sm bg-cover bg-center mt-0.5 ring-1 ring-slate-200 dark:ring-white/10"
                    style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuB5WdPzHGhg_JAl03-xGWmaeGXOOAMw1k7EiEdkk1ZyR74ymN5ovU1YaMQJjxnadzTLasjBrBVZV7JtSOlTUjdglbRDF07mLWMzZUbLWDFfEd2z5msdwI_SSoaC-cbDgeWN5-gCK52ugOhOxt5QRuyQiCogkhBBIlJnOoSwesf-cDCsq3EFgqlJSnGBqONYG0SenUoNd3Dwyq_nmV1oj91ML1ZYsf80q9J6PvTG1YnkY46zyCQ8AGvwESpxlsZabNAPqwM72aZHIO0")' }}
                ></div>
                <div className="flex flex-col items-end gap-1 max-w-[85%]">
                    <div className="flex items-center gap-2 flex-row-reverse">
                        <span className="text-xs font-bold text-pl-text-dark dark:text-white">USER</span>
                    </div>
                    <div className="px-6 py-4 bg-pl-brand dark:bg-pl-border text-white dark:text-pl-text-primary rounded-sm border border-transparent dark:border-white/5 shadow-md tracking-wide">
                        <div className="text-base leading-relaxed whitespace-pre-wrap">{message.content}</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex gap-4 relative group animate-fade-in-up">
            <div className="absolute left-[15px] top-[36px] bottom-6 w-[2px] bg-gradient-to-b from-pl-brand/0 via-pl-brand/50 to-pl-brand/0 animate-stream" style={{ backgroundSize: '100% 200%' }}></div>
            <div className="size-8 shrink-0 rounded-sm bg-white dark:bg-pl-panel border border-slate-200 dark:border-pl-border flex items-center justify-center mt-0.5 z-10 shadow-sm">
                <span className="material-symbols-outlined text-[18px] text-pl-brand">smart_toy</span>
            </div>
            <div className="flex flex-col gap-2 max-w-[90%] sm:max-w-[85%]">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-pl-text-dark dark:text-pl-brand">BYTE</span>
                    {message.mode === 'turbo' && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-sm bg-blue-50 dark:bg-pl-brand/10 text-pl-brand border border-blue-100 dark:border-pl-brand/20 text-[9px] font-bold uppercase tracking-wide">
                            <span className="material-symbols-outlined filled text-[10px]">bolt</span>
                            Turbo Analysis
                        </span>
                    )}
                </div>

                {/* Thinking/Reasoning Display */}
                {message.thinking && message.thinking.trim() && (
                    <div className="mb-4">
                        <Reasoning className="w-full" isStreaming={message.isStreaming || false}>
                            <ReasoningTrigger />
                            <ReasoningContent>
                                {message.thinking}
                            </ReasoningContent>
                        </Reasoning>
                    </div>
                )}

                {/* Tool Invocations (Live) - Using ai-elements */}
                {message.toolInvocations && message.toolInvocations.map((tool, idx) => {
                    // Map our status to ai-elements state
                    let toolState: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' = 'input-streaming';
                    if (tool.status === 'calling') toolState = 'input-available'; // or input-streaming
                    if (tool.status === 'completed') toolState = 'output-available';
                    if (tool.status === 'failed') toolState = 'output-error';

                    return (
                        <Tool key={tool.id || idx} open={true}>
                            <ToolHeader
                                type="tool-call"
                                title={tool.name}
                                state={toolState}
                            />
                            <ToolContent>
                                {/* Input parameters hidden as per user request */}
                                {tool.result && <ToolOutput output={tool.result} errorText={tool.status === 'failed' ? "Tool execution failed" : undefined} />}
                            </ToolContent>
                        </Tool>
                    );
                })}

                <div className="bg-white dark:bg-pl-panel p-6 rounded-sm border border-slate-200 dark:border-pl-border shadow-sm dark:shadow-glow group tracking-wide">
                    <div className="prose prose-sm dark:prose-invert max-w-none text-pl-text-med dark:text-pl-text-primary
                        prose-p:leading-6 prose-p:mb-4
                        prose-ul:my-4 prose-ul:space-y-2 prose-pl-0
                        prose-li:leading-6 prose-li:flex prose-li:gap-2 before:content-none
                        prose-headings:text-pl-text-dark dark:prose-headings:text-white prose-headings:font-bold prose-headings:mb-3 prose-headings:mt-6
                        prose-strong:font-bold prose-strong:text-pl-text-dark dark:prose-strong:text-white
                        prose-pre:bg-pl-bg-light dark:prose-pre:bg-black/20 prose-pre:border prose-pre:border-slate-200 dark:prose-pre:border-white/10 prose-pre:rounded-sm">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                ul: ({ node, ...props }) => (
                                    <div className="my-6 p-6 bg-pl-bg-light dark:bg-white/5 border-l-4 border-pl-brand rounded-sm relative overflow-hidden shadow-sm">
                                        <div className="text-[10px] font-bold text-pl-brand dark:text-pl-text-secondary uppercase tracking-widest mb-4 opacity-80">
                                            Detailed Analysis
                                        </div>
                                        <ul className="space-y-4" {...props} />
                                    </div>
                                ),
                                ol: ({ node, ...props }) => (
                                    <div className="my-6 p-6 bg-pl-bg-light dark:bg-white/5 border-l-4 border-pl-brand rounded-sm relative overflow-hidden shadow-sm">
                                        <div className="text-[10px] font-bold text-pl-brand dark:text-pl-text-secondary uppercase tracking-widest mb-4 opacity-80">
                                            Step-by-Step Breakdown
                                        </div>
                                        <ol className="list-decimal pl-4 space-y-4" {...props} />
                                    </div>
                                ),
                                li: ({ node, children, ...props }) => {
                                    return (
                                        <li className="flex gap-3 text-[15px] leading-relaxed group/li" {...props}>
                                            <span className="text-pl-brand mt-1.5 shrink-0 transition-transform group-hover/li:scale-125">•</span>
                                            <span className="flex-1">{children}</span>
                                        </li>
                                    )
                                },
                                a: ({ node, ...props }) => <a className="text-pl-brand hover:underline font-medium break-all" target="_blank" rel="noopener noreferrer" {...props} />,
                                blockquote: ({ node, children, ...props }) => {
                                    // Use a hook-based component logic inline or extract it. 
                                    // extracting to a defined component is safer for hooks.
                                    return <BlockquoteRenderer {...props}>{children}</BlockquoteRenderer>;
                                },
                                p: ({ node, children, ...props }) => {
                                    return <p className="font-bold leading-loose mb-6" {...props}>{children}</p>;
                                },
                                code: ({ node, className, children, ...props }) => {
                                    const match = /language-(\w+)/.exec(className || '');
                                    const isInline = !match;
                                    return isInline ? (
                                        <code className="bg-slate-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono text-pl-text-dark dark:text-pl-text-primary border border-slate-200 dark:border-white/5" {...props}>
                                            {children}
                                        </code>
                                    ) : (
                                        <code className={className} {...props}>
                                            {children}
                                        </code>
                                    );
                                }
                            }}
                        >
                            {message.content.replace(/\]\s+\(/g, '](')}
                        </ReactMarkdown>
                        {/* Streaming cursor */}
                        {message.isStreaming && (
                            <span className="inline-block w-2 h-4 bg-pl-brand animate-pulse ml-1 align-middle"></span>
                        )}
                    </div>

                    {/* Tool Tags */}
                    {message.role === 'assistant' && message.tool_calls && message.tool_calls.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-white/5 opacity-80 hover:opacity-100 transition-opacity">
                            {message.tool_calls.map((tool, idx) => {
                                const toolMap: Record<string, { label: string, color: string, icon: string }> = {
                                    'virustotal_scan': { label: 'VirusTotal', color: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800', icon: 'security' },
                                    'greynoise_ip_check': { label: 'GreyNoise', color: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800', icon: 'router' },
                                    'update_user_security_profile': { label: 'Profile Updated', color: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800', icon: 'person_search' },
                                };
                                const config = toolMap[tool] || { label: tool, color: 'bg-slate-50 dark:bg-white/5 text-pl-text-med dark:text-pl-text-secondary border-slate-200 dark:border-white/10', icon: 'settings' };

                                return (
                                    <div key={idx} className={`flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-bold uppercase tracking-wider ${config.color} select-none`}>
                                        <span className="material-symbols-outlined text-[12px]">{config.icon}</span>
                                        {config.label}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div className="flex items-center gap-1 mt-4 pt-3 border-t border-slate-100 dark:border-white/5">
                        <button
                            onClick={handleSpeak}
                            disabled={isSpeaking}
                            className={`p-1.5 rounded hover:bg-slate-100 dark:hover:bg-white/5 text-pl-text-sub hover:text-pl-text-dark dark:text-pl-text-secondary dark:hover:text-pl-text-primary transition-colors ${isSpeaking ? 'text-pl-brand animate-pulse' : ''}`}
                            title="Speak"
                        >
                            <span className="material-symbols-outlined text-[16px]">
                                {isSpeaking ? 'volume_up' : 'volume_mute'}
                            </span>
                        </button>
                        <button className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-white/5 text-pl-text-sub hover:text-pl-text-dark dark:text-pl-text-secondary dark:hover:text-pl-text-primary transition-colors" title="Copy to Clipboard">
                            <span className="material-symbols-outlined text-[16px]">content_copy</span>
                        </button>
                        <button className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-white/5 text-pl-text-sub hover:text-pl-text-dark dark:text-pl-text-secondary dark:hover:text-pl-text-primary transition-colors" title="Regenerate Response">
                            <span className="material-symbols-outlined text-[16px]">refresh</span>
                        </button>
                        <div className="w-px h-3 bg-slate-200 dark:bg-white/10 mx-1"></div>
                        <button className="p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20 text-pl-text-sub hover:text-green-600 dark:text-pl-text-secondary dark:hover:text-green-400 transition-colors">
                            <span className="material-symbols-outlined text-[16px]">thumb_up</span>
                        </button>
                        <button className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-pl-text-sub hover:text-red-600 dark:text-pl-text-secondary dark:hover:text-red-400 transition-colors">
                            <span className="material-symbols-outlined text-[16px]">thumb_down</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
