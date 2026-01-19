'use client';

import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Loader2, FileText, Zap, Database, Brain } from 'lucide-react';

interface UploadStatusProps {
  uploadId: number;
  fileName: string;
  onClose: () => void;
}

export default function UploadStatusWidget({ uploadId, fileName, onClose }: UploadStatusProps) {
  const [status, setStatus] = useState<'uploading' | 'processing' | 'completed' | 'failed'>('uploading');
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [chunksCreated, setChunksCreated] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const stages = [
    { icon: FileText, label: 'Uploading file', color: 'text-blue-400' },
    { icon: Zap, label: 'Processing document', color: 'text-yellow-400' },
    { icon: Brain, label: 'AI Analysis', color: 'text-purple-400' },
    { icon: Database, label: 'Storing in database', color: 'text-green-400' },
  ];

  useEffect(() => {
    // Poll for status
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/upload/status/${uploadId}`);
        const data = await response.json();

        setStatus(data.upload_status);
        setChunksCreated(data.chunks_created || 0);

        // Calculate progress based on status
        if (data.upload_status === 'completed') {
          setProgress(100);
          setCurrentStage(3);
          clearInterval(pollInterval);
        } else if (data.upload_status === 'processing') {
          // Simulate progress during processing
          setProgress(prev => Math.min(prev + 2, 95));
          setCurrentStage(Math.floor((progress / 100) * 3));
        } else if (data.upload_status === 'failed') {
          setErrorMessage(data.error_message || 'Upload failed');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Failed to poll status:', error);
      }
    }, 1000); // Poll every second

    return () => clearInterval(pollInterval);
  }, [uploadId, progress]);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] border border-cyan-500/30 rounded-2xl max-w-lg w-full shadow-2xl shadow-cyan-500/20 animate-in zoom-in-95 duration-300">
        {/* Header */}
        <div className="p-6 border-b border-cyan-500/20">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                {status === 'completed' ? (
                  <CheckCircle className="w-6 h-6 text-green-400" />
                ) : status === 'failed' ? (
                  <AlertCircle className="w-6 h-6 text-red-400" />
                ) : (
                  <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                )}
                {status === 'completed' ? 'Upload Complete!' : status === 'failed' ? 'Upload Failed' : 'Processing Document'}
              </h3>
              <p className="text-sm text-gray-400 truncate">{fileName}</p>
            </div>
            {status === 'completed' && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Progress */}
        <div className="p-6 space-y-6">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-300 font-medium">Progress</span>
              <span className="text-cyan-400 font-bold">{progress}%</span>
            </div>
            <div className="h-3 bg-gray-800/50 rounded-full overflow-hidden relative">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-500 ease-out relative"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
              </div>
            </div>
          </div>

          {/* Stages */}
          <div className="space-y-3">
            {stages.map((stage, idx) => {
              const StageIcon = stage.icon;
              const isCompleted = idx < currentStage;
              const isCurrent = idx === currentStage;
              const isUpcoming = idx > currentStage;

              return (
                <div
                  key={idx}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                    isCurrent ? 'bg-cyan-500/10 border border-cyan-500/30' : 'border border-transparent'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                      isCompleted
                        ? 'bg-green-500/20 border-2 border-green-500'
                        : isCurrent
                        ? 'bg-cyan-500/20 border-2 border-cyan-500'
                        : 'bg-gray-800 border-2 border-gray-700'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <StageIcon className={`w-5 h-5 ${isCurrent ? stage.color : 'text-gray-600'} ${isCurrent && 'animate-pulse'}`} />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${isCurrent ? 'text-white' : isCompleted ? 'text-gray-300' : 'text-gray-500'}`}>
                      {stage.label}
                    </p>
                    {isCurrent && status === 'processing' && (
                      <div className="flex items-center gap-1 mt-1">
                        <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-ping"></div>
                        <span className="text-xs text-cyan-400">In progress...</span>
                      </div>
                    )}
                  </div>
                  {isCompleted && (
                    <div className="text-xs text-green-400 font-medium">✓</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Stats */}
          {chunksCreated > 0 && (
            <div className="bg-gray-800/50 rounded-lg p-4 border border-cyan-500/20">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Chunks Created</span>
                <span className="text-lg font-bold text-cyan-400">{chunksCreated.toLocaleString()}</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {status === 'failed' && errorMessage && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-sm text-red-400">{errorMessage}</p>
            </div>
          )}

          {/* Success Message */}
          {status === 'completed' && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <p className="text-sm text-green-400">
                ✓ Document successfully processed and added to the knowledge base!
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        {status === 'completed' && (
          <div className="p-6 border-t border-cyan-500/20">
            <button
              onClick={onClose}
              className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50"
            >
              Continue to Chat
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
