"use client";

import React, { useRef, useEffect } from 'react';

interface InputAreaProps {
    input: string;
    setInput: (value: string) => void;
    onSendMessage: (e: React.FormEvent) => void; // Renamed to match ChatInterface
    sendVoiceMessage: (blob: Blob) => void;
    isLoading: boolean;
    mode: 'simple' | 'turbo';
    setMode: (mode: 'simple' | 'turbo') => void;
    isVoiceMode?: boolean;
    setIsVoiceMode?: (val: boolean) => void;
    classNames?: string; // Optional styling overrides
}

export default function InputArea({ input, setInput, onSendMessage, sendVoiceMessage, isLoading, mode, setMode, isVoiceMode, setIsVoiceMode }: InputAreaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [isRecording, setIsRecording] = React.useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    // VAD Refs
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const silenceStartRef = useRef<number | null>(null);
    const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const animationFrameRef = useRef<number | null>(null);
    const isSpeakingRef = useRef<boolean>(false);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Detect supported mime type
            const mimeType = MediaRecorder.isTypeSupported('audio/webm')
                ? 'audio/webm'
                : MediaRecorder.isTypeSupported('audio/ogg')
                    ? 'audio/ogg'
                    : '';

            // Use better audio constraints for higher quality
            try {
                const audioTracks = stream.getAudioTracks();
                if (audioTracks.length > 0) {
                    const constraints = {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 44100, // Higher sample rate for better quality
                    };
                    await audioTracks[0].applyConstraints(constraints);
                }
            } catch (err) {
                console.warn("Could not apply audio constraints:", err);
                // Continue anyway - browser will use defaults
            }

            const options = mimeType ? { mimeType, audioBitsPerSecond: 128000 } : { audioBitsPerSecond: 128000 };
            const mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = () => {
                const finalType = mediaRecorder.mimeType || 'audio/webm';
                if (chunksRef.current.length === 0) {
                    console.warn("No audio data recorded.");
                    setIsRecording(false);
                    return;
                }
                const audioBlob = new Blob(chunksRef.current, { type: finalType });
                console.log(`Sending voice message: ${audioBlob.size} bytes, type: ${finalType}`);
                if (audioBlob.size > 500) { // Increased minimum size threshold
                    sendVoiceMessage(audioBlob);
                } else {
                    console.warn("Audio blob too small, likely silent/empty.");
                    setIsRecording(false);
                }
                stream.getTracks().forEach(track => track.stop());
            };

            // Capture data every 100ms for better chunking
            mediaRecorder.start(100);
            setIsRecording(true);

            // --- VAD: Silence Detection ---
            const AudioContextClass = (window.AudioContext || (window as any).webkitAudioContext);
            const audioContext = new AudioContextClass();
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
            audioContextRef.current = audioContext;
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 512; // Small FFT for responsiveness
            analyser.smoothingTimeConstant = 0.1;
            analyserRef.current = analyser;

            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);

            const checkSilence = () => {
                if (!analyserRef.current) return;

                const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
                analyserRef.current.getByteFrequencyData(dataArray);

                // Calculate volume (RMS-like)
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    sum += dataArray[i];
                }
                const average = sum / dataArray.length;

                // Thresholds (adjusted for better detection):
                // volume > 15: Speaking (increased threshold)
                // volume < 8: Silence (increased threshold to avoid false positives)

                if (average > 15) {
                    // Speech detected
                    silenceStartRef.current = null;
                    isSpeakingRef.current = true;
                } else if (average < 8) {
                    // Silence detected
                    if (isSpeakingRef.current) {
                        // Only count silence IF they have started speaking first
                        if (silenceStartRef.current === null) {
                            silenceStartRef.current = Date.now();
                        } else {
                            const silenceDuration = Date.now() - silenceStartRef.current;
                            // Increased silence duration to 3 seconds for better capture
                            if (silenceDuration > 3000) { // 3.0s of silence
                                console.log("VAD: Silence limit reached, stopping recording.");
                                stopRecordingRef.current?.(); // Auto-stop
                                return; // Stop loop
                            }
                        }
                    }
                }

                animationFrameRef.current = requestAnimationFrame(checkSilence);
            };

            // Reset state
            silenceStartRef.current = null;
            isSpeakingRef.current = false;
            checkSilence();
            // ------------------------------

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Could not access microphone.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            setIsRecording(false);

            // Cleanup VAD
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            if (audioContextRef.current) audioContextRef.current.close();
            audioContextRef.current = null;
            analyserRef.current = null;
        }
    };

    // Ref to allow internal calling
    const stopRecordingRef = useRef<() => void>(null);
    useEffect(() => {
        stopRecordingRef.current = stopRecording;
    });

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSendMessage(e as unknown as React.FormEvent);
        }
    };

    return (
        <div className="w-full bg-transparent pt-4 pb-6 px-4 sm:px-6 z-20">
            <div className="max-w-4xl mx-auto">
                <div className="relative flex flex-col bg-white dark:bg-pl-panel rounded-md border border-slate-300 dark:border-pl-border shadow-tech-lg dark:shadow-[0_0_40px_-10px_rgba(0,0,0,0.7)] transition-all overflow-hidden group">
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-transparent border-none !outline-none !shadow-none !ring-0 focus:ring-0 focus:outline-none focus:border-none focus-visible:ring-0 focus-visible:outline-none text-pl-text-dark dark:text-pl-text-primary placeholder:text-slate-400 dark:placeholder:text-zinc-600 resize-none py-6 px-6 min-h-[120px] max-h-[400px] text-base leading-relaxed custom-scrollbar font-mono sm:font-display tracking-wide"
                        placeholder="Enter command or query..."
                        rows={1}
                        spellCheck={false}
                        disabled={isLoading}
                    ></textarea>
                    <div className="flex items-center justify-between px-2 pb-2">
                        <div className="flex items-center gap-1">
                            <button
                                type="button"
                                className="flex items-center justify-center size-8 rounded text-pl-text-med dark:text-pl-text-secondary hover:text-pl-brand dark:hover:text-pl-text-primary hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
                                title="Upload Data"
                            >
                                <span className="material-symbols-outlined text-[20px]">add</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setMode(mode === 'simple' ? 'turbo' : 'simple')}
                                className={`flex items-center gap-2 px-2 py-1 rounded transition-colors border ${mode === 'turbo'
                                    ? 'bg-blue-50 dark:bg-pl-brand/10 text-pl-brand border-blue-200 dark:border-pl-brand/20'
                                    : 'text-pl-text-med dark:text-pl-text-secondary hover:bg-slate-100 dark:hover:bg-white/5 border-transparent hover:border-slate-200 dark:hover:border-white/10'
                                    } group/btn`}
                                title={mode === 'turbo' ? 'Disable Reasoning' : 'Enable Reasoning'}
                            >
                                <span className="material-symbols-outlined text-[16px]">psychology</span>
                                <span className="text-xs font-medium">Reasoning</span>
                            </button>
                            <button
                                type="button"
                                className="flex items-center gap-2 px-2 py-1 rounded text-pl-text-med dark:text-pl-text-secondary hover:bg-slate-100 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-slate-200 dark:hover:border-white/10 group/btn"
                            >
                                <span className="material-symbols-outlined text-[16px]">travel_explore</span>
                                <span className="text-xs font-medium">Search</span>
                            </button>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={isRecording ? stopRecording : startRecording}
                                className={`flex items-center justify-center size-8 rounded transition-all ${isRecording
                                    ? 'bg-red-500 text-white animate-pulse shadow-md'
                                    : 'text-pl-text-med dark:text-pl-text-secondary hover:text-pl-text-dark dark:hover:text-pl-text-primary hover:bg-slate-100 dark:hover:bg-white/5'
                                    }`}
                                title={isRecording ? "Stop recording" : "Start voice chat"}
                                disabled={isLoading}
                            >
                                <span className="material-symbols-outlined text-[20px]">
                                    {isRecording ? 'stop' : 'mic'}
                                </span>
                            </button>
                            <button
                                onClick={onSendMessage}
                                disabled={!input.trim() || isLoading}
                                className="flex items-center justify-center size-8 rounded bg-pl-brand dark:bg-pl-brand text-white hover:bg-pl-brand-hover dark:hover:bg-blue-600 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
