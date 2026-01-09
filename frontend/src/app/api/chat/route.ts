import { type UIMessage } from 'ai';
import { NextRequest } from 'next/server';
import WebSocket from 'ws';

export const runtime = 'nodejs';
export const maxDuration = 60;

/**
 * AI SDK Chat API Route
 * 
 * This endpoint adapts the existing WebSocket-based backend to work with
 * AI SDK's useChat hook by creating a REST streaming endpoint.
 */
export async function POST(req: NextRequest) {
    try {
        const { messages, threadId = 'new', mode = 'simple' }: {
            messages: UIMessage[];
            threadId?: string;
            mode?: 'simple' | 'turbo';
        } = await req.json();

        console.log('📥 Received chat request:', {
            messageCount: messages.length,
            threadId,
            mode
        });

        // Get auth token from headers
        const authHeader = req.headers.get('authorization');
        if (!authHeader) {
            return new Response('Unauthorized', { status: 401 });
        }
        const token = authHeader.replace('Bearer ', '');

        // Create WebSocket connection to backend
        const wsUrl = `ws://localhost:8000/ws/chat?token=${token}`;
        const ws = new WebSocket(wsUrl);

        // Create a TransformStream to convert WebSocket messages to AI SDK format
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
            async start(controller) {
                return new Promise<void>((resolve, reject) => {
                    ws.on('open', () => {
                        console.log('✅ WebSocket connected to backend');

                        // Send the last user message to the backend
                        const lastMessage = messages[messages.length - 1];
                        const userMessage = lastMessage.parts
                            .filter(part => part.type === 'text')
                            .map(part => part.text)
                            .join(' ');

                        ws.send(JSON.stringify({
                            message: userMessage,
                            thread_id: threadId,
                            mode: mode
                        }));
                    });

                    ws.on('message', (rawData: WebSocket.Data) => {
                        try {
                            const data = JSON.parse(rawData.toString());
                            console.log('📨 Backend event:', data.type);

                            switch (data.type) {
                                case 'thinking':
                                    // Stream thinking as reasoning parts
                                    const thinkingChunk = `0:{"type":"reasoning","text":${JSON.stringify(data.content)}}\n`;
                                    controller.enqueue(encoder.encode(thinkingChunk));
                                    break;

                                case 'answer':
                                    // Stream answer as text parts
                                    const answerChunk = `0:{"type":"text","text":${JSON.stringify(data.content)}}\n`;
                                    controller.enqueue(encoder.encode(answerChunk));
                                    break;

                                case 'tool_call':
                                    // Stream tool invocation
                                    const toolCallChunk = `0:{"type":"tool-invocation","toolName":${JSON.stringify(data.tool_name)},"args":${JSON.stringify(data.tool_args)},"state":"call"}\n`;
                                    controller.enqueue(encoder.encode(toolCallChunk));
                                    break;

                                case 'tool_result':
                                    // Stream tool result
                                    const toolResultChunk = `0:{"type":"tool-result","toolName":${JSON.stringify(data.tool_name)},"result":${JSON.stringify(String(data.content))}}\n`;
                                    controller.enqueue(encoder.encode(toolResultChunk));
                                    break;

                                case 'done':
                                    console.log('✅ Stream complete');
                                    ws.close();
                                    controller.close();
                                    resolve();
                                    break;

                                case 'error':
                                    console.error('❌ Backend error:', data.error);
                                    ws.close();
                                    controller.error(new Error(data.error));
                                    reject(new Error(data.error));
                                    break;
                            }
                        } catch (err) {
                            console.error('Error processing WebSocket message:', err);
                        }
                    });

                    ws.on('error', (error) => {
                        console.error('❌ WebSocket error:', error);
                        controller.error(error);
                        reject(error);
                    });

                    ws.on('close', () => {
                        console.log('🔌 WebSocket closed');
                        controller.close();
                        resolve();
                    });
                });
            },

            cancel() {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.close();
                }
            }
        });

        return new Response(stream, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
        });

    } catch (error) {
        console.error('API route error:', error);
        return new Response(JSON.stringify({ error: String(error) }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}
