'use client';

import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

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
      className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6"
      style={{
        background: 'linear-gradient(180deg, #0F1729 0%, #1E293B 100%)',
      }}
    >
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
            <div className="glass-effect px-8 py-12 rounded-2xl max-w-md">
              <h2 className="text-2xl font-bold text-primary mb-3">
                Welcome to Financial RAG Assistant
              </h2>
              <p className="text-text-secondary mb-6">
                Ask questions about your financial documents and get AI-powered answers with
                source citations.
              </p>
              <div className="space-y-2 text-sm text-text-muted text-left">
                <p>💡 <strong>Example queries:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>What is the fair value of investment properties?</li>
                  <li>How is depreciation calculated?</li>
                  <li>What was the total revenue for FY 2024-25?</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.message_id || Math.random()} message={message} sessionId={sessionId} />
            ))}

            {isLoading && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  );
}
