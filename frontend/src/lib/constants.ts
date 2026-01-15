export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

// Ensure WS URL uses the correct protocol for production if specified as https
export const GET_WS_URL = (token?: string) => {
    let baseUrl = WS_BASE_URL;

    // If we're in the browser, handle WSS automatically if on HTTPS
    if (typeof window !== 'undefined') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        if (!baseUrl.startsWith('ws')) {
            baseUrl = `${protocol}//${baseUrl}`;
        } else if (window.location.protocol === 'https:' && baseUrl.startsWith('ws:')) {
            baseUrl = baseUrl.replace('ws:', 'wss:');
        }
    }

    if (token) {
        return `${baseUrl}/ws/chat?token=${token}`;
    }
    return baseUrl;
};
