import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-200/80 bg-white py-6 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-start gap-3 sm:gap-6 text-xs text-slate-500 pr-18 sm:pr-32">
        <p className="flex flex-wrap items-center justify-center sm:justify-start gap-1 text-center sm:text-left">
          <span>Copyright © 42Works Info Solutions Pvt Ltd 2026. All Rights Reserved.</span>
          <a
            href="https://42works.net/privacy-policy/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-slate-700 hover:text-amber-600 underline decoration-slate-300 hover:decoration-amber-500 transition-colors ml-1"
          >
            Privacy Policy
          </a>
        </p>

        <span className="hidden sm:inline text-slate-300">•</span>

        <div className="flex items-center gap-2 text-xs text-slate-600 font-medium">
          <span>AI Poster & Social Dispatch Studio</span>
        </div>
      </div>
    </footer>
  );
};
