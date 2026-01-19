'use client';

import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';
import MessageBubble from './MessageBubble_v2';
import TypingIndicator from './TypingIndicator_v2';
import { Sparkles, MessageSquare } from 'lucide-react';

interface ChatWindowProps {
  messages: ChatMessage[];
  sessionId: string;
  isLoading: boolean;
}

export default function ChatWindow({ messages, sessionId, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto custom-scrollbar px-6 py-8 relative"
      style={{
        background: 'radial-gradient(ellipse at top, rgba(6, 182, 212, 0.03) 0%, transparent 60%), radial-gradient(ellipse at bottom, rgba(59, 130, 246, 0.03) 0%, transparent 60%)',
      }}
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, rgb(6, 182, 212) 1px, transparent 1px)`,
        backgroundSize: '40px 40px'
      }}></div>

      <div className="max-w-5xl mx-auto relative z-10">
        {messages.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[500px] text-center">
            <div className="relative">
              {/* Animated glow */}
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-full blur-3xl animate-pulse"></div>

              {/* Icon */}
              <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 flex items-center justify-center mb-8 shadow-2xl shadow-cyan-500/20">
                <Sparkles className="w-10 h-10 text-cyan-400" strokeWidth={1.5} />
              </div>
            </div>

            <h2 className="text-3xl font-bold bg-gradient-to-r from-white via-cyan-200 to-blue-200 bg-clip-text text-transparent mb-4">
              Financial RAG Assistant
            </h2>

            <p className="text-gray-400 mb-8 max-w-lg text-sm leading-relaxed">
              Ask questions about your financial documents and get AI-powered answers with
              source citations and relevance scores.
            </p>

            <div className="bg-gradient-to-br from-cyan-500/5 to-blue-500/5 border border-cyan-500/20 rounded-2xl p-6 max-w-md backdrop-blur-xl shadow-xl">
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                <p className="text-sm font-semibold text-cyan-300">Example Queries</p>
              </div>
              <ul className="space-y-2.5 text-sm text-gray-300 text-left">
                <li className="flex items-start gap-2 group cursor-pointer hover:text-white transition-colors">
                  <span className="text-cyan-500 mt-0.5">→</span>
                  <span>What is the fair value of investment properties?</span>
                </li>
                <li className="flex items-start gap-2 group cursor-pointer hover:text-white transition-colors">
                  <span className="text-cyan-500 mt-0.5">→</span>
                  <span>How is depreciation calculated?</span>
                </li>
                <li className="flex items-start gap-2 group cursor-pointer hover:text-white transition-colors">
                  <span className="text-cyan-500 mt-0.5">→</span>
                  <span>What was the total revenue for FY 2024-25?</span>
                </li>
                <li className="flex items-start gap-2 group cursor-pointer hover:text-white transition-colors">
                  <span className="text-cyan-500 mt-0.5">→</span>
                  <span>Analyze the strategic risks mentioned in the report</span>
                </li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble key={message.message_id || index} message={message} sessionId={sessionId} />
            ))}

            {isLoading && (
              <div className="flex justify-start mb-6">
                <div className="max-w-[85%]">
                  <TypingIndicator />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  );
}
