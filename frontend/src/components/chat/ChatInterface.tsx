"use client";

import React, { useState, useRef, useEffect } from 'react';
import Header from '@/components/layout/Header';
import MessageBubble from '@/components/chat/MessageBubble';
import InputArea from '@/components/chat/InputArea';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    thinking?: string;
    mode?: 'simple' | 'turbo';
    tool_calls?: string[];
    isNew?: boolean;
    isStreaming?: boolean;
}

interface ChatInterfaceProps {
    threadId?: string;
}

export default function ChatInterface({ threadId }: ChatInterfaceProps) {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentThreadId, setCurrentThreadId] = useState<string | undefined>(threadId);
    const [mode, setMode] = useState<'simple' | 'turbo'>('simple');
    const [isVoiceMode, setIsVoiceMode] = useState(false);

    // WebSocket state
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [thinkingContent, setThinkingContent] = useState("");
    const [streamingContent, setStreamingContent] = useState("");
    const [isThinking, setIsThinking] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading, streamingContent, thinkingContent]);

    // WebSocket Connection Management
    useEffect(() => {
        if (status === 'authenticated' && session?.user) {
            const token = (session as any).accessToken;
            if (!token) return;

            // Create WebSocket connection
            console.log("DEBUG: Connecting to WS with token:", token?.substring(0, 10));
            const websocket = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);

            websocket.onopen = () => {
                console.log('DEBUG: WebSocket connected successfully');
                setWsConnected(true);
                setWs(websocket);
                wsRef.current = websocket;
            };

            websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'thinking') {
                        setIsThinking(true);
                        setThinkingContent(prev => prev + (data.content || ''));
                    } else if (data.type === 'answer') {
                        setStreamingContent(prev => prev + (data.content || ''));
                    } else if (data.type === 'done') {
                        // Finalize message
                        const finalMessage: Message = {
                            role: 'assistant',
                            content: streamingContent,
                            thinking: thinkingContent || undefined,
                            mode: mode,
                            tool_calls: data.tool_calls || [],
                            isNew: true,
                            isStreaming: false
                        };

                        setMessages(prev => [...prev, finalMessage]);

                        // Update thread ID if needed
                        if (!currentThreadId && data.thread_id) {
                            setCurrentThreadId(data.thread_id);
                            window.history.pushState(null, '', `/c/${data.thread_id}`);
                        }

                        // Reset streaming state
                        setThinkingContent('');
                        setStreamingContent('');
                        setIsThinking(false);
                        setIsLoading(false);

                        // Clear isNew flag after animation
                        setTimeout(() => {
                            setMessages(prev => prev.map(msg =>
                                msg === finalMessage ? { ...msg, isNew: false } : msg
                            ));
                        }, 2000);
                    } else if (data.type === 'error') {
                        console.error('WebSocket error:', data.error);
                        setMessages(prev => [...prev, {
                            role: 'assistant',
                            content: `Error: ${data.error}`
                        }]);
                        setIsLoading(false);
                        setThinkingContent('');
                        setStreamingContent('');
                        setIsThinking(false);
                    }
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            websocket.onerror = (error) => {
                console.error('DEBUG: WebSocket error observed:', error);
                setWsConnected(false);
            };

            websocket.onclose = (event) => {
                console.log(`DEBUG: WebSocket disconnected. Code: ${event.code}, Reason: ${event.reason}`);
                setWsConnected(false);
                setWs(null);
                wsRef.current = null;
            };

            return () => {
                websocket.close();
            };
        }
    }, [status, session]);

    // Handle Thread Switching
    useEffect(() => {
        setCurrentThreadId(threadId);

        if (!threadId) {
            setMessages([]);
            return;
        }

        const loadHistory = async () => {
            if (status === 'authenticated' && session?.user) {
                try {
                    const token = (session as any).accessToken;
                    const response = await fetch(`http://localhost:8000/chat/threads/${threadId}`, {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (Array.isArray(data)) {
                            const historyMessages: Message[] = data.map((log: any) => ({
                                role: log.role,
                                content: log.content,
                                thinking: log.thinking,
                                mode: log.mode,
                                tool_calls: log.tool_calls
                            }));
                            setMessages(historyMessages);
                        }
                    } else {
                        console.error("Failed to load thread");
                        setMessages([]);
                    }
                } catch (e) {
                    console.error(e);
                    setMessages([]);
                }
            }
        };

        loadHistory();
    }, [threadId, status, session]);

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !wsConnected) return;

        // Optimistically add user message
        const userMessage: Message = { role: 'user', content: input, mode: mode };
        setMessages(prev => [...prev, userMessage]);

        const messageToSend = input;
        setInput('');
        setIsLoading(true);
        setThinkingContent('');
        setStreamingContent('');

        try {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                // Send via WebSocket
                wsRef.current.send(JSON.stringify({
                    message: messageToSend,
                    thread_id: currentThreadId || 'new',
                    mode: mode
                }));
            } else {
                throw new Error('WebSocket not connected');
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not connect to the AI backend." }]);
            setIsLoading(false);
        }
    };

    const sendVoiceMessage = async (audioBlob: Blob) => {
        setIsLoading(true);
        try {
            const token = (session as any).accessToken;
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('thread_id', currentThreadId || 'new');
            formData.append('mode', mode);

            const response = await fetch('http://localhost:8000/chat/voice', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (!data.transcription && !data.response) {
                handleVoiceFinished();
                return;
            }

            if (data.transcription) {
                setMessages(prev => [...prev, { role: 'user', content: data.transcription, mode: mode }]);
            }

            const assistantMessage: Message = {
                role: 'assistant',
                content: data.response,
                mode: mode,
                tool_calls: data.tool_calls || [],
                isNew: true
            };
            setMessages(prev => [...prev, assistantMessage]);

            setTimeout(() => {
                setMessages(prev => prev.map(msg =>
                    msg === assistantMessage ? { ...msg, isNew: false } : msg
                ));
            }, 2000);

            if (data.audio) {
                const audioContent = `data:audio/wav;base64,${data.audio}`;
                const audio = new Audio(audioContent);
                audio.onended = () => {
                    handleVoiceFinished();
                };
                audio.play();
                setIsVoiceMode(true);
            }

            if (!currentThreadId && data.thread_id) {
                setCurrentThreadId(data.thread_id);
                window.history.pushState(null, '', `/c/${data.thread_id}`);
            }

        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not process voice message." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVoiceFinished = () => {
        if (isVoiceMode) {
            setTimeout(() => {
                const startBtn = document.querySelector('button[title="Start voice chat"]');
                if (startBtn instanceof HTMLElement) {
                    startBtn.click();
                }
            }, 500);
        }
    };

    if (status === 'loading') return <div>Loading...</div>;

    const isHero = messages.length === 0 && !currentThreadId;

    return (
        <main className="flex-1 flex flex-col relative min-w-0 bg-pl-bg-light dark:bg-pl-bg bg-grid-pattern h-full transition-colors duration-200">
            <Header />

            <div className="flex-1 overflow-y-auto px-4 sm:px-6 pb-4 md:pb-6 scroll-smooth custom-scrollbar">
                <div className="max-w-4xl mx-auto flex flex-col gap-6 py-6">

                    {messages.length > 0 && (
                        <div className="flex items-center gap-4 py-4 opacity-70">
                            <div className="h-px bg-slate-200 dark:bg-pl-border flex-1"></div>
                            <span className="text-[10px] font-bold text-pl-text-sub dark:text-pl-text-secondary uppercase tracking-widest">Today, 10:23 AM</span>
                            <div className="h-px bg-slate-200 dark:bg-pl-border flex-1"></div>
                        </div>
                    )}

                    {messages.length === 0 ? (
                        <div className="flex gap-4 animate-fade-in mt-10">
                            <div className="size-8 shrink-0 rounded-sm bg-white dark:bg-pl-panel border border-slate-200 dark:border-pl-border flex items-center justify-center mt-0.5 shadow-sm">
                                <span className="material-symbols-outlined text-[18px] text-pl-brand">smart_toy</span>
                            </div>
                            <div className="flex flex-col gap-2 max-w-[90%] sm:max-w-[85%]">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-pl-text-dark dark:text-pl-brand">SYSTEM</span>
                                    <span className="text-[10px] text-pl-text-sub dark:text-zinc-600">10:23:05</span>
                                </div>
                                <div className="bg-white dark:bg-pl-panel p-4 rounded-sm border border-slate-200 dark:border-pl-border shadow-sm dark:shadow-none">
                                    <p className="text-pl-text-dark dark:text-pl-text-primary text-sm leading-6">
                                        System initialized. I am ready to process requests involving code generation, text summarization, or complex topic analysis. Please input your query.
                                    </p>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-1">
                                    <button
                                        onClick={() => setInput("Explain quantum computing")}
                                        className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-transparent hover:bg-blue-50 dark:hover:bg-white/5 border border-slate-200 dark:border-pl-border hover:border-pl-brand dark:hover:border-pl-text-secondary/30 rounded-sm text-xs font-medium text-pl-brand dark:text-pl-text-secondary dark:hover:text-pl-text-primary transition-all"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">science</span>
                                        Explain quantum computing
                                    </button>
                                    <button
                                        onClick={() => setInput("Python script generation")}
                                        className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-transparent hover:bg-blue-50 dark:hover:bg-white/5 border border-slate-200 dark:border-pl-border hover:border-pl-brand dark:hover:border-pl-text-secondary/30 rounded-sm text-xs font-medium text-pl-brand dark:text-pl-text-secondary dark:hover:text-pl-text-primary transition-all"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">code</span>
                                        Python script generation
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg, index) => (
                            <MessageBubble key={index} message={msg} />
                        ))
                    )}

                    {/* Show streaming thinking and answer */}
                    {(isThinking || streamingContent) && (
                        <MessageBubble
                            message={{
                                role: 'assistant',
                                content: streamingContent,
                                thinking: thinkingContent,
                                mode: mode,
                                isStreaming: true
                            }}
                        />
                    )}

                    {isLoading && !isThinking && !streamingContent && (
                        <div className="flex gap-4 animate-pulse">
                            <div className="size-8 shrink-0 rounded-sm bg-white dark:bg-pl-panel border border-slate-200 dark:border-pl-border flex items-center justify-center mt-0.5">
                                <span className="material-symbols-outlined text-[18px] text-pl-brand animate-spin">sync</span>
                            </div>
                            <div className="flex flex-col gap-2">
                                <span className="text-xs font-bold text-pl-text-dark dark:text-pl-brand">SYSTEM</span>
                                <div className="h-10 w-48 bg-slate-200 dark:bg-white/5 rounded-sm"></div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            <div className="bg-gradient-to-t from-pl-bg-light via-pl-bg-light to-transparent dark:from-pl-bg dark:via-pl-bg dark:to-transparent pt-10 pb-6 px-4 sm:px-6 z-10 sticky bottom-0">
                <div className="max-w-4xl mx-auto">
                    {!wsConnected && (
                        <div className="mb-2 text-center text-xs text-amber-600 dark:text-amber-400">
                            <span className="material-symbols-outlined text-[14px] align-middle">warning</span> Reconnecting to server...
                        </div>
                    )}
                    <InputArea
                        onSendMessage={sendMessage}
                        input={input}
                        setInput={setInput}
                        isLoading={isLoading}
                        mode={mode}
                        setMode={setMode}
                        sendVoiceMessage={sendVoiceMessage}
                        isVoiceMode={isVoiceMode}
                        setIsVoiceMode={setIsVoiceMode}
                    />
                </div>
            </div>
        </main>
    );
}
