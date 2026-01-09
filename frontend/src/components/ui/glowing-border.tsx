"use client";

import { cn } from "@/lib/utils";
import React, { useRef, useEffect } from "react";

export const GlowingBorder = ({
    children,
    className,
    containerClassName,
}: {
    children: React.ReactNode;
    className?: string;
    containerClassName?: string;
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (!canvas || !container) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;
        let mouseX = 0;
        let mouseY = 0;

        const handleResize = () => {
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
        };

        const handleMouseMove = (e: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            mouseX = e.clientX - rect.left;
            mouseY = e.clientY - rect.top;
        };

        const draw = () => {
            if (!ctx || !canvas) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Create radial gradient following mouse
            const gradient = ctx.createRadialGradient(
                mouseX,
                mouseY,
                0,
                mouseX,
                mouseY,
                canvas.width / 2
            );

            gradient.addColorStop(0, "rgba(59, 130, 246, 0.5)"); // Blue glow
            gradient.addColorStop(0.5, "rgba(139, 92, 246, 0.3)"); // Purple
            gradient.addColorStop(1, "rgba(59, 130, 246, 0)");

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            animationFrameId = requestAnimationFrame(draw);
        };

        handleResize();
        window.addEventListener("resize", handleResize);
        container.addEventListener("mousemove", handleMouseMove);
        draw();

        return () => {
            window.removeEventListener("resize", handleResize);
            container.removeEventListener("mousemove", handleMouseMove);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <div
            ref={containerRef}
            className={cn("relative overflow-hidden", containerClassName)}
        >
            <canvas
                ref={canvasRef}
                className="pointer-events-none absolute inset-0 z-0"
            />
            <div className={cn("relative z-10", className)}>{children}</div>
        </div>
    );
};
