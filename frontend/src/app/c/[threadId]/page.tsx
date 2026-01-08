"use client";

import ChatInterface from '@/components/chat/ChatInterface';
import { use } from 'react';

export default function ThreadPage({ params }: { params: Promise<{ threadId: string }> | { threadId: string } }) {
    // Handle both sync and async params for Next.js compatibility
    const resolvedParams = params instanceof Promise ? use(params) : params;
    return <ChatInterface threadId={resolvedParams.threadId} />;
}
