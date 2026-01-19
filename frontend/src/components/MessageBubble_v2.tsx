'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Sparkles } from 'lucide-react';
import type { ChatMessage } from '../types';
import FeedbackButtons from './FeedbackButtons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: ChatMessage;
  sessionId: string;
}

export default function MessageBubble({ message, sessionId }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  const sources = message.query_metadata?.sources || [];

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-in fade-in slide-in-from-bottom-4 duration-500`}>
      <div className={`max-w-[85%] ${isUser ? 'order-1' : 'order-2'}`}>
        {/* Message Content */}
        <div
          className={`px-5 py-4 rounded-2xl shadow-lg transition-all duration-300 hover:shadow-xl ${
            isUser
              ? 'bg-gradient-to-br from-cyan-500/15 to-blue-500/15 text-white border border-cyan-500/30 hover:border-cyan-400/50 shadow-cyan-500/10'
              : 'bg-gradient-to-br from-[#1a1f35]/80 to-[#0F1729]/80 backdrop-blur-xl text-gray-100 border border-cyan-500/10 hover:border-cyan-500/20 shadow-cyan-900/20'
          }`}
        >
          {/* Role Badge */}
          {!isUser && (
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-cyan-500/10">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                <Sparkles className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
              </div>
              <span className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider">AI Assistant</span>
            </div>
          )}

          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="text-sm leading-relaxed markdown-content prose prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Timestamp */}
          <p className={`text-[10px] mt-3 ${isUser ? 'text-cyan-300/70' : 'text-gray-500'}`}>
            {message.created_at
              ? new Date(message.created_at).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : ''}
          </p>
        </div>

        {/* Sources (only for assistant messages) */}
        {!isUser && sources.length > 0 && (
          <div className="mt-3 ml-1">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 transition-all hover:gap-3 group"
            >
              <FileText size={14} className="group-hover:scale-110 transition-transform" />
              <span className="font-medium">
                {sources.length} source{sources.length > 1 ? 's' : ''}
              </span>
              {showSources ? (
                <ChevronUp size={14} className="group-hover:-translate-y-0.5 transition-transform" />
              ) : (
                <ChevronDown size={14} className="group-hover:translate-y-0.5 transition-transform" />
              )}
            </button>

            {showSources && (
              <div className="mt-3 space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                {sources.slice(0, 3).map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-gradient-to-br from-cyan-500/5 to-blue-500/5 border border-cyan-500/20 rounded-xl p-3 hover:border-cyan-400/40 transition-all cursor-pointer group shadow-sm hover:shadow-md"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-400 font-medium">
                          Page{source.pages?.length > 1 ? 's' : ''}:
                        </span>
                        <span className="text-[10px] font-mono text-cyan-300 px-2 py-0.5 bg-cyan-500/10 rounded-full border border-cyan-500/20">
                          {source.pages?.join(', ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
                            style={{ width: `${source.score * 100}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-cyan-400 font-mono ml-1">
                          {(source.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-300 line-clamp-2 group-hover:line-clamp-none transition-all leading-relaxed">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Feedback Buttons (only for assistant messages with message_id) */}
        {!isUser && message.message_id && (
          <div className="mt-3 ml-1">
            <FeedbackButtons
              messageId={message.message_id}
              sessionId={sessionId}
              initialScore={message.feedback_score}
            />
          </div>
        )}
      </div>
    </div>
  );
}
