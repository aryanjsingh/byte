"use client";

import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface InputAreaProps {
    input: string;
    setInput: (value: string) => void;
    onSendMessage: (e: React.FormEvent) => void;
    sendVoiceMessage: (blob: Blob) => void;
    isLoading: boolean;
    mode: 'simple' | 'turbo';
    setMode: (mode: 'simple' | 'turbo') => void;
    isVoiceMode?: boolean;
    setIsVoiceMode?: (val: boolean) => void;
    selectedImage?: string | null;
    setSelectedImage?: (image: string | null) => void;
    imageMimeType?: string | null;
    setImageMimeType?: (type: string | null) => void;
}

export default function InputArea({
    input,
    setInput,
    onSendMessage,
    sendVoiceMessage,
    isLoading,
    mode,
    setMode,
    selectedImage,
    setSelectedImage,
    imageMimeType,
    setImageMimeType
}: InputAreaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isRecording, setIsRecording] = React.useState(false);
    const [isFocused, setIsFocused] = React.useState(false);
    const [isDragging, setIsDragging] = React.useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const silenceStartRef = useRef<number | null>(null);
    const animationFrameRef = useRef<number | null>(null);
    const isSpeakingRef = useRef<boolean>(false);
    const stopRecordingRef = useRef<() => void>(null);

    // Handle image file
    const handleImageFile = (file: File) => {
        if (file && file.type.startsWith('image/') && setSelectedImage && setImageMimeType) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result as string;
                // Remove data:image/xxx;base64, prefix
                const base64Data = base64.split(',')[1];
                setSelectedImage(base64Data);
                setImageMimeType(file.type);
            };
            reader.readAsDataURL(file);
        }
    };

    // Drag and drop handlers
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
            const hasImage = Array.from(e.dataTransfer.items).some(
                item => item.type.startsWith('image/')
            );
            if (hasImage) {
                setIsDragging(true);
            }
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        // Only set dragging to false if we're leaving the main container
        if (e.currentTarget === e.target) {
            setIsDragging(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            const imageFile = Array.from(files).find(file => file.type.startsWith('image/'));
            if (imageFile) {
                handleImageFile(imageFile);
            }
        }
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
            const options = mimeType ? { mimeType, audioBitsPerSecond: 128000 } : { audioBitsPerSecond: 128000 };
            const mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const finalType = mediaRecorder.mimeType || 'audio/webm';
                if (chunksRef.current.length === 0) {
                    setIsRecording(false);
                    return;
                }
                const audioBlob = new Blob(chunksRef.current, { type: finalType });
                if (audioBlob.size > 500) {
                    sendVoiceMessage(audioBlob);
                }
                stream.getTracks().forEach(track => track.stop());
                setIsRecording(false);
            };

            mediaRecorder.start(100);
            setIsRecording(true);

            const AudioContextClass = (window.AudioContext || (window as any).webkitAudioContext);
            const audioContext = new AudioContextClass();
            if (audioContext.state === 'suspended') await audioContext.resume();
            audioContextRef.current = audioContext;
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            analyser.smoothingTimeConstant = 0.1;
            analyserRef.current = analyser;

            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);

            const checkSilence = () => {
                if (!analyserRef.current) return;
                const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
                analyserRef.current.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                const average = sum / dataArray.length;

                if (average > 15) {
                    silenceStartRef.current = null;
                    isSpeakingRef.current = true;
                } else if (average < 8 && isSpeakingRef.current) {
                    if (silenceStartRef.current === null) {
                        silenceStartRef.current = Date.now();
                    } else if (Date.now() - silenceStartRef.current > 3000) {
                        stopRecordingRef.current?.();
                        return;
                    }
                }
                animationFrameRef.current = requestAnimationFrame(checkSilence);
            };

            silenceStartRef.current = null;
            isSpeakingRef.current = false;
            checkSilence();
        } catch (err) {
            console.error("Error accessing microphone:", err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            if (audioContextRef.current) audioContextRef.current.close();
            audioContextRef.current = null;
            analyserRef.current = null;
        }
    };

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
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="w-full"
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <div className={`relative rounded-2xl transition-all duration-300 ${
                isDragging
                    ? 'glass-input shadow-2xl shadow-blue-500/30 ring-2 ring-blue-500/50'
                    : isFocused
                        ? 'glass-input shadow-2xl shadow-blue-500/10'
                        : 'glass-card'
                }`}>
                {/* Drag Overlay */}
                <AnimatePresence>
                    {isDragging && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 rounded-2xl bg-blue-500/10 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none"
                        >
                            <div className="text-center">
                                <motion.div
                                    animate={{ scale: [1, 1.1, 1] }}
                                    transition={{ duration: 1, repeat: Infinity }}
                                    className="size-16 mx-auto mb-3 rounded-full bg-blue-500/20 flex items-center justify-center"
                                >
                                    <span className="material-symbols-outlined text-4xl text-blue-400">image</span>
                                </motion.div>
                                <p className="text-blue-400 font-medium">Drop image here</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Animated Border Gradient */}
                <AnimatePresence>
                    {(isFocused || isDragging) && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 rounded-2xl p-[1px] pointer-events-none"
                        >
                            <div className={`absolute inset-0 rounded-2xl blur-[2px] ${
                                isDragging
                                    ? 'bg-gradient-to-r from-blue-500/50 via-cyan-500/50 to-blue-500/50'
                                    : 'bg-gradient-to-r from-blue-500/30 via-purple-500/30 to-pink-500/20'
                            }`} />
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="relative">
                    {/* Image Preview - Enhanced Thumbnail */}
                    <AnimatePresence>
                        {selectedImage && (
                            <motion.div
                                initial={{ opacity: 0, y: -10, height: 0 }}
                                animate={{ opacity: 1, y: 0, height: 'auto' }}
                                exit={{ opacity: 0, y: -10, height: 0 }}
                                className="px-4 pt-4 pb-2"
                            >
                                <div className="flex items-start gap-3 p-2 rounded-xl bg-white/5 border border-white/10">
                                    {/* Thumbnail */}
                                    <div className="relative group">
                                        <img
                                            src={`data:${imageMimeType};base64,${selectedImage}`}
                                            alt="Preview"
                                            className="h-16 w-16 object-cover rounded-lg border border-white/20 shadow-lg"
                                        />
                                        {/* Hover overlay */}
                                        <div className="absolute inset-0 rounded-lg bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <span className="material-symbols-outlined text-white text-[20px]">zoom_in</span>
                                        </div>
                                    </div>
                                    
                                    {/* Info */}
                                    <div className="flex-1 min-w-0 py-1">
                                        <div className="flex items-center gap-2">
                                            <span className="material-symbols-outlined text-blue-400 text-[16px]">image</span>
                                            <span className="text-sm text-white/80 font-medium">Image attached</span>
                                        </div>
                                        <p className="text-xs text-white/40 mt-1 truncate">
                                            {imageMimeType?.split('/')[1]?.toUpperCase() || 'Image'} • Ready to send
                                        </p>
                                    </div>
                                    
                                    {/* Remove button */}
                                    <motion.button
                                        whileHover={{ scale: 1.1 }}
                                        whileTap={{ scale: 0.9 }}
                                        onClick={() => {
                                            setSelectedImage?.(null);
                                            setImageMimeType?.(null);
                                        }}
                                        className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-white/40 hover:text-red-400 transition-all"
                                        title="Remove image"
                                    >
                                        <span className="material-symbols-outlined text-[18px]">close</span>
                                    </motion.button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        className="w-full bg-transparent border-none outline-none text-white placeholder:text-white/30 resize-none py-5 px-5 min-h-[60px] max-h-[200px] text-base leading-relaxed"
                        placeholder="Ask me anything..."
                        rows={1}
                        spellCheck={false}
                        disabled={isLoading}
                    />

                    {/* Bottom Toolbar */}
                    <div className="flex items-center justify-between px-2 sm:px-3 pb-3">
                        <div className="flex items-center gap-0.5 sm:gap-1">
                            {/* Image Upload Button */}
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                className="hidden"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                        handleImageFile(file);
                                    }
                                }}
                            />
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className={`flex items-center justify-center size-9 rounded-xl transition-all ${selectedImage
                                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                                    }`}
                                title="Upload image"
                            >
                                <span className="material-symbols-outlined text-[20px]">image</span>
                            </motion.button>

                            {/* Reasoning Toggle */}
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                type="button"
                                onClick={() => setMode(mode === 'simple' ? 'turbo' : 'simple')}
                                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 rounded-xl transition-all ${mode === 'turbo'
                                    ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30'
                                    : 'text-white/40 hover:text-white/70 hover:bg-white/5 border border-transparent'
                                    }`}
                                title={mode === 'turbo' ? 'Disable Reasoning' : 'Enable Reasoning'}
                            >
                                <span className="material-symbols-outlined text-[18px]">psychology</span>
                                <span className="text-xs font-medium hidden sm:inline">Reasoning</span>
                                {mode === 'turbo' && (
                                    <motion.span
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="size-1.5 rounded-full bg-blue-400"
                                    />
                                )}
                            </motion.button>

                            {/* Web Search */}
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                type="button"
                                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/5 transition-all border border-transparent"
                            >
                                <span className="material-symbols-outlined text-[18px]">travel_explore</span>
                                <span className="text-xs font-medium hidden sm:inline">Search</span>
                            </motion.button>
                        </div>

                        <div className="flex items-center gap-2">
                            {/* Voice Button */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                type="button"
                                onClick={isRecording ? stopRecording : startRecording}
                                disabled={isLoading}
                                className={`relative flex items-center justify-center size-10 rounded-xl transition-all ${isRecording
                                    ? 'bg-red-500 text-white shadow-lg shadow-red-500/30'
                                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                                    }`}
                                title={isRecording ? "Stop recording" : "Voice input"}
                            >
                                {isRecording && (
                                    <motion.div
                                        animate={{ scale: [1, 1.3, 1] }}
                                        transition={{ duration: 1, repeat: Infinity }}
                                        className="absolute inset-0 rounded-xl bg-red-500/30"
                                    />
                                )}
                                <span className="material-symbols-outlined text-[20px] relative z-10">
                                    {isRecording ? 'stop' : 'mic'}
                                </span>
                            </motion.button>

                            {/* Send Button */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onSendMessage}
                                disabled={(!input.trim() && !selectedImage) || isLoading}
                                className={`flex items-center justify-center size-10 rounded-xl transition-all ${(input.trim() || selectedImage) && !isLoading
                                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50'
                                    : 'bg-white/5 text-white/20 cursor-not-allowed'
                                    }`}
                            >
                                {isLoading ? (
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                        className="size-5 border-2 border-white/30 border-t-white rounded-full"
                                    />
                                ) : (
                                    <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
                                )}
                            </motion.button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Keyboard Hint - Hidden on mobile */}
            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="hidden sm:block text-center text-white/20 text-xs mt-3"
            >
                Press <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono text-[10px]">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono text-[10px]">Shift + Enter</kbd> for new line
            </motion.p>
        </motion.div>
    );
}
