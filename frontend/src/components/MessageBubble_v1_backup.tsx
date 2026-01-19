'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
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
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 message-enter`}>
      <div className={`max-w-[80%] ${isUser ? 'order-1' : 'order-2'}`}>
        {/* Message Content */}
        <div
          className={`px-4 py-3 rounded-2xl ${isUser
              ? 'bg-primary/20 text-text-primary border border-primary/50'
              : 'glass-effect text-text-secondary'
            }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="text-sm leading-relaxed markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Timestamp */}
          <p className="text-xs text-text-muted mt-2">
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
          <div className="mt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-xs text-primary hover:text-primary-light transition-colors"
            >
              <FileText size={14} />
              <span>
                {sources.length} source{sources.length > 1 ? 's' : ''}
              </span>
              {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {showSources && (
              <div className="mt-2 space-y-2 animate-slide-up">
                {sources.slice(0, 3).map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-background-card/50 border border-primary/10 rounded-lg p-2"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-text-muted">
                        Page{source.pages?.length > 1 ? 's' : ''}: {source.pages?.join(', ')}
                      </span>
                      <span className="text-primary text-[10px]">
                        Score: {(source.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-text-secondary line-clamp-2">{source.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Feedback Buttons (only for assistant messages with message_id) */}
        {!isUser && message.message_id && (
          <div className="mt-2">
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
