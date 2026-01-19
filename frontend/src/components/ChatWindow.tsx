'use client';

import React, { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../types';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { Sparkles, MessageSquare, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

interface ChatWindowProps {
  messages: ChatMessage[];
  sessionId: string;
  isLoading: boolean;
  companyId?: string;
  companyName?: string;
  onSendMessage?: (query: string) => void;
}

export default function ChatWindow({ messages, sessionId, isLoading, companyId, companyName, onSendMessage }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Load dynamic suggested questions when company changes
  useEffect(() => {
    if (companyId && companyName && messages.length === 0) {
      loadSuggestedQuestions();
    }
  }, [companyId, companyName, messages.length]);

  const loadSuggestedQuestions = async () => {
    if (!companyId || !companyName) return;

    setLoadingQuestions(true);
    try {
      const response = await apiClient.generateSuggestions(companyId, companyName, 4);
      setSuggestedQuestions(response.questions);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
      // Fallback questions
      setSuggestedQuestions([
        `What are the key financial metrics for ${companyName}?`,
        `What strategic risks does ${companyName} face?`,
        `What are ${companyName}'s growth initiatives?`,
        `How does ${companyName} generate revenue?`
      ]);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleQuestionClick = (question: string) => {
    if (onSendMessage) {
      onSendMessage(question);
    }
  };

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
              {/* Icon */}
              <div className="relative w-20 h-20 rounded-full flex items-center justify-center mb-8 shadow-xl"
                   style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
                <Sparkles className="w-10 h-10 text-white" strokeWidth={1.5} />
              </div>
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {companyName ? `Analyzing ${companyName}` : 'Financial RAG Assistant'}
            </h2>

            <p className="text-gray-600 mb-8 max-w-lg text-sm leading-relaxed">
              Ask questions about your financial documents and get AI-powered answers with
              source citations and relevance scores.
            </p>

            <div className="bg-white border border-[#1762C7]/20 rounded-2xl p-6 max-w-2xl w-full shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-[#1762C7]" />
                  <p className="text-sm font-semibold text-gray-900">
                    {loadingQuestions ? 'Generating Questions...' : 'Suggested Questions'}
                  </p>
                </div>
                {loadingQuestions && (
                  <Loader2 className="w-4 h-4 text-[#1762C7] animate-spin" />
                )}
              </div>

              {loadingQuestions ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-12 bg-[#1762C7]/10 rounded-lg animate-pulse"></div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {suggestedQuestions.map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuestionClick(question)}
                      className="text-left p-3 bg-white hover:bg-[#1762C7]/5 border-2 border-[#1762C7]/30 hover:border-[#1762C7]/60 rounded-xl text-sm text-gray-700 hover:text-gray-900 transition-all hover:scale-105 group shadow-md hover:shadow-lg"
                    >
                      <span className="flex items-start gap-2">
                        <span className="text-[#1762C7] mt-0.5 group-hover:translate-x-1 transition-transform">→</span>
                        <span className="leading-relaxed">{question}</span>
                      </span>
                    </button>
                  ))}
                </div>
              )}
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
