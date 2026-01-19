'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="px-5 py-4 rounded-2xl bg-gradient-to-br from-[#1a1f35]/80 to-[#0F1729]/80 backdrop-blur-xl border border-cyan-500/10 shadow-lg shadow-cyan-900/20 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Role Badge */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-cyan-500/10">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
          <Sparkles className="w-3.5 h-3.5 text-white animate-pulse" strokeWidth={2.5} />
        </div>
        <span className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider">AI Assistant</span>
      </div>

      <div className="flex items-center gap-3">
        {/* Animated Dots */}
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce shadow-lg shadow-cyan-500/50" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce shadow-lg shadow-cyan-500/50" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce shadow-lg shadow-cyan-500/50" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
        </div>

        <span className="text-xs text-gray-400 animate-pulse">Analyzing documents...</span>
      </div>
    </div>
  );
}
