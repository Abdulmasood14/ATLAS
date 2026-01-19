'use client';

import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="px-5 py-4 rounded-2xl bg-white border border-[#1762C7]/20 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Role Badge */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#1762C7]/10">
        <div className="w-6 h-6 rounded-full flex items-center justify-center shadow-lg"
             style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
          <Sparkles className="w-3.5 h-3.5 text-white animate-pulse" strokeWidth={2.5} />
        </div>
        <span className="text-[10px] font-semibold text-[#1762C7] uppercase tracking-wider">AI Assistant</span>
      </div>

      <div className="flex items-center gap-3">
        {/* Animated Dots */}
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 bg-[#1762C7] rounded-full animate-bounce shadow-lg" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
          <div className="w-2 h-2 bg-[#1762C7] rounded-full animate-bounce shadow-lg" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
          <div className="w-2 h-2 bg-[#1762C7] rounded-full animate-bounce shadow-lg" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
        </div>

        <span className="text-xs text-gray-600 animate-pulse">Analyzing documents...</span>
      </div>
    </div>
  );
}
