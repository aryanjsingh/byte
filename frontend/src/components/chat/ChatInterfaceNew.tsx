"use client";

import { useState } from 'react';
import { useChat } from '@ai-sdk/react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import {
    Conversation,
    ConversationContent,
    ConversationScrollButton
} from '@/components/ai-elements/conversation';
import {
    Message,
    MessageContent,
    MessageResponse,
    MessageActions,
    MessageAction,
} from '@/components/ai-elements/message';
import {
    PromptInput,
    PromptInputActionAddAttachments,
    PromptInputActionMenu,
    PromptInputActionMenuContent,
    PromptInputActionMenuTrigger,
    PromptInputAttachment,
    PromptInputAttachments,
    PromptInputBody,
    PromptInputButton,
    PromptInputHeader,
    type PromptInputMessage,
    PromptInputSelect,
    PromptInputSelectContent,
    PromptInputSelectItem,
    PromptInputSelectTrigger,
    PromptInputSelectValue,
    PromptInputSubmit,
    PromptInputTextarea,
    PromptInputFooter,
    PromptInputTools,
} from '@/components/ai-elements/prompt-input';
import {
    Reasoning,
    ReasoningContent,
    ReasoningTrigger,
} from '@/components/ai-elements/reasoning';
import {
    Tool,
    ToolHeader,
    ToolInput,
    ToolOutput,
} from '@/components/ai-elements/tool';
import { Loader } from '@/components/ai-elements/loader';
import { CopyIcon, RefreshCcwIcon, BoltIcon } from 'lucide-react';
import Header from '@/components/layout/Header';

interface ChatInterfaceProps {
    threadId?: string;
}

export default function ChatInterface({ threadId }: ChatInterfaceProps) {
    const { data: session, status: authStatus } = useSession();
    const router = useRouter();
    const [input, setInput] = useState('');
    const [mode, setMode] = useState<'simple' | 'turbo'>('simple');
    const [currentThreadId, setCurrentThreadId] = useState(threadId || 'new');

    const { messages, sendMessage, status } = useChat({
        transport: {
            // @ts-ignore - AI SDK v6 transport options
            api: '/api/chat',
            headers: {
                Authorization: `Bearer ${(session as any)?.accessToken}`
            },
            body: {
                threadId: currentThreadId,
                mode: mode
            }
        }
    });

    const handleSubmit = (message: PromptInputMessage) => {
        const hasText = Boolean(message.text);
        const hasAttachments = Boolean(message.files?.length);

        if (!(hasText || hasAttachments)) {
            return;
        }

        sendMessage({
            text: message.text || 'Sent with attachments',
            files: message.files
        });

        setInput('');
    };

    if (authStatus === 'loading') {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader />
            </div>
        );
    }

    if (authStatus === 'unauthenticated') {
        router.push('/auth/signin');
        return null;
    }

    return (
        <main className="flex-1 flex flex-col relative min-w-0 bg-gradient-to-br from-[#0c0f13] via-[#11161d] to-[#0c0f13] h-screen">
            <Header />

            <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-6">
                <Conversation className="flex-1 glass-subtle rounded-xl overflow-hidden">
                    <ConversationContent className="p-4">
                        {messages.length === 0 ? (
                            <div className="flex gap-4 animate-fade-in mt-10">
                                <div className="size-8 shrink-0 rounded-lg glass-strong flex items-center justify-center mt-0.5 glow-brand">
                                    <span className="material-symbols-outlined text-[18px] text-blue-400">smart_toy</span>
                                </div>
                                <div className="flex flex-col gap-2 max-w-[90%] sm:max-w-[85%]">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-blue-400">BYTE</span>
                                    </div>
                                    <div className="glass-strong p-4 rounded-lg border border-blue-500/20">
                                        <p className="text-slate-200 text-sm leading-6">
                                            System initialized. I am ready to help you with cybersecurity questions, threat analysis, and general assistance. How can I help you today?
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            messages.map((message) => (
                                <div key={message.id}>
                                    {message.parts.map((part, i) => {
                                        switch (part.type) {
                                            case 'text':
                                                return (
                                                    <Message
                                                        key={`${message.id}-${i}`}
                                                        from={message.role}
                                                        className={message.role === 'user' ? 'message-glass-user' : 'message-glass-assistant'}
                                                    >
                                                        <MessageContent className="rounded-lg">
                                                            <MessageResponse className="text-slate-100">{part.text}</MessageResponse>
                                                        </MessageContent>
                                                        {message.role === 'assistant' && i === message.parts.length - 1 && (
                                                            <MessageActions>
                                                                <MessageAction
                                                                    onClick={() => navigator.clipboard.writeText(part.text)}
                                                                    label="Copy"
                                                                    className="hover:glow-blue transition-all"
                                                                >
                                                                    <CopyIcon className="size-3" />
                                                                </MessageAction>
                                                            </MessageActions>
                                                        )}
                                                    </Message>
                                                );

                                            case 'reasoning':
                                                return (
                                                    <Reasoning
                                                        key={`${message.id}-${i}`}
                                                        className="w-full mb-4 glass-subtle rounded-lg border-gradient"
                                                        isStreaming={
                                                            status === 'streaming' &&
                                                            i === message.parts.length - 1 &&
                                                            message.id === messages.at(-1)?.id
                                                        }
                                                    >
                                                        <ReasoningTrigger />
                                                        <ReasoningContent className="text-slate-300">{part.text}</ReasoningContent>
                                                    </Reasoning>
                                                );

                                            default:
                                                // Check if it's a tool-related part
                                                if (part.type.startsWith('tool-')) {
                                                    const toolPart = part as any;
                                                    return (
                                                        <Tool key={`${message.id}-${i}`} className="glass-subtle border-blue-500/20">
                                                            <ToolHeader
                                                                title={toolPart.toolCallId || 'Tool'}
                                                                type={toolPart.type}
                                                                state={toolPart.state}
                                                            />
                                                            {toolPart.input && <ToolInput input={toolPart.input} />}
                                                            {(toolPart.output || toolPart.errorText) && (
                                                                <ToolOutput
                                                                    output={toolPart.output}
                                                                    errorText={toolPart.errorText}
                                                                />
                                                            )}
                                                        </Tool>
                                                    );
                                                }
                                                return null;
                                        }
                                    })}
                                </div>
                            ))
                        )}

                        {status === 'submitted' && <Loader />}
                    </ConversationContent>
                    <ConversationScrollButton />
                </Conversation>

                <PromptInput
                    onSubmit={handleSubmit}
                    className="mt-4 input-glass rounded-xl animate-glow"
                    globalDrop
                    multiple
                >
                    <PromptInputHeader className="px-4 pt-4">
                        <PromptInputAttachments>
                            {(attachment) => <PromptInputAttachment data={attachment} className="glass-strong" />}
                        </PromptInputAttachments>
                    </PromptInputHeader>

                    <PromptInputBody className="px-4">
                        <PromptInputTextarea
                            onChange={(e) => setInput(e.target.value)}
                            value={input}
                            placeholder="Ask BYTE anything..."
                            className="bg-transparent text-slate-100 placeholder:text-slate-500 border-none focus:ring-0 resize-none"
                        />
                    </PromptInputBody>

                    <PromptInputFooter className="px-4 pb-4 pt-2 border-t border-white/10">
                        <PromptInputTools>
                            <PromptInputActionMenu>
                                <PromptInputActionMenuTrigger className="glass hover:glass-strong transition-all" />
                                <PromptInputActionMenuContent className="glass-strong border-blue-500/20">
                                    <PromptInputActionAddAttachments />
                                </PromptInputActionMenuContent>
                            </PromptInputActionMenu>

                            <PromptInputSelect
                                onValueChange={(value) => setMode(value as 'simple' | 'turbo')}
                                value={mode}
                            >
                                <PromptInputSelectTrigger className="glass hover:glass-strong transition-all border-blue-500/20">
                                    <PromptInputSelectValue />
                                </PromptInputSelectTrigger>
                                <PromptInputSelectContent className="glass-strong border-blue-500/20">
                                    <PromptInputSelectItem value="simple" className="hover:glass transition-all">
                                        <div className="flex items-center gap-2">
                                            <span className="text-slate-200">Simple Mode</span>
                                        </div>
                                    </PromptInputSelectItem>
                                    <PromptInputSelectItem value="turbo" className="hover:glass transition-all">
                                        <div className="flex items-center gap-2">
                                            <BoltIcon className="size-3 text-blue-400" />
                                            <span className="text-slate-200">Turbo Mode</span>
                                        </div>
                                    </PromptInputSelectItem>
                                </PromptInputSelectContent>
                            </PromptInputSelect>
                        </PromptInputTools>

                        <PromptInputSubmit
                            disabled={!input && status !== 'streaming'}
                            status={status}
                            className="glass-strong hover:glow-blue transition-all border-blue-500/30"
                        />
                    </PromptInputFooter>
                </PromptInput>
            </div>
        </main>
    );
}
