'use client';

import React, { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface InputBoxProps {
  onSubmit: (query: string) => void;
  isDisabled: boolean;
  placeholder?: string;
}

export default function InputBox({
  onSubmit,
  isDisabled,
  placeholder = 'Type your question...',
}: InputBoxProps) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmedQuery = query.trim();
    if (trimmedQuery && !isDisabled) {
      onSubmit(trimmedQuery);
      setQuery('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(e.target.value);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  return (
    <div className="border-t border-[#1762C7]/20 bg-white/50 backdrop-blur-xl p-4">
      <div className="max-w-4xl mx-auto flex items-end gap-3">
        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isDisabled}
            rows={1}
            className="w-full px-4 py-3 bg-white border border-[#1762C7]/30 rounded-xl
                     text-gray-900 placeholder:text-gray-400
                     focus:outline-none focus:border-[#1762C7]/50 focus:ring-2 focus:ring-[#1762C7]/20
                     resize-none transition-all duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed
                     custom-scrollbar shadow-sm"
            style={{ maxHeight: '150px' }}
          />
        </div>

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={isDisabled || !query.trim()}
          className="px-4 py-3 disabled:bg-gray-200 disabled:text-gray-500
                   text-white rounded-xl transition-all duration-200
                   disabled:cursor-not-allowed flex items-center gap-2 font-medium
                   shadow-lg hover:shadow-xl hover:-translate-y-0.5"
          style={!isDisabled && query.trim() ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
          title="Send message (Enter)"
        >
          {isDisabled ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <Send size={20} />
          )}
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>

      {/* Hint */}
      <div className="max-w-4xl mx-auto mt-2">
        <p className="text-xs text-gray-500 text-center">
          Press <kbd className="px-1 py-0.5 bg-white border border-[#1762C7]/20 rounded text-[10px] text-gray-700">Enter</kbd> to
          send, <kbd className="px-1 py-0.5 bg-white border border-[#1762C7]/20 rounded text-[10px] text-gray-700">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
