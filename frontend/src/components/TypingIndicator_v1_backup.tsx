'use client';

import React from 'react';

export default function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="glass-effect px-4 py-3 rounded-2xl">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-primary rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-primary rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-primary rounded-full typing-dot"></div>
        </div>
      </div>
    </div>
  );
}
