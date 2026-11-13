import React, { useEffect, useState, useRef } from 'react';
import gsap from 'gsap';

export const RadialCursor: React.FC = () => {
  const [isHovered, setIsHovered] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const ringRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only enable on desktop pointer devices
    if (window.matchMedia('(pointer: coarse)').matches) return;

    const ring = ringRef.current;
    const dot = dotRef.current;
    if (!ring || !dot) return;

    // GSAP quickTo provides ultra-smooth 120fps hardware-accelerated follower physics
    const setRingX = gsap.quickTo(ring, 'x', { duration: 0.35, ease: 'power2.out' });
    const setRingY = gsap.quickTo(ring, 'y', { duration: 0.35, ease: 'power2.out' });
    const setDotX = gsap.quickTo(dot, 'x', { duration: 0.08, ease: 'none' });
    const setDotY = gsap.quickTo(dot, 'y', { duration: 0.08, ease: 'none' });

    const handleMouseMove = (e: MouseEvent) => {
      if (!isVisible) {
        setIsVisible(true);
        gsap.to([ring, dot], { opacity: 1, duration: 0.2 });
      }
      setRingX(e.clientX);
      setRingY(e.clientY);
      setDotX(e.clientX);
      setDotY(e.clientY);

      // Check if hovering interactive target
      const target = e.target as HTMLElement | null;
      const isInteractive = Boolean(
        target?.closest('button') ||
          target?.closest('a') ||
          target?.closest('input') ||
          target?.closest('textarea') ||
          target?.closest('select') ||
          target?.closest('[role="button"]') ||
          target?.classList.contains('cursor-pointer')
      );
      setIsHovered(isInteractive);
    };

    const handleMouseLeave = () => {
      gsap.to([ring, dot], { opacity: 0, duration: 0.2 });
    };

    const handleMouseEnter = () => {
      gsap.to([ring, dot], { opacity: 1, duration: 0.2 });
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
    };
  }, [isVisible]);

  // GSAP animation on hover state changes
  useEffect(() => {
    if (!ringRef.current || !dotRef.current) return;
    if (isHovered) {
      gsap.to(ringRef.current, {
        scale: 1.5,
        borderColor: '#FFC20E',
        backgroundColor: 'rgba(255, 194, 14, 0.18)',
        duration: 0.25,
        ease: 'back.out(1.7)',
      });
      gsap.to(dotRef.current, {
        scale: 0.75,
        backgroundColor: '#FFC20E',
        duration: 0.2,
      });
    } else {
      gsap.to(ringRef.current, {
        scale: 1,
        borderColor: 'rgba(255, 194, 14, 0.35)',
        backgroundColor: 'rgba(255, 194, 14, 0.04)',
        duration: 0.25,
        ease: 'power2.out',
      });
      gsap.to(dotRef.current, {
        scale: 1,
        backgroundColor: '#FFC20E',
        duration: 0.2,
      });
    }
  }, [isHovered]);

  return (
    <div className="pointer-events-none fixed inset-0 z-[9999] overflow-hidden">
      {/* Outer Radial Ring / Halo powered by GSAP */}
      <div
        ref={ringRef}
        style={{ opacity: 0 }}
        className="fixed top-0 left-0 -translate-x-1/2 -translate-y-1/2 rounded-full border border-amber-500/40 bg-[#FFC20E]/10 h-8 w-8 will-change-transform shadow-xs transition-opacity duration-300"
      />
      {/* Center Precise Dot powered by GSAP */}
      <div
        ref={dotRef}
        style={{ opacity: 0 }}
        className="fixed top-0 left-0 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#FFC20E] h-2 w-2 will-change-transform shadow-sm transition-opacity duration-300"
      />
    </div>
  );
};
