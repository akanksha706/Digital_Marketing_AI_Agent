import React, { useRef } from 'react';
import gsap from 'gsap';

interface AppreciativePosterProps {
  src: string;
  alt: string;
  className?: string;
  aspectRatio?: string;
  headline?: string;
  children?: React.ReactNode;
  enableIdleFloat?: boolean;
}

export const AppreciativePoster: React.FC<AppreciativePosterProps> = ({
  src,
  alt,
  className = '',
  aspectRatio = 'aspect-square',
  headline,
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  // GSAP 3D Interactive Tilt & Holographic Glare Tracking
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    const glare = glareRef.current;
    if (!card) return;

    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -9; // Max 9 deg
    const rotateY = ((x - centerX) / centerX) * 9;

    gsap.to(card, {
      rotateX,
      rotateY,
      scale: 1.025,
      y: -6,
      transformPerspective: 1000,
      duration: 0.3,
      ease: 'power2.out',
      overwrite: 'auto',
    });

    if (glare) {
      gsap.to(glare, {
        opacity: 0.25,
        x: (x - rect.width / 2) * 1.1,
        y: (y - rect.height / 2) * 1.1,
        duration: 0.2,
        ease: 'none',
      });
    }
  };

  const handleMouseLeave = () => {
    const card = cardRef.current;
    const glare = glareRef.current;
    if (!card) return;

    gsap.to(card, {
      rotateX: 0,
      rotateY: 0,
      scale: 1,
      y: 0,
      duration: 0.6,
      ease: 'elastic.out(1, 0.45)',
    });

    if (glare) {
      gsap.to(glare, {
        opacity: 0,
        duration: 0.4,
      });
    }
  };

  return (
    <div
      ref={containerRef}
      className={`perspective-1000 relative select-none ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        ref={cardRef}
        style={{ transformStyle: 'preserve-3d' }}
        className={`relative w-full overflow-hidden rounded-2xl bg-slate-900 shadow-md transition-shadow duration-300 hover:shadow-xl ${aspectRatio}`}
      >
        {/* Main Poster Visual */}
        <img
          src={src}
          alt={alt}
          className="h-full w-full object-cover select-none pointer-events-none transition-transform duration-500 will-change-transform"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/samples/c0b9f6cf6ff9_final.png';
          }}
        />

        {/* Dynamic Holographic Glare / Light Reflection Overlay */}
        <div
          ref={glareRef}
          style={{ opacity: 0 }}
          className="pointer-events-none absolute inset-0 bg-radial from-white/40 via-white/10 to-transparent w-[200%] h-[200%] -top-1/2 -left-1/2 will-change-transform mix-blend-overlay"
        />

        {/* Slot for overlay actions / inspect controls */}
        {children}
      </div>

      {headline && (
        <p className="mt-2 line-clamp-1 text-center text-xs font-semibold text-slate-700">
          {headline}
        </p>
      )}
    </div>
  );
};
