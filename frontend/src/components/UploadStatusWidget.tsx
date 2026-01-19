'use client';

import React, { useState, useEffect, useRef } from 'react';
import { FileText, Check, Loader2, AlertCircle, Terminal, CheckCircle2, XCircle } from 'lucide-react';
import { apiClient } from '../services/api';

interface UploadStatus {
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  upload_id?: number;
  fileName?: string;
  chunksCreated?: number;
  chunksStored?: number;
  error?: string;
}

interface UploadStatusWidgetProps {
  uploadStatus: UploadStatus;
  onClose?: () => void;
}

interface LogEntry {
  message: string;
  level: string;
  timestamp: number;
}

export default function UploadStatusWidget({ uploadStatus, onClose }: UploadStatusWidgetProps) {
  const [internalStatus, setInternalStatus] = useState<UploadStatus>(uploadStatus);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [showLogs, setShowLogs] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Sync internal status with prop
  useEffect(() => {
    setInternalStatus(prev => {
      const next = { ...prev, ...uploadStatus };

      // Don't let prop reset progress if we've made progress via WebSocket
      if (prev.status === 'processing' && uploadStatus.status === 'processing' && uploadStatus.progress === 0) {
        next.progress = prev.progress;
      }

      // Don't overwrite completed status
      if (prev.status === 'completed' && uploadStatus.status === 'processing') {
        return prev;
      }

      return next;
    });
  }, [uploadStatus]);

  // Scroll logs to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Handle WebSocket for processing logs
  useEffect(() => {
    if (internalStatus.status !== 'processing' || !internalStatus.upload_id) return;

    const wsUrl = apiClient.getIngestionWebSocketUrl(internalStatus.upload_id);
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'log') {
        const log = data.data as LogEntry;
        setLogs(prev => [...prev.slice(-19), log]);

        const msg = log.message.toLowerCase();

        // Stage detection
        if (msg.includes('stage 1') || msg.includes('orientation')) setActiveStep(1);
        if (msg.includes('stage 2') || msg.includes('ingestion into rag')) setActiveStep(2);
        if (msg.includes('extracting pages')) setActiveStep(3);
        if (msg.includes('detecting section')) setActiveStep(4);
        if (msg.includes('chunking')) setActiveStep(5);
        if (msg.includes('classifying')) setActiveStep(6);
        if (msg.includes('embedding')) setActiveStep(7);
        if (msg.includes('storing chunks')) setActiveStep(8);

        // Progress updates
        setInternalStatus(prev => {
          let newProgress = prev.progress;

          // Stage-based progress
          if (msg.includes('stage 1')) newProgress = Math.max(newProgress, 5);
          if (msg.includes('stage 2')) newProgress = Math.max(newProgress, 30);
          if (msg.includes('extracting pages')) newProgress = Math.max(newProgress, 40);
          if (msg.includes('detecting section')) newProgress = Math.max(newProgress, 50);
          if (msg.includes('chunking')) newProgress = Math.max(newProgress, 60);
          if (msg.includes('classifying')) newProgress = Math.max(newProgress, 70);
          if (msg.includes('embedding')) newProgress = Math.max(newProgress, 80);
          if (msg.includes('storing chunks')) newProgress = Math.max(newProgress, 90);

          // Completion detection - CRITICAL FIX
          if (msg.includes('ingestion complete') || msg.includes('status: success')) {
            newProgress = 100;
            // Trigger completion state
            setTimeout(() => {
              playSuccessSound();
              setInternalStatus(s => ({ ...s, status: 'completed', progress: 100 }));
            }, 500);
          }

          // Slow creep
          if (newProgress < 98 && newProgress > 0) {
            newProgress += 0.15;
          }

          return { ...prev, progress: Math.min(newProgress, 100) };
        });
      } else if (data.type === 'status') {
        if (data.data.status === 'completed') {
          playSuccessSound();
          apiClient.getUploadStatus(internalStatus.upload_id!).then(res => {
            setInternalStatus({
              ...internalStatus,
              status: 'completed',
              progress: 100,
              chunksCreated: res.chunks_created,
              chunksStored: res.chunks_stored
            });
          });
        } else if (data.data.status === 'failed') {
          setInternalStatus(prev => ({ ...prev, status: 'failed', error: 'Ingestion failed.' }));
        }
      }
    };

    ws.onerror = () => console.error('WebSocket Error');

    return () => ws.close();
  }, [internalStatus.status, internalStatus.upload_id]);

  const playSuccessSound = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
      console.error('Audio error:', e);
    }
  };

  const steps = [
    'Orientation Correction',
    'RAG Pipeline Init',
    'Text Extraction & OCR',
    'Section Boundary Detection',
    'Adaptive Chunking',
    'AI Chunk Classification',
    'Neural Embeddings',
    'PostgreSQL Vector Storage'
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-700/50 overflow-hidden animate-slideUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-white/5 animate-shimmer"></div>
          <div className="relative flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl backdrop-blur-sm">
              {internalStatus.status === 'completed' ? (
                <CheckCircle2 className="w-8 h-8 text-white" />
              ) : internalStatus.status === 'failed' ? (
                <XCircle className="w-8 h-8 text-white" />
              ) : (
                <FileText className="w-8 h-8 text-white animate-pulse" />
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-white">
                {internalStatus.status === 'completed' ? 'Processing Complete!' :
                  internalStatus.status === 'failed' ? 'Processing Failed' :
                    'Analyzing & Ingesting...'}
              </h3>
              <p className="text-blue-100 text-sm mt-1">{internalStatus.fileName || 'Document'}</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="px-6 pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-300">AI Processing Pipeline</span>
            <span className="text-sm font-bold text-blue-400">{Math.round(internalStatus.progress)}%</span>
          </div>
          <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out relative overflow-hidden"
              style={{ width: `${internalStatus.progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-shimmer"></div>
            </div>
          </div>
        </div>

        {/* Processing Steps */}
        <div className="px-6 py-4">
          <div className="grid grid-cols-2 gap-2">
            {steps.map((step, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-2 p-2 rounded-lg transition-all duration-300 ${activeStep > idx ? 'bg-green-500/10 border border-green-500/30' :
                    activeStep === idx + 1 ? 'bg-blue-500/10 border border-blue-500/30 animate-pulse' :
                      'bg-slate-800/30 border border-slate-700/30'
                  }`}
              >
                {activeStep > idx ? (
                  <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                ) : activeStep === idx + 1 ? (
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-slate-600 flex-shrink-0"></div>
                )}
                <span className={`text-xs font-medium ${activeStep > idx ? 'text-green-300' :
                    activeStep === idx + 1 ? 'text-blue-300' :
                      'text-slate-500'
                  }`}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Live Console Toggle */}
        <div className="px-6">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            <Terminal className="w-4 h-4" />
            <span>{showLogs ? 'Hide' : 'Show'} Live Console</span>
          </button>
        </div>

        {/* Live Console */}
        {showLogs && (
          <div className="px-6 py-4 animate-slideDown">
            <div className="bg-slate-950/50 rounded-lg p-4 h-48 overflow-y-auto border border-slate-700/30 font-mono text-xs">
              {logs.length === 0 ? (
                <div className="flex items-center gap-2 text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Initializing secure link...</span>
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div
                    key={idx}
                    className={`py-1 animate-fadeIn ${log.level === 'error' ? 'text-red-400' :
                        log.level === 'warning' ? 'text-yellow-400' :
                          log.level === 'success' ? 'text-green-400' :
                            'text-slate-300'
                      }`}
                  >
                    {log.message}
                  </div>
                ))
              )}
              <div ref={logEndRef} />
            </div>
          </div>
        )}

        {/* Stats */}
        {internalStatus.status === 'completed' && (
          <div className="px-6 py-4 bg-slate-800/30 border-t border-slate-700/30 animate-fadeIn">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{internalStatus.chunksCreated || 0}</div>
                <div className="text-xs text-slate-400">Chunks Created</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{internalStatus.chunksStored || 0}</div>
                <div className="text-xs text-slate-400">Chunks Stored</div>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {internalStatus.status === 'failed' && (
          <div className="px-6 py-4 bg-red-500/10 border-t border-red-500/30 animate-fadeIn">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-300">Processing Error</p>
                <p className="text-xs text-red-400 mt-1">{internalStatus.error || 'Unknown error occurred'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-800/30 border-t border-slate-700/30 flex justify-end">
          {internalStatus.status === 'completed' || internalStatus.status === 'failed' ? (
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Close
            </button>
          ) : null}
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes slideDown {
          from { max-height: 0; opacity: 0; }
          to { max-height: 500px; opacity: 1; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.4s ease-out;
        }
        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
        .animate-shimmer::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}
