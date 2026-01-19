'use client';

import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import CompanySelector from '../components/CompanySelector';
import FileUpload from '../components/FileUpload';
import ExportButton from '../components/ExportButton';
import AnalysisTab from '../components/AnalysisTab';
import DeepDiveTab from '../components/DeepDiveTab';
import StoryTab from '../components/StoryTab';
import { apiClient } from '../services/api';
import type { ChatMessage, ChatSession, Company } from '../types';
import {
  BarChart3,
  TrendingUp,
  Activity,
  Clock,
  FileText,
  Bell,
  Cpu,
  Sparkles,
  MessageSquare,
  LineChart,
  Layers,
  BookOpen
} from 'lucide-react';

export default function Home() {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'analysis' | 'deepdive' | 'story'>('chat');

  // Analytics data caching - persists across tab switches
  const [analyticsCache, setAnalyticsCache] = useState<Record<string, any>>({});

  // Story data caching - persists across tab switches
  const [storyCache, setStoryCache] = useState<Record<string, any>>({});

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
          chunk_count: response.chunk_count,
        },
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Failed to send message:', err);

      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#eaf4f7] text-gray-900 overflow-hidden font-sans">

      {/* LEFT SIDEBAR: Navigation & Company Selection */}
      <aside className="w-64 bg-white/95 backdrop-blur-xl border-r border-[#1762C7]/20 flex flex-col shrink-0 z-20 shadow-xl">
        {/* Logo Area */}
        <div className="h-16 flex items-center px-6 border-b border-[#1762C7]/20 shrink-0">
          <div className="flex items-center gap-3">
            <img src="/xirr-logo.png" alt="XIRR.ai Atlas" className="w-8 h-8 object-contain" />
            <span className="font-bold text-lg tracking-tight text-gray-900">XIRR<span className="text-[#1762C7]">.ai</span> <span className="text-[#1FA8A6]">Atlas</span></span>
          </div>
        </div>

        {/* Scrollable Nav Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">

          {/* Company Selector Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider px-2 flex items-center gap-2">
              <BarChart3 className="w-3 h-3" />
              Analysis Target
            </h3>
            <CompanySelector
              onSelectCompany={(company) => {
                setSelectedCompany(company);
                setShowUpload(false);
              }}
              selectedCompanyId={selectedCompany?.company_id}
            />
            <button
              onClick={() => setShowUpload(!showUpload)}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg border border-dashed border-[#1762C7]/30 bg-[#1762C7]/5 hover:bg-[#1762C7]/10 text-xs text-[#1762C7] hover:border-[#1762C7]/50 transition-all group relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-[#1762C7]/0 via-[#1762C7]/10 to-[#1762C7]/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <FileText className="w-3.5 h-3.5 group-hover:scale-110 transition-transform relative z-10" />
              <span className="relative z-10">{showUpload ? 'Cancel Upload' : 'Upload New Report'}</span>
            </button>

            {showUpload && (
              <div className="animate-in fade-in zoom-in-95 duration-300">
                <FileUpload onUploadSuccess={(newCompanyId, newCompanyName) => {
                  setShowUpload(false);
                  // Auto-select the newly uploaded company
                  setSelectedCompany({
                    company_id: newCompanyId,
                    company_name: newCompanyName,
                    chunk_count: 0
                  });
                }} />
              </div>
            )}
          </div>
        </div>

        {/* User / Status Footer */}
        <div className="p-4 border-t border-[#1762C7]/20 bg-gray-50/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${session ? 'bg-emerald-400' : 'bg-amber-400'} animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.6)]`}></div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-700">System Status</p>
              <p className="text-[10px] text-gray-500 truncate">{session ? 'Connected - ' + session.session_id.slice(0, 8) : 'Awaiting Selection'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* CENTER: Chat Interface */}
      <main className="flex-1 flex flex-col min-w-0 bg-transparent relative">
        {/* Header */}
        <header className="h-16 border-b border-[#1762C7]/20 flex items-center justify-between px-6 bg-white/30 backdrop-blur-xl z-10 shrink-0">
          <div className="flex items-center gap-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              {selectedCompany ? (
                <>
                  {selectedCompany.company_name}
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] text-white border border-[#1762C7]/30 font-mono" style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
                    FY{selectedCompany.fiscal_year || new Date().getFullYear()}
                  </span>
                </>
              ) : (
                <>
                  <Activity className="w-5 h-5 text-[#1762C7]" />
                  Dashboard
                </>
              )}
            </h2>

            {/* Tab Navigation */}
            {selectedCompany && (
              <div className="flex gap-1 border border-[#1762C7]/20 rounded-lg p-1 bg-white/50">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'chat'
                      ? 'text-white shadow-lg'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={activeTab === 'chat' ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
                >
                  <MessageSquare className="w-4 h-4" />
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'analysis'
                      ? 'text-white shadow-lg'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={activeTab === 'analysis' ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
                >
                  <LineChart className="w-4 h-4" />
                  Analysis
                </button>
                <button
                  onClick={() => setActiveTab('deepdive')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'deepdive'
                      ? 'text-white shadow-lg'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={activeTab === 'deepdive' ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
                >
                  <Layers className="w-4 h-4" />
                  Deep Dive
                </button>
                <button
                  onClick={() => setActiveTab('story')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'story'
                      ? 'text-white shadow-lg'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={activeTab === 'story' ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
                >
                  <BookOpen className="w-4 h-4" />
                  Story
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-4">
            {session && selectedCompany && activeTab === 'chat' && (
              <ExportButton sessionId={session.session_id} isDisabled={messages.length === 0} />
            )}
            <div className="h-8 w-[1px] bg-[#1762C7]/20"></div>
            <button className="text-gray-600 hover:text-gray-900 transition-colors relative group">
              <Bell className="w-5 h-5" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-pink-500 rounded-full border-2 border-[#eaf4f7] group-hover:scale-125 transition-transform"></span>
            </button>
            <img src="/xirr-logo.png" alt="XIRR.ai" className="w-8 h-8 object-contain rounded-full border border-[#1762C7]/20 shadow-lg hover:shadow-xl transition-all cursor-pointer" />
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {selectedCompany ? (
            <>
              {/* Chat Tab */}
              {activeTab === 'chat' && (
                <>
                  {/* Chat Window */}
                  <div className="flex-1 relative overflow-hidden flex flex-col">
                    <ChatWindow
                      messages={messages}
                      sessionId={session?.session_id || ''}
                      isLoading={isLoading}
                      companyId={selectedCompany?.company_id}
                      companyName={selectedCompany?.company_name}
                      onSendMessage={handleSendMessage}
                    />
                    {/* Suggested Questions */}
                    {messages.length === 0 && !isLoading && (
                      <div className="absolute bottom-4 left-0 w-full px-8 pb-4 pointer-events-none">
                        <div className="flex gap-2 justify-center flex-wrap pointer-events-auto">
                          {['Financial Performance', 'Strategic Risks', 'Operational Highlights', 'Future Outlook'].map((topic) => (
                            <button
                              key={topic}
                              onClick={() => handleSendMessage(`Analyze the ${topic.toLowerCase()} of this company.`)}
                              className="px-4 py-2.5 bg-white/80 hover:bg-white border border-[#1762C7]/30 hover:border-[#1762C7]/50 rounded-full text-xs text-[#1762C7] transition-all hover:scale-105 shadow-lg group"
                            >
                              <span className="flex items-center gap-1.5">
                                {topic}
                                <span className="group-hover:translate-x-0.5 transition-transform">↗</span>
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Input Area */}
                  <div className="shrink-0 bg-white/50 backdrop-blur-sm z-10 border-t border-[#1762C7]/20">
                    <div className="max-w-5xl mx-auto px-6 py-4">
                      <InputBox onSubmit={handleSendMessage} isDisabled={isLoading || !session} />
                    </div>
                  </div>
                </>
              )}

              {/* Analysis Tab */}
              {activeTab === 'analysis' && (
                <AnalysisTab
                  companyId={selectedCompany.company_id}
                  companyName={selectedCompany.company_name}
                  tickerSymbol={undefined}
                  cachedData={analyticsCache[selectedCompany.company_id]}
                  onDataLoaded={(data) => setAnalyticsCache(prev => ({...prev, [selectedCompany.company_id]: data}))}
                />
              )}

              {/* Deep Dive Tab */}
              {activeTab === 'deepdive' && (
                <DeepDiveTab
                  companyId={selectedCompany.company_id}
                  companyName={selectedCompany.company_name}
                />
              )}

              {/* Story Tab */}
              {activeTab === 'story' && (
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                  <StoryTab
                    companyId={selectedCompany.company_id}
                    companyName={selectedCompany.company_name}
                    cachedData={storyCache[selectedCompany.company_id]}
                    onDataLoaded={(data) => setStoryCache(prev => ({...prev, [selectedCompany.company_id]: data}))}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-gray-600">
              <div className="w-28 h-28 rounded-full bg-white border border-[#1762C7]/20 flex items-center justify-center mb-6 shadow-xl">
                <Activity className="w-12 h-12 text-[#1762C7]/70" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Ready to Analyze</h3>
              <p className="max-w-md text-sm text-gray-600">
                Select a company from the sidebar to initialize the RAG engine and start your analysis session.
              </p>
            </div>
          )}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 px-5 py-3 bg-red-50 border border-red-300 text-red-700 rounded-xl backdrop-blur-xl text-sm flex items-center gap-3 shadow-2xl z-50 animate-in fade-in slide-in-from-top-4">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            {error}
            <button onClick={() => setError(null)} className="ml-2 hover:bg-red-100 p-1.5 rounded-lg transition-colors">✕</button>
          </div>
        )}
      </main>

      {/* RIGHT SIDEBAR: Widgets & Stats */}
      <aside className="w-72 bg-white/95 backdrop-blur-xl border-l border-[#1762C7]/20 hidden xl:flex flex-col shrink-0 z-20 shadow-xl">
        <div className="p-4 border-b border-[#1762C7]/20">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#1762C7]" />
            Insights
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">

          {/* System Metrics */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">System Metrics</h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white border border-[#1762C7]/20 p-3 rounded-xl hover:border-[#1762C7]/40 transition-all cursor-pointer group shadow-sm">
                <p className="text-[10px] text-gray-600 mb-1.5">Model</p>
                <p className="text-xs font-mono text-[#1762C7] group-hover:text-[#1FA8A6] transition-colors">Phi 4</p>
              </div>
              <div className="bg-white border border-emerald-500/20 p-3 rounded-xl hover:border-emerald-400/40 transition-all cursor-pointer group shadow-sm">
                <p className="text-[10px] text-gray-600 mb-1.5">Latency</p>
                <p className="text-xs font-mono text-emerald-600 group-hover:text-emerald-500 transition-colors">~800ms</p>
              </div>
            </div>
          </div>

          {/* Entity Stats */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">Entity Stats</h4>
            {selectedCompany ? (
              <div className="bg-white border border-[#1762C7]/20 rounded-xl overflow-hidden hover:border-[#1762C7]/40 transition-all shadow-sm">
                <div className="p-3 border-b border-[#1762C7]/10 flex justify-between items-center group cursor-pointer hover:bg-gray-50 transition-colors">
                  <span className="text-xs text-gray-700">Total Chunks</span>
                  <span className="text-xs font-mono text-[#1762C7] group-hover:text-[#1FA8A6] transition-colors">{selectedCompany.chunk_count}</span>
                </div>
                <div className="p-3 border-b border-[#1762C7]/10 flex justify-between items-center group cursor-pointer hover:bg-gray-50 transition-colors">
                  <span className="text-xs text-gray-700">Messages</span>
                  <span className="text-xs font-mono text-[#1762C7] group-hover:text-[#1FA8A6] transition-colors">{messages.length}</span>
                </div>
                <div className="p-3" style={{background: 'linear-gradient(to right, rgba(31, 168, 166, 0.1), rgba(23, 98, 199, 0.1))'}}>
                  <div className="flex items-center gap-2 text-[10px] text-[#1762C7]">
                    <Cpu className="w-3 h-3 animate-pulse" /> Engine Active
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 border border-dashed border-[#1762C7]/20 rounded-xl bg-white shadow-sm">
                <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2 opacity-50" />
                <p className="text-xs text-gray-500">No entity selected</p>
              </div>
            )}
          </div>

          {/* Recent Queries - REAL DATA */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">Recent Queries</h4>
              {messages.filter(m => m.role === 'user').length > 0 && (
                <button
                  onClick={() => setMessages([])}
                  className="text-[10px] text-[#1762C7] hover:text-[#1FA8A6] transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="space-y-2">
              {messages.filter(m => m.role === 'user').slice(-5).reverse().map((msg, i) => (
                <div
                  key={msg.message_id || i}
                  className="flex gap-3 items-start p-2.5 hover:bg-gray-50 rounded-lg transition-all cursor-pointer group border border-transparent hover:border-[#1762C7]/20"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-[#1762C7]/60 mt-1.5 group-hover:bg-[#1FA8A6] transition-all flex-shrink-0"></div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-gray-700 line-clamp-2 group-hover:text-gray-900 transition-colors leading-relaxed">{msg.content}</p>
                    <p className="text-[10px] text-gray-500 mt-1">
                      {msg.created_at ? new Date(msg.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                    </p>
                  </div>
                </div>
              ))}
              {messages.filter(m => m.role === 'user').length === 0 && (
                <div className="text-center p-6 border border-dashed border-[#1762C7]/20 rounded-xl bg-white shadow-sm">
                  <Clock className="w-7 h-7 text-gray-400 mx-auto mb-2 opacity-50" />
                  <p className="text-xs text-gray-500">No queries yet</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </aside>

    </div>
  );
}
