import React, { useRef, useEffect, useCallback } from 'react';

/**
 * NeuralBackground — Animated particle system with neural-network aesthetic.
 * 
 * Renders floating nodes connected by translucent lines on a full-screen canvas.
 * Nodes drift slowly and connections form when particles are within a threshold distance.
 * Mouse proximity creates a subtle attraction/glow effect.
 */
export default function NeuralBackground() {
    const canvasRef = useRef(null);
    const mouseRef = useRef({ x: -1000, y: -1000 });
    const animFrameRef = useRef(null);
    const particlesRef = useRef([]);

    const PARTICLE_COUNT = 110;
    const CONNECTION_DISTANCE = 180;
    const MOUSE_RADIUS = 220;
    const SPEED = 0.35;

    const initParticles = useCallback((width, height) => {
        const particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * SPEED,
                vy: (Math.random() - 0.5) * SPEED,
                radius: Math.random() * 1.8 + 0.8,
                opacity: Math.random() * 0.5 + 0.2,
                // Some particles are "accent" colored (teal)
                accent: Math.random() < 0.15,
            });
        }
        return particles;
    }, []);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let width = window.innerWidth;
        let height = window.innerHeight;

        const resize = () => {
            width = window.innerWidth;
            height = window.innerHeight;
            canvas.width = width * window.devicePixelRatio;
            canvas.height = height * window.devicePixelRatio;
            canvas.style.width = `${width}px`;
            canvas.style.height = `${height}px`;
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        };
        resize();

        particlesRef.current = initParticles(width, height);

        const handleMouseMove = (e) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        };

        const handleMouseLeave = () => {
            mouseRef.current = { x: -1000, y: -1000 };
        };

        window.addEventListener('resize', resize);
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseleave', handleMouseLeave);

        const animate = () => {
            ctx.clearRect(0, 0, width, height);
            const particles = particlesRef.current;
            const mouse = mouseRef.current;

            // Update positions
            for (const p of particles) {
                // Drift
                p.x += p.vx;
                p.y += p.vy;

                // Mouse attraction (subtle)
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MOUSE_RADIUS && dist > 0) {
                    const force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS * 0.008;
                    p.vx += dx / dist * force;
                    p.vy += dy / dist * force;
                }

                // Damping
                p.vx *= 0.999;
                p.vy *= 0.999;

                // Wrap edges
                if (p.x < -10) p.x = width + 10;
                if (p.x > width + 10) p.x = -10;
                if (p.y < -10) p.y = height + 10;
                if (p.y > height + 10) p.y = -10;
            }

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const a = particles[i];
                    const b = particles[j];
                    const dx = a.x - b.x;
                    const dy = a.y - b.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DISTANCE) {
                        const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.15;

                        // Connections near mouse glow brighter
                        const midX = (a.x + b.x) / 2;
                        const midY = (a.y + b.y) / 2;
                        const mouseDist = Math.sqrt(
                            (mouse.x - midX) ** 2 + (mouse.y - midY) ** 2
                        );
                        const mouseBoost = mouseDist < MOUSE_RADIUS
                            ? (1 - mouseDist / MOUSE_RADIUS) * 0.2
                            : 0;

                        const isAccent = a.accent || b.accent;
                        const color = isAccent
                            ? `rgba(45, 212, 191, ${alpha + mouseBoost})`
                            : `rgba(59, 130, 246, ${alpha + mouseBoost})`;

                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y);
                        ctx.lineTo(b.x, b.y);
                        ctx.strokeStyle = color;
                        ctx.lineWidth = 0.6;
                        ctx.stroke();
                    }
                }
            }

            // Draw particles
            for (const p of particles) {
                // Mouse proximity glow
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const mouseGlow = dist < MOUSE_RADIUS
                    ? (1 - dist / MOUSE_RADIUS) * 0.6
                    : 0;

                const baseColor = p.accent
                    ? `rgba(45, 212, 191, ${p.opacity + mouseGlow})`
                    : `rgba(59, 130, 246, ${p.opacity + mouseGlow})`;

                // Outer glow
                if (mouseGlow > 0.1) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.radius * 4, 0, Math.PI * 2);
                    const glowColor = p.accent
                        ? `rgba(45, 212, 191, ${mouseGlow * 0.15})`
                        : `rgba(59, 130, 246, ${mouseGlow * 0.15})`;
                    ctx.fillStyle = glowColor;
                    ctx.fill();
                }

                // Core dot
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = baseColor;
                ctx.fill();
            }

            animFrameRef.current = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            cancelAnimationFrame(animFrameRef.current);
            window.removeEventListener('resize', resize);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, [initParticles]);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 0,
                opacity: 0.9,
            }}
        />
    );
}
