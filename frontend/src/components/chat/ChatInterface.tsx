"use client";

import React, { useState, useRef, useEffect } from 'react';
import Header from '@/components/layout/Header';
import MessageBubble from '@/components/chat/MessageBubble';
import InputArea from '@/components/chat/InputArea';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

interface ToolCallInfo {
    id: string;
    name: string;
    args?: any;
    result?: string;
    status: 'calling' | 'completed' | 'failed';
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    thinking?: string;
    mode?: 'simple' | 'turbo';
    tool_calls?: string[];
    toolInvocations?: ToolCallInfo[];
    isNew?: boolean;
    isStreaming?: boolean;
    imageData?: string;  // Base64 encoded image (user upload)
    imageMimeType?: string;  // e.g., 'image/jpeg'
    images?: Array<{  // Images from image_search tool
        url: string;
        thumbnail?: string;
        title?: string;
    }>;
    generatedImage?: {  // AI-generated image from image_gen tool
        base64: string;
        mimeType: string;
        prompt: string;
    };
}

interface ChatInterfaceProps {
    threadId?: string;
}

const suggestionCards = [
    { icon: 'fact_check', title: 'Analyze News', desc: 'Verify if a news story is real or fake', gradient: 'from-blue-500/10 to-purple-500/10', border: 'border-blue-500/20' },
    { icon: 'language', title: 'Verify URL', desc: 'Check domains for phishing or scams', gradient: 'from-purple-500/10 to-pink-500/10', border: 'border-purple-500/20' },
    { icon: 'security', title: 'Scan Threat', desc: 'Scan IPs or files for security risks', gradient: 'from-amber-500/10 to-orange-500/10', border: 'border-amber-500/20' },
    { icon: 'shield', title: 'Security Tips', desc: 'Get advice on staying safe online', gradient: 'from-green-500/10 to-emerald-500/10', border: 'border-green-500/20' },
];

export default function ChatInterface({ threadId }: ChatInterfaceProps) {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentThreadId, setCurrentThreadId] = useState<string | undefined>(threadId);
    const [mode, setMode] = useState<'simple' | 'turbo'>('simple');
    const [isVoiceMode, setIsVoiceMode] = useState(false);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [imageMimeType, setImageMimeType] = useState<string | null>(null);

    const [ws, setWs] = useState<WebSocket | null>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [thinkingContent, setThinkingContent] = useState("");
    const [streamingContent, setStreamingContent] = useState("");
    const [toolInvocations, setToolInvocations] = useState<ToolCallInfo[]>([]);
    const [isThinking, setIsThinking] = useState(false);
    const [threadTitle, setThreadTitle] = useState<string>("New Chat");
    const [isTransitioning, setIsTransitioning] = useState(false);

    const thinkingRef = useRef("");
    const streamingRef = useRef("");
    const toolInvocationsRef = useRef<ToolCallInfo[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading, streamingContent, thinkingContent, toolInvocations]);

    useEffect(() => {
        if (status === 'authenticated' && session?.user) {
            const token = (session as any).accessToken;
            if (!token) return;

            let reconnectAttempts = 0;
            const maxReconnectAttempts = 5;
            let reconnectTimeout: NodeJS.Timeout | null = null;

            const connectWebSocket = () => {
                const websocket = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);

                websocket.onopen = () => {
                    console.log('✅ WebSocket connected');
                    setWsConnected(true);
                    setWs(websocket);
                    wsRef.current = websocket;
                    reconnectAttempts = 0; // Reset on successful connection
                };

                websocket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);

                        if (data.type === 'thinking') {
                            setIsThinking(true);
                            const newContent = data.content || '';
                            setThinkingContent(prev => prev + newContent);
                            thinkingRef.current += newContent;
                        } else if (data.type === 'answer') {
                            setIsThinking(false);
                            const newContent = data.content || '';
                            setStreamingContent(prev => prev + newContent);
                            streamingRef.current += newContent;
                        } else if (data.type === 'tool_call') {
                            const newTool: ToolCallInfo = {
                                id: data.tool_call_id || Date.now().toString(),
                                name: data.tool_name,
                                args: data.tool_args,
                                status: 'calling'
                            };
                            setToolInvocations(prev => [...prev, newTool]);
                            toolInvocationsRef.current = [...toolInvocationsRef.current, newTool];
                        } else if (data.type === 'tool_result') {
                            console.log('🔧 Tool result received:', data.tool_name, 'content length:', data.content?.length);
                            // Match by tool_name since tool_call_id may not be present
                            setToolInvocations(prev => prev.map(tool =>
                                (data.tool_call_id && tool.id === data.tool_call_id) || tool.name === data.tool_name ?
                                    { ...tool, result: data.content, status: 'completed' } : tool
                            ));
                            toolInvocationsRef.current = toolInvocationsRef.current.map(tool =>
                                (data.tool_call_id && tool.id === data.tool_call_id) || tool.name === data.tool_name ?
                                    { ...tool, result: data.content, status: 'completed' } : tool
                            );
                            console.log('🔧 Updated toolInvocationsRef:', toolInvocationsRef.current);
                        } else if (data.type === 'done') {
                            // Save message if we have any content OR tool invocations
                            const hasContent = streamingRef.current.trim() || thinkingRef.current.trim();
                            const hasTools = toolInvocationsRef.current.length > 0;

                            // Extract images from image_search tool results
                            let images: Array<{ url: string, thumbnail?: string, title?: string }> | undefined;
                            const imageSearchTool = toolInvocationsRef.current.find(t => t.name === 'image_search');
                            if (imageSearchTool && imageSearchTool.result) {
                                try {
                                    const parsedResult = JSON.parse(imageSearchTool.result);
                                    if (parsedResult.type === 'image_results' && parsedResult.images) {
                                        images = parsedResult.images;
                                    }
                                } catch (e) {
                                    console.warn('Failed to parse image_search result:', e);
                                }
                            }

                            // Extract generated image from image_gen tool results
                            let generatedImage: { base64: string, mimeType: string, prompt: string } | undefined;
                            const imageGenTool = toolInvocationsRef.current.find(t => t.name === 'image_gen');
                            console.log('🎨 Looking for image_gen tool:', imageGenTool);
                            if (imageGenTool && imageGenTool.result) {
                                console.log('🎨 image_gen result found, length:', imageGenTool.result.length);
                                console.log('🎨 image_gen result preview:', imageGenTool.result.substring(0, 200));
                                try {
                                    const parsedResult = JSON.parse(imageGenTool.result);
                                    console.log('🎨 Parsed result type:', parsedResult.type);
                                    console.log('🎨 Has image_base64:', !!parsedResult.image_base64);
                                    if (parsedResult.type === 'image_gen_result' && parsedResult.image_base64) {
                                        generatedImage = {
                                            base64: parsedResult.image_base64,
                                            mimeType: parsedResult.mime_type || 'image/png',
                                            prompt: parsedResult.prompt || ''
                                        };
                                        console.log('🎨 generatedImage set successfully, base64 length:', generatedImage.base64.length);
                                    }
                                } catch (e) {
                                    console.warn('Failed to parse image_gen result:', e);
                                }
                            }

                            if (hasContent || hasTools) {
                                const finalMessage: Message = {
                                    role: 'assistant',
                                    content: streamingRef.current,
                                    thinking: thinkingRef.current || undefined,
                                    mode: mode,
                                    tool_calls: data.tool_calls || toolInvocationsRef.current.map(t => t.name),
                                    toolInvocations: hasTools ? [...toolInvocationsRef.current] : undefined,
                                    images: images,
                                    generatedImage: generatedImage,
                                    isNew: true,
                                    isStreaming: false
                                };
                                console.log('📦 Final message toolInvocations:', finalMessage.toolInvocations);
                                console.log('🖼️ Final message images:', finalMessage.images);
                                console.log('🎨 Final message generatedImage:', finalMessage.generatedImage);
                                setMessages(prev => [...prev, finalMessage]);
                                setTimeout(() => {
                                    setMessages(prev => prev.map(msg =>
                                        msg === finalMessage ? { ...msg, isNew: false } : msg
                                    ));
                                }, 2000);
                            }

                            if (!currentThreadId && data.thread_id) {
                                setCurrentThreadId(data.thread_id);
                                setIsTransitioning(true);
                                // Navigate to the new thread
                                router.push(`/c/${data.thread_id}`);
                            }

                            setThinkingContent('');
                            setStreamingContent('');
                            setToolInvocations([]);
                            thinkingRef.current = '';
                            streamingRef.current = '';
                            toolInvocationsRef.current = [];
                            setIsThinking(false);
                            setIsLoading(false);
                        } else if (data.type === 'error') {
                            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.error}` }]);
                            setIsLoading(false);
                            setThinkingContent('');
                            setStreamingContent('');
                            setToolInvocations([]);
                            thinkingRef.current = '';
                            streamingRef.current = '';
                            toolInvocationsRef.current = [];
                            setIsThinking(false);
                        }
                    } catch (e) {
                        console.error('Failed to parse WebSocket message:', e);
                    }
                };

                websocket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    setWsConnected(false);
                };

                websocket.onclose = (event) => {
                    console.log('🔌 WebSocket closed:', event.code, event.reason);
                    setWsConnected(false);
                    setWs(null);
                    wsRef.current = null;

                    // Auto-reconnect with exponential backoff
                    if (reconnectAttempts < maxReconnectAttempts) {
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 16000);
                        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
                        reconnectTimeout = setTimeout(() => {
                            reconnectAttempts++;
                            connectWebSocket();
                        }, delay);
                    } else {
                        console.log('❌ Max reconnection attempts reached');
                    }
                };

                return websocket;
            };

            const ws = connectWebSocket();

            return () => {
                if (reconnectTimeout) clearTimeout(reconnectTimeout);
                ws.close();
            };
        }
    }, [status, session]);

    useEffect(() => {
        if (!threadId) {
            setCurrentThreadId(undefined);
            setMessages([]);
            return;
        }

        if (threadId === currentThreadId && messages.length > 0) return;
        setCurrentThreadId(threadId);

        const loadHistory = async () => {
            if (status === 'authenticated' && session?.user) {
                try {
                    const token = (session as any).accessToken;
                    const response = await fetch(`http://localhost:8000/chat/threads/${threadId}`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        setThreadTitle(data.title || "Active Session");
                        if (Array.isArray(data.messages)) {
                            const historyMessages: Message[] = data.messages.map((log: any) => {
                                // Convert tool_invocations from DB format to frontend format
                                let toolInvocations: ToolCallInfo[] | undefined;
                                let images: Array<{ url: string, thumbnail?: string, title?: string }> | undefined;

                                if (log.tool_invocations && Array.isArray(log.tool_invocations) && log.tool_invocations.length > 0) {
                                    toolInvocations = log.tool_invocations.map((inv: any, idx: number) => ({
                                        id: `${log.id}-${idx}`,
                                        name: inv.name,
                                        args: inv.args,
                                        result: inv.result,
                                        status: inv.status || 'completed'
                                    }));

                                    // Extract images from image_search tool results
                                    const imageSearchInv = log.tool_invocations.find((inv: any) => inv.name === 'image_search');
                                    if (imageSearchInv && imageSearchInv.result) {
                                        try {
                                            const parsed = JSON.parse(imageSearchInv.result);
                                            if (parsed.type === 'image_results' && parsed.images) {
                                                images = parsed.images;
                                            }
                                        } catch (e) {
                                            // JSON parse failed, skip
                                        }
                                    }
                                }

                                // Extract generated image from image_gen tool results
                                let generatedImage: { base64: string, mimeType: string, prompt: string } | undefined;
                                if (log.tool_invocations && Array.isArray(log.tool_invocations)) {
                                    const imageGenInv = log.tool_invocations.find((inv: any) => inv.name === 'image_gen');
                                    if (imageGenInv && imageGenInv.result) {
                                        try {
                                            const parsed = JSON.parse(imageGenInv.result);
                                            if (parsed.type === 'image_gen_result' && parsed.image_base64) {
                                                generatedImage = {
                                                    base64: parsed.image_base64,
                                                    mimeType: parsed.mime_type || 'image/png',
                                                    prompt: parsed.prompt || ''
                                                };
                                            }
                                        } catch (e) {
                                            // JSON parse failed, skip
                                        }
                                    }
                                }

                                return {
                                    role: log.role,
                                    content: log.content,
                                    thinking: log.thinking || undefined,
                                    mode: log.mode,
                                    tool_calls: log.tool_calls,
                                    toolInvocations: toolInvocations,
                                    images: images,
                                    generatedImage: generatedImage
                                };
                            });
                            setMessages(historyMessages);
                        }
                    } else {
                        setMessages([]);
                        setThreadTitle("New Chat");
                    }
                } catch (e) {
                    setMessages([]);
                    setThreadTitle("New Chat");
                }
            }
        };

        loadHistory();
    }, [threadId, currentThreadId, messages.length, status, session]);

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !wsConnected) return;

        // Trigger transition animation when sending first message
        if (!currentThreadId && messages.length === 0) {
            setIsTransitioning(true);
        }

        const userMessage: Message = { role: 'user', content: input, mode: mode };
        setMessages(prev => [...prev, userMessage]);

        const messageToSend = input;
        setInput('');
        setIsLoading(true);
        setThinkingContent('');
        setStreamingContent('');
        setToolInvocations([]);
        thinkingRef.current = '';
        streamingRef.current = '';
        toolInvocationsRef.current = [];

        try {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                    message: messageToSend,
                    thread_id: currentThreadId || 'new',
                    mode: mode,
                    image_data: selectedImage,
                    image_mime_type: imageMimeType
                }));
                // Clear image after sending
                setSelectedImage(null);
                setImageMimeType(null);
            } else {
                throw new Error('WebSocket not connected');
            }
        } catch (error) {
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
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });

            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            if (!data.transcription && !data.response) {
                setIsLoading(false);
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

            if (data.audio) {
                const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
                audio.play();
            }

            if (!currentThreadId && data.thread_id) {
                setCurrentThreadId(data.thread_id);
                window.history.pushState(null, '', `/c/${data.thread_id}`);
            }
        } catch (error) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not process voice message." }]);
        } finally {
            setIsLoading(false);
        }
    };

    if (status === 'loading') {
        return (
            <div className="flex-1 flex items-center justify-center">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="size-8 border-2 border-blue-500 border-t-transparent rounded-full"
                />
            </div>
        );
    }

    const isHero = messages.length === 0 && !currentThreadId && !isTransitioning;

    return (
        <main className="flex-1 flex flex-col relative min-w-0 h-full bg-grid-pattern">
            <Header title={threadTitle} />

            <div className="flex-1 overflow-y-auto px-4 sm:px-6 pb-4 scroll-smooth">
                <div className="max-w-4xl mx-auto flex flex-col gap-6 py-6">
                    <AnimatePresence mode="wait">
                        {isHero ? (
                            <motion.div
                                key="hero"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="flex flex-col items-center justify-center min-h-[60vh] text-center"
                            >
                                {/* Hero Icon */}
                                <motion.div
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
                                    className="relative mb-8"
                                >
                                    <div className="size-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-2xl glow-gradient">
                                        <span className="material-symbols-outlined text-[40px]">auto_awesome</span>
                                    </div>
                                    <motion.div
                                        animate={{ scale: [1, 1.2, 1] }}
                                        transition={{ duration: 2, repeat: Infinity }}
                                        className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-600/30 blur-xl -z-10"
                                    />
                                </motion.div>

                                {/* Hero Text */}
                                <motion.h1
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.2 }}
                                    className="text-3xl sm:text-4xl font-bold text-white mb-3"
                                >
                                    How can I help you today?
                                </motion.h1>
                                <motion.p
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.3 }}
                                    className="text-white/50 text-lg mb-10 max-w-md"
                                >
                                    I'm Byte, your AI assistant. Ask me anything or choose a suggestion below.
                                </motion.p>

                                {/* Suggestion Cards */}
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.4 }}
                                    className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-2xl"
                                >
                                    {suggestionCards.map((card, index) => (
                                        <motion.button
                                            key={card.title}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.5 + index * 0.1 }}
                                            whileHover={{ scale: 1.02, y: -2 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setInput(card.desc)}
                                            className={`p-4 rounded-xl bg-gradient-to-br ${card.gradient} border ${card.border} backdrop-blur-sm text-left group transition-all duration-300 hover:shadow-lg`}
                                        >
                                            <span className="material-symbols-outlined text-[24px] text-white/70 group-hover:text-white mb-2 block transition-colors">
                                                {card.icon}
                                            </span>
                                            <h3 className="text-sm font-semibold text-white/90 group-hover:text-white">{card.title}</h3>
                                            <p className="text-xs text-white/40 mt-1">{card.desc}</p>
                                        </motion.button>
                                    ))}
                                </motion.div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="messages"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="space-y-6"
                            >
                                {messages.map((msg, index) => (
                                    <MessageBubble key={index} message={msg} index={index} />
                                ))}

                                {isLoading && (
                                    <MessageBubble
                                        message={{
                                            role: 'assistant',
                                            content: streamingContent,
                                            thinking: thinkingContent,
                                            mode: mode,
                                            toolInvocations: toolInvocations,
                                            isStreaming: true
                                        }}
                                        index={messages.length}
                                    />
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="sticky bottom-0 z-10 pb-[env(safe-area-inset-bottom)]">
                <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-[#0a0a0f] via-[#0a0a0f]/80 to-transparent pointer-events-none" />
                <div className="relative max-w-4xl mx-auto px-4 sm:px-6 pb-4 sm:pb-6">
                    {!wsConnected && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-3 flex items-center justify-center gap-2 text-amber-400 text-sm"
                        >
                            <span className="material-symbols-outlined text-[16px] animate-pulse">warning</span>
                            Reconnecting to server...
                        </motion.div>
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
                        selectedImage={selectedImage}
                        setSelectedImage={setSelectedImage}
                        imageMimeType={imageMimeType}
                        setImageMimeType={setImageMimeType}
                    />
                </div>
            </div>
        </main>
    );
}
