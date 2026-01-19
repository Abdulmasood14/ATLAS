'use client';

import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import CompanySelector from '../components/CompanySelector';
import FileUpload from '../components/FileUpload';
import ExportButton from '../components/ExportButton';
import { apiClient } from '../services/api';
import type { ChatMessage, ChatSession, Company } from '../types';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Activity,
  Clock,
  Settings,
  HelpCircle,
  FileText,
  Search,
  Bell,
  Cpu
} from 'lucide-react';

export default function Home() {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  // Initialize session when company changes
  useEffect(() => {
    if (selectedCompany) {
      initializeSession(selectedCompany);
    } else {
      setSession(null);
      setMessages([]);
    }
  }, [selectedCompany]);

  const initializeSession = async (company: Company) => {
    try {
      setIsLoading(true);
      const newSession = await apiClient.createSession(company.company_id, company.company_name);
      setSession(newSession);
      setMessages([]); // Clear previous messages
      console.log('Session created:', newSession.session_id);
      setError(null);
    } catch (err) {
      console.error('Failed to create session:', err);
      setError('Failed to initialize chat session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (query: string) => {
    if (!session || !selectedCompany) {
      setError('No active session. Please select a company.');
      return;
    }

    // Add user message immediately
    const userMessage: ChatMessage = {
      session_id: session.session_id,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Set loading state
    setIsLoading(true);
    setError(null);

    try {
      // Send query to backend
      const response = await apiClient.sendQuery(query, session.session_id, selectedCompany.company_id);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        message_id: response.message_id,
        session_id: session.session_id,
        role: 'assistant',
        content: response.answer,
        query_metadata: {
          sources: response.sources,
          model_used: response.model_used,
          retrieval_tier_used: response.retrieval_tier_used,
          success: response.success,
          error: response.error,
        },
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Failed to send query:', err);

      // Add error message
      const errorMessage: ChatMessage = {
        session_id: session.session_id,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message || 'Unknown error'}. Please try again.`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);

      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#020617] text-gray-100 overflow-hidden font-sans">

      {/* LEFT SIDEBAR: Navigation & Company Selection */}
      <aside className="w-64 bg-[#0F1729] border-r border-[#1E293B] flex flex-col shrink-0 z-20">
        {/* Logo Area */}
        <div className="h-16 flex items-center px-6 border-b border-[#1E293B] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
            </div>
            <span className="font-bold text-lg tracking-tight">FinRAG<span className="text-cyan-400">.ai</span></span>
          </div>
        </div>

        {/* Scrollable Nav Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">

          {/* Company Selector Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2">Analysis Target</h3>
            <CompanySelector
              onSelectCompany={(company) => {
                setSelectedCompany(company);
                setShowUpload(false);
              }}
              selectedCompanyId={selectedCompany?.company_id}
            />
            <button
              onClick={() => setShowUpload(!showUpload)}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-md border border-dashed border-gray-700 bg-gray-900/50 hover:bg-gray-800 text-xs text-gray-400 hover:text-cyan-400 transition-all group"
            >
              <FileText className="w-3 h-3 group-hover:scale-110 transition-transform" />
              {showUpload ? 'Cancel Upload' : 'Upload New Report'}
            </button>

            {showUpload && (
              <div className="animate-in fade-in zoom-in-95 duration-200">
                <FileUpload onUploadSuccess={() => {
                  setShowUpload(false);
                  window.location.reload();
                }} />
              </div>
            )}
          </div>
        </div>

        {/* User / Status Footer */}
        <div className="p-4 border-t border-[#1E293B] bg-[#0B1121]">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${session ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]`}></div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-300">System Status</p>
              <p className="text-[10px] text-gray-500 truncate">{session ? 'Online - ID: ' + session.session_id.slice(0, 4) : 'Standing By'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* CENTER: Chat Interface */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#020617] relative">
        {/* Header */}
        <header className="h-16 border-b border-[#1E293B] flex items-center justify-between px-6 bg-[#020617]/80 backdrop-blur-sm z-10 shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              {selectedCompany ? (
                <>
                  {selectedCompany.company_name}
                  <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">FY2024</span>
                </>
              ) : 'Dashboard'}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            {session && selectedCompany && (
              <ExportButton sessionId={session.session_id} isDisabled={messages.length === 0} />
            )}
            <div className="h-8 w-[1px] bg-[#1E293B]"></div>
            <button className="text-gray-400 hover:text-white transition-colors relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-pink-500 rounded-full border-2 border-[#020617]"></span>
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 border border-white/10 shadow-lg"></div>
          </div>
        </header>

        {/* Chat Area - ensuring flex-1 and overflow hidden to contain ChatWindow */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {selectedCompany ? (
            <>
              {/* Chat Window takes all available space and handles scrolling internally */}
              <div className="flex-1 relative overflow-hidden flex flex-col">
                <ChatWindow
                  messages={messages}
                  sessionId={session?.session_id || ''}
                  isLoading={isLoading}
                />
                {/* Suggested QuestionsOverlay (only if no messages) */}
                {messages.length === 0 && !isLoading && (
                  <div className="absolute bottom-4 left-0 w-full px-8 pb-4">
                    <div className="flex gap-2 justify-center flex-wrap">
                      {['Financial Performance', 'Strategic Risks', 'Operational Highlights', 'Future Outlook'].map((topic) => (
                        <button
                          key={topic}
                          onClick={() => handleSendMessage(`Analyze the ${topic.toLowerCase()} of this company.`)}
                          className="px-4 py-2 bg-[#1E293B]/80 hover:bg-cyan-500/20 border border-cyan-500/30 rounded-full text-xs text-cyan-300 transition-all hover:scale-105 backdrop-blur-sm"
                        >
                          {topic} ↗
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area fixed at bottom */}
              <div className="shrink-0 p-4 pb-6 bg-gradient-to-t from-[#020617] to-transparent z-10">
                <div className="max-w-4xl mx-auto">
                  <InputBox onSubmit={handleSendMessage} isDisabled={isLoading || !session} />
                  <p className="text-center text-[10px] text-gray-600 mt-2">
                    AI-generated insights. Verify important figures from original documents.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-gray-500">
              <div className="w-24 h-24 rounded-full bg-[#0F1729] border border-[#1E293B] flex items-center justify-center mb-6 shadow-2xl shadow-cyan-900/10">
                <Activity className="w-10 h-10 text-cyan-500/50" />
              </div>
              <h3 className="text-2xl font-bold text-gray-200 mb-2">Ready to Analyze</h3>
              <p className="max-w-md text-sm text-gray-400">
                Select a company from the sidebar to initialize the RAG engine and start your analysis session.
              </p>
            </div>
          )}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 px-4 py-2 bg-red-500/10 border border-red-500/50 text-red-200 rounded-lg backdrop-blur-md text-sm flex items-center gap-2 shadow-xl z-50 animate-in fade-in slide-in-from-top-4">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse my-auto"></div>
            {error}
            <button onClick={() => setError(null)} className="ml-2 hover:bg-white/10 p-1 rounded">✕</button>
          </div>
        )}
      </main>

      {/* RIGHT SIDEBAR: Widgets & Stats (Fixed width) */}
      <aside className="w-72 bg-[#0F1729] border-l border-[#1E293B] hidden xl:flex flex-col shrink-0 z-20">
        <div className="p-4 border-b border-[#1E293B]">
          <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Market Context
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">

          {/* Widget 1: System Stats */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">System Metrics</h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-[#0B1121] border border-[#1E293B] p-3 rounded-lg">
                <p className="text-[10px] text-gray-500 mb-1">Model</p>
                <p className="text-xs font-mono text-cyan-400">Phi 4</p>
              </div>
              <div className="bg-[#0B1121] border border-[#1E293B] p-3 rounded-lg">
                <p className="text-[10px] text-gray-500 mb-1">Latency</p>
                <p className="text-xs font-mono text-emerald-400">~800ms</p>
              </div>
            </div>
          </div>

          {/* Widget 2: Company Stats (Placeholder) */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">Entity Stats</h4>
            {selectedCompany ? (
              <div className="bg-[#0B1121] border border-[#1E293B] rounded-lg overflow-hidden">
                <div className="p-3 border-b border-[#1E293B] flex justify-between items-center">
                  <span className="text-xs text-gray-300">Total Chunks</span>
                  <span className="text-xs font-mono text-gray-100">{selectedCompany.chunk_count}</span>
                </div>
                <div className="p-3 border-b border-[#1E293B] flex justify-between items-center">
                  <span className="text-xs text-gray-300">Confidence</span>
                  <span className="text-xs font-mono text-emerald-400">High</span>
                </div>
                <div className="p-3 bg-cyan-500/5">
                  <div className="flex items-center gap-2 text-[10px] text-cyan-400">
                    <Cpu className="w-3 h-3" /> Processing Active
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 border border-dashed border-[#1E293B] rounded-lg">
                <p className="text-xs text-gray-600">No entity selected</p>
              </div>
            )}
          </div>

          {/* Widget 3: Recent Activity */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">Recent Activity</h4>
              <button className="text-[10px] text-cyan-400 hover:text-cyan-300">Clear</button>
            </div>
            <div className="space-y-2">
              {/* Fake items for design */}
              {[1, 2, 3].map((_, i) => (
                <div key={i} className="flex gap-3 items-start p-2 hover:bg-white/5 rounded-lg transition-colors cursor-pointer group">
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-600 mt-1.5 group-hover:bg-cyan-500 transition-colors"></div>
                  <div>
                    <p className="text-xs text-gray-300 line-clamp-1">Analysis of Q3 Revenue Growth</p>
                    <p className="text-[10px] text-gray-600">2 mins ago</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </aside>

    </div>
  );
}
