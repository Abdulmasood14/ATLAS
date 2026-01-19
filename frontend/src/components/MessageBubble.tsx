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
              ? 'bg-white border border-[#1762C7]/30 hover:border-[#1762C7]/50 text-gray-900'
              : 'bg-white border border-[#1762C7]/20 hover:border-[#1762C7]/30 text-gray-900'
          }`}
        >
          {/* Role Badge */}
          {!isUser && (
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#1762C7]/10">
              <div className="w-6 h-6 rounded-full flex items-center justify-center shadow-lg"
                   style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
                <Sparkles className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
              </div>
              <span className="text-[10px] font-semibold text-[#1762C7] uppercase tracking-wider">AI Assistant</span>
            </div>
          )}

          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap text-gray-900">{message.content}</p>
          ) : (
            <div className="text-sm leading-relaxed prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  ul: ({node, ...props}) => <ul className="list-disc list-outside ml-5 space-y-2 my-3" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-outside ml-5 space-y-2 my-3" {...props} />,
                  li: ({node, ...props}) => <li className="text-gray-700 leading-relaxed pl-1" {...props} />,
                  h1: ({node, ...props}) => <h1 className="text-xl font-bold text-gray-900 mt-4 mb-3" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-lg font-bold text-gray-900 mt-3 mb-2" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-base font-semibold text-gray-900 mt-2 mb-2" {...props} />,
                  p: ({node, ...props}) => <p className="text-gray-700 leading-relaxed mb-3" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                  em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                  blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-[#1762C7] pl-4 my-3 italic text-gray-600" {...props} />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Timestamp and Latency */}
          <div className="flex items-center gap-3 mt-3">
            <p className="text-[10px] text-gray-500">
              {message.created_at
                ? new Date(message.created_at).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : ''}
            </p>
            {!isUser && message.query_metadata?.response_time_ms && (
              <span className="text-[10px] text-[#1762C7] font-mono">
                {message.query_metadata.response_time_ms}ms
              </span>
            )}
          </div>
        </div>

        {/* Sources (only for assistant messages) */}
        {!isUser && sources.length > 0 && (
          <div className="mt-3 ml-1">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-xs text-[#1762C7] hover:text-[#1FA8A6] transition-all hover:gap-3 group"
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
                    className="text-xs bg-white border border-[#1762C7]/20 rounded-xl p-3 hover:border-[#1762C7]/40 transition-all cursor-pointer group shadow-sm hover:shadow-md"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-600 font-medium">
                          Page{source.pages?.length > 1 ? 's' : ''}:
                        </span>
                        <span className="text-[10px] font-mono text-[#1762C7] px-2 py-0.5 bg-[#1762C7]/10 rounded-full border border-[#1762C7]/20">
                          {source.pages?.join(', ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${source.score * 100}%`,
                              background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'
                            }}
                          />
                        </div>
                        <span className="text-[10px] text-[#1762C7] font-mono ml-1">
                          {(source.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-700 line-clamp-2 group-hover:line-clamp-none transition-all leading-relaxed">
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
