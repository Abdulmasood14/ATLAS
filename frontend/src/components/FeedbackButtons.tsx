/**
 * Feedback Buttons Component (RLHF)
 *
 * Three-button feedback system for assistant responses:
 * - Good (1.0) - Thumbs up
 * - Medium (0.5) - Neutral
 * - Bad (0.0) - Thumbs down
 */
'use client';

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Minus } from 'lucide-react';
import { apiClient } from '../services/api';

interface FeedbackButtonsProps {
  messageId: number;
  sessionId: string;
  initialScore?: number | null;
  onFeedbackSubmitted?: (score: number) => void;
}

export default function FeedbackButtons({
  messageId,
  sessionId,
  initialScore = null,
  onFeedbackSubmitted,
}: FeedbackButtonsProps) {
  const [selectedScore, setSelectedScore] = useState<number | null>(initialScore);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const handleFeedback = async (score: 0 | 0.5 | 1) => {
    if (isSubmitting) return;

    setIsSubmitting(true);

    try {
      await apiClient.submitFeedback(messageId, sessionId, score);

      setSelectedScore(score);
      setShowToast(true);

      // Hide toast after 2 seconds
      setTimeout(() => setShowToast(false), 2000);

      // Notify parent component
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(score);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getButtonClass = (score: number) => {
    const baseClass = 'relative group px-3 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-1.5';

    if (selectedScore === score) {
      // Selected state
      if (score === 1.0) {
        return `${baseClass} bg-emerald-50 text-emerald-600 border border-emerald-300`;
      } else if (score === 0.5) {
        return `${baseClass} bg-amber-50 text-amber-600 border border-amber-300`;
      } else {
        return `${baseClass} bg-red-50 text-red-600 border border-red-300`;
      }
    } else {
      // Unselected state
      return `${baseClass} bg-gray-100 text-gray-600 hover:bg-[#1762C7]/10 border border-gray-300 hover:border-[#1762C7]/30`;
    }
  };

  return (
    <div className="flex items-center gap-2 mt-2">
      {/* Good Button */}
      <button
        onClick={() => handleFeedback(1.0)}
        disabled={isSubmitting}
        className={getButtonClass(1.0)}
        title="Good response"
      >
        <ThumbsUp size={14} className={selectedScore === 1.0 ? 'fill-current' : ''} />
        <span className="text-xs font-medium">Good</span>
      </button>

      {/* Medium Button */}
      <button
        onClick={() => handleFeedback(0.5)}
        disabled={isSubmitting}
        className={getButtonClass(0.5)}
        title="Medium response"
      >
        <Minus size={14} />
        <span className="text-xs font-medium">Medium</span>
      </button>

      {/* Bad Button */}
      <button
        onClick={() => handleFeedback(0.0)}
        disabled={isSubmitting}
        className={getButtonClass(0.0)}
        title="Bad response"
      >
        <ThumbsDown size={14} className={selectedScore === 0.0 ? 'fill-current' : ''} />
        <span className="text-xs font-medium">Bad</span>
      </button>

      {/* Toast Notification */}
      {showToast && (
        <div className="ml-2 px-3 py-1 bg-[#1762C7]/10 text-[#1762C7] text-xs rounded-md border border-[#1762C7]/30 animate-fade-in">
          ✓ Feedback recorded
        </div>
      )}
    </div>
  );
}
