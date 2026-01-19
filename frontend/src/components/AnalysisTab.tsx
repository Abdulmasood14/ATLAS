'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { apiClient } from '../services/api';
import {
  TrendingUp,
  DollarSign,
  BarChart3,
  Building2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  PieChart,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  Layers,
  ShieldCheck,
  Target,
  Cpu,
  X
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

interface MetricValue {
  key: string;
  name: string;
  value: any;
  source: string;
  confidence: number;
  extracted_at: string;
}

interface AnalyticsData {
  company_id: string;
  company_name: string;
  ticker_symbol?: string;
  metrics: MetricValue[];
  categories: {
    market?: MetricValue[];
    performance?: MetricValue[];
    company_info?: MetricValue[];
    business?: MetricValue[];
    governance?: MetricValue[];
  };
  extraction_status: string;
  generated_at: string;
}

interface AnalysisTabProps {
  companyId?: string;
  companyName?: string;
  tickerSymbol?: string;
  cachedData?: AnalyticsData | null;
  onDataLoaded?: (data: AnalyticsData) => void;
}

// Full-screen Modal for deep reading
const MetricModal = ({ metric, isOpen, onClose, getSourceBadge }: {
  metric: MetricValue | null;
  isOpen: boolean;
  onClose: () => void;
  getSourceBadge: (s: string) => React.ReactNode;
}) => {
  if (!isOpen || !metric) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 md:p-10">
      <div
        className="absolute inset-0 bg-[#eaf4f7]/80 backdrop-blur-sm animate-in fade-in duration-300"
        onClick={onClose}
      />
      <div className="relative w-full max-w-3xl bg-white border border-[#1762C7]/20 rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-in slide-in-from-bottom-8 duration-300">
        <div className="p-6 border-b border-[#1762C7]/10 flex items-center justify-between bg-gradient-to-r from-[#1762C7]/5 to-transparent">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-bold text-gray-600 uppercase tracking-[0.2em] font-mono">{metric.name}</h3>
              {getSourceBadge(metric.source)}
            </div>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Comprehensive Analyst Summary</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-xl text-gray-600 hover:text-gray-900 transition-all hover:rotate-90"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-8 overflow-y-auto custom-scrollbar flex-1 max-h-[70vh]">
          <div className="text-gray-900 text-base leading-loose font-sans whitespace-pre-line space-y-4">
            {typeof metric.value === 'string' ? (
              metric.value.split('\n\n').map((para, i) => (
                <p key={i} className="mb-4">{para}</p>
              ))
            ) : (
              <span className="text-3xl font-bold text-[#1762C7]">{metric.value}</span>
            )}
          </div>
        </div>

        <div className="p-4 bg-white/[0.02] border-t border-[#1762C7]/10 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[10px] text-gray-500 font-mono">
            <ShieldCheck className="w-4 h-4 text-emerald-500/50" />
            VERIFIED BY AI TERMINAL
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-[#1762C7]/10 hover:bg-[#1762C7]/20 text-[#1762C7] border border-[#1762C7]/20 rounded-xl text-xs font-bold transition-all"
          >
            CLOSE PREVIEW
          </button>
        </div>
      </div>
    </div>
  );
};

// Compact Card with "Read More" for long textual insights
const ExpandableMetricCard = ({ metric, getSourceBadge, getConfidenceBar, onOpenDetail }: {
  metric: MetricValue;
  getSourceBadge: (s: string) => React.ReactNode;
  getConfidenceBar: (c: number) => React.ReactNode;
  onOpenDetail: (m: MetricValue) => void;
}) => {
  const isLongText = typeof metric.value === 'string' && metric.value.length > 150;

  return (
    <div className="fundamental-card flex flex-col h-full group">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <h4 className="text-[11px] font-bold text-gray-600 uppercase tracking-wider">{metric.name}</h4>
          <Info className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        {getSourceBadge(metric.source)}
      </div>

      <div className="flex-1">
        {metric.value !== null && metric.value !== undefined ? (
          <div className="text-sm text-gray-900 leading-relaxed font-sans">
            {typeof metric.value === 'number' ? (
              <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                {metric.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </span>
            ) : (
              <div className="relative">
                <p className={`${isLongText ? 'line-clamp-3' : ''} text-gray-300 leading-relaxed`}>
                  {metric.value}
                </p>
                {isLongText && (
                  <button
                    onClick={() => onOpenDetail(metric)}
                    className="mt-2 flex items-center gap-1 text-[10px] font-bold text-[#1762C7] hover:text-[#1FA8A6] transition-colors uppercase tracking-tight group-hover:translate-x-1 duration-300"
                  >
                    <ChevronDown className="w-3 h-3" /> Read Summary
                  </button>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2 py-2 opacity-50">
            <div className="h-2 w-full bg-gray-800 rounded animate-pulse" />
            <div className="h-2 w-2/3 bg-gray-800 rounded animate-pulse" />
            <p className="text-[10px] text-gray-600 italic font-sans mt-1">Awaiting secondary extraction...</p>
          </div>
        )}
      </div>

      {metric.confidence > 0 && (
        <div className="mt-4 pt-3 border-t border-[#1762C7]/10 space-y-1">
          <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono text-[9px]">
            <span>CONFIDENCE</span>
            <span className={metric.confidence > 0.7 ? 'text-emerald-400' : 'text-amber-400'}>
              {(metric.confidence * 100).toFixed(0)}%
            </span>
          </div>
          {getConfidenceBar(metric.confidence)}
        </div>
      )}
    </div>
  );
};

export default function AnalysisTab({ companyId, companyName, tickerSymbol, cachedData, onDataLoaded }: AnalysisTabProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(cachedData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('market');
  const [selectedMetric, setSelectedMetric] = useState<MetricValue | null>(null);

  useEffect(() => {
    // Use cached data if available, otherwise load fresh
    if (cachedData) {
      setAnalyticsData(cachedData);
    } else if (companyId && companyName) {
      loadAnalytics();
    }
  }, [companyId, companyName, tickerSymbol, cachedData]);

  const loadAnalytics = async (forceRefresh = false) => {
    if (!companyId || !companyName) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.generateAnalytics(companyId, companyName, tickerSymbol, forceRefresh);
      setAnalyticsData(data);
      // Cache the data in parent component
      if (onDataLoaded) {
        onDataLoaded(data);
      }
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      let errorMessage = 'Failed to load analytics. Please try again.';
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'Analysis pipeline timed out. The report is very large. Try clicking Restart Pipeline.';
      } else if (err.code === 'ERR_NETWORK') {
        errorMessage = 'Network connectivity issue. Check if backend is active.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'market': return <TrendingUp className="w-4 h-4" />;
      case 'performance': return <BarChart3 className="w-4 h-4" />;
      case 'valuation': return <Target className="w-4 h-4" />;
      case 'company_info': return <Building2 className="w-4 h-4" />;
      case 'business': return <Layers className="w-4 h-4" />;
      case 'risk': return <ShieldCheck className="w-4 h-4" />;
      default: return <BarChart3 className="w-4 h-4" />;
    }
  };

  const getCategoryTitle = (category: string) => {
    switch (category) {
      case 'market': return 'Market & Trading';
      case 'performance': return 'Financial Performance';
      case 'valuation': return 'Valuation & Strategy';
      case 'company_info': return 'Company Profile';
      case 'business': return 'Business & Markets';
      case 'risk': return 'Risk & Governance';
      default: return category.replace('_', ' ').toUpperCase();
    }
  };

  const getSourceBadge = (source: string) => {
    const badges: { [key: string]: { border: string; text: string; label: string } } = {
      'annual_report': { border: 'border-[#1762C7]/30', text: 'text-[#1762C7]', label: 'ANNUAL REPORT' },
      'yfinance': { border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'REAL-TIME DATA' },
      'not_found': { border: 'border-gray-700', text: 'text-gray-600', label: 'MISSING' },
    };
    const badge = badges[source] || badges['not_found'];
    return (
      <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${badge.border} ${badge.text} tracking-wider`}>
        {badge.label}
      </span>
    );
  };

  const getConfidenceBar = (confidence: number) => {
    const width = `${confidence * 100}%`;
    const color = confidence > 0.7 ? 'bg-emerald-500' : confidence > 0.4 ? 'bg-amber-500' : 'bg-rose-500';
    return (
      <div className="w-full bg-gray-800/50 rounded-full h-1 overflow-hidden shadow-inner">
        <div className={`h-full ${color} transition-all duration-500 shadow-[0_0_5px_rgba(16,185,129,0.3)]`} style={{ width }}></div>
      </div>
    );
  };

  // Top Ribbon Data
  const topMetrics = useMemo(() => {
    if (!analyticsData) return [];
    return [
      analyticsData.metrics.find(m => m.key === 'current_price'),
      analyticsData.metrics.find(m => m.key === 'pe_ratio'),
      analyticsData.metrics.find(m => m.key === 'eps'),
      analyticsData.metrics.find(m => m.key === 'pb_ratio'),
      analyticsData.metrics.find(m => m.key === 'peg_ratio'),
      analyticsData.metrics.find(m => m.key === 'roic'),
    ].filter(Boolean) as MetricValue[];
  }, [analyticsData]);

  if (!companyId || !companyName) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#eaf4f7]">
        <div className="w-20 h-20 rounded-2xl bg-cyan-500/5 border border-[#1762C7]/10 flex items-center justify-center mb-6">
          <Layers className="w-10 h-10 text-[#1762C7]/40" />
        </div>
        <h3 className="text-xl font-bold text-gray-300 mb-2">Initialize Analysis</h3>
        <p className="max-w-xs text-sm text-gray-500">Select a company profile to extract and visualize deep fundamental insights.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#eaf4f7] p-12">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-[#1762C7]/20 border-t-cyan-500 rounded-full animate-spin"></div>
          <Cpu className="w-6 h-6 text-[#1762C7] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
        </div>
        <h3 className="text-lg font-bold text-gray-900 mt-8 mb-2 tracking-tight">AI ANALYST PROCESSING</h3>
        <div className="flex flex-col items-center gap-1">
          <p className="text-xs text-[#1762C7] animate-pulse font-mono tracking-widest">PARALLEL RAG EXTRACTION ACTIVE</p>
          <p className="text-[10px] text-gray-600 mt-2 italic font-inter italic font-inter px-8 text-center max-w-sm">Comparing annual report disclosures with real-time market data to build intrinsic model...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#eaf4f7] p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-rose-500 mb-4" />
        <h3 className="text-lg font-bold text-gray-900 mb-2">Processing Exception</h3>
        <p className="text-sm text-gray-500 mb-6 max-w-sm font-inter leading-relaxed">{error}</p>
        <button onClick={() => loadAnalytics(true)} className="btn-primary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Restart Pipeline
        </button>
      </div>
    );
  }

  if (!analyticsData) return null;

  return (
    <div className="flex-1 overflow-hidden flex flex-col bg-[#eaf4f7]">
      {/* Top Professional Ribbon */}
      <div className="shrink-0 bg-white/40 backdrop-blur-xl border-b border-[#1762C7]/10 px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-bold text-gray-900 tracking-tight">{analyticsData.company_name}</h2>
              {analyticsData.ticker_symbol && (
                <span className="px-2 py-0.5 rounded bg-[#1762C7]/10 text-[#1762C7] border border-[#1762C7]/20 text-[10px] font-mono font-bold">
                  {analyticsData.ticker_symbol}
                </span>
              )}
            </div>
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em] font-mono">Fundamental Intelligence Terminal</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex gap-4 p-1.5 bg-white/5 rounded-xl border border-[#1762C7]/10">
              {topMetrics.map((m) => (
                <div key={m.key} className="px-4 py-1.5 border-r border-[#1762C7]/10 last:border-0">
                  <p className="text-[9px] text-gray-500 font-bold uppercase whitespace-nowrap">{m.name.split(' ')[0]}</p>
                  <p className="text-sm font-bold text-emerald-400 font-mono">
                    {typeof m.value === 'number' ? m.value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : m.value || '—'}
                  </p>
                </div>
              ))}
            </div>
            <button
              onClick={() => loadAnalytics(true)}
              className="p-2.5 rounded-xl bg-[#1762C7]/10 hover:bg-[#1762C7]/20 text-[#1762C7] border border-[#1762C7]/20 transition-all hover:scale-105 active:scale-95 group shadow-lg"
              title="Full Deep Refresh"
            >
              <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-700" />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="shrink-0 bg-[#eaf4f7] border-b border-[#1762C7]/10 px-6 pt-2">
        <div className="max-w-[1600px] mx-auto flex gap-6">
          {Object.keys(analyticsData.categories).map((category) => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`pb-3 px-1 flex items-center gap-2 border-b-2 transition-all text-[11px] font-bold uppercase tracking-widest ${activeCategory === category
                ? 'border-[#1762C7] text-[#1762C7]'
                : 'border-transparent text-gray-500 hover:text-gray-300'
                }`}
            >
              {getCategoryIcon(category)}
              {getCategoryTitle(category)}
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-mono font-bold ${activeCategory === category ? 'bg-[#1762C7]/20 text-[#1762C7]' : 'bg-white/5 text-gray-600'}`}>
                {analyticsData.categories[category as keyof typeof analyticsData.categories]?.length || 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Analysis Scroller */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-[#eaf4f7] space-y-8">
        <div className="max-w-[1600px] mx-auto">

          {/* Visualization Section */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 mb-8">
            {/* Radar Comparison Card */}
            <div className="xl:col-span-4 bg-white/30 border border-[#1762C7]/10 rounded-2xl p-6 shadow-sm overflow-hidden relative group">
              <div className="flex items-center justify-between mb-8 text-[10px] font-bold text-gray-600 uppercase tracking-widest">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-[#1762C7]" /> Fundamental Radar
                </div>
              </div>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={
                    analyticsData.categories[activeCategory as keyof typeof analyticsData.categories]?.slice(0, 6).map(m => ({
                      metric: m.name.split(' ').slice(0, 2).join(' '),
                      score: (m.confidence || 0.5) * 100,
                      full: 100
                    })) || []
                  }>
                    <PolarGrid stroke="#1E293B" strokeWidth={0.5} />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#64748B', fontSize: 9, fontWeight: 700 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                      name="Confidence"
                      dataKey="score"
                      stroke="#06b6d4"
                      strokeWidth={2}
                      fill="#06b6d4"
                      fillOpacity={0.15}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Business Breakdown Card (Geographical/Product) - Only show if data exists */}
            {(analyticsData.metrics.some(m => m.key === 'geographical_revenue_share') ||
              analyticsData.metrics.some(m => m.key === 'revenue_share_by_product')) && (
                <div className="xl:col-span-8 bg-white/30 border border-[#1762C7]/10 rounded-2xl p-6 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between mb-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                      <div className="flex items-center gap-2 text-emerald-400/80">
                        <TrendingUp className="w-4 h-4" /> Geographical Split
                      </div>
                    </div>
                    <div className="flex-1 rounded-xl bg-white/[0.02] border border-[#1762C7]/10 p-4 flex items-center justify-center text-center">
                      {analyticsData.metrics.find(m => m.key === 'geographical_revenue_share')?.value ? (
                        <div className="space-y-2">
                          <p className="text-xs text-gray-300 leading-relaxed italic line-clamp-4">
                            {String(analyticsData.metrics.find(m => m.key === 'geographical_revenue_share')?.value)}
                          </p>
                          <span className="text-[10px] text-[#1762C7]/50 uppercase font-mono tracking-tighter">AI Derived Breakdown</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center opacity-30">
                          <BarChart className="w-8 h-8 mb-2" />
                          <span className="text-[9px]">NO GEO DATA</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <div className="flex items-center justify-between mb-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                      <div className="flex items-center gap-2 text-blue-400/80">
                        <Layers className="w-4 h-4" /> Product Mix Analysis
                      </div>
                    </div>
                    <div className="flex-1 rounded-xl bg-white/[0.02] border border-[#1762C7]/10 p-4 flex items-center justify-center text-center">
                      {analyticsData.metrics.find(m => m.key === 'revenue_share_by_product')?.value ? (
                        <div className="space-y-2">
                          <p className="text-xs text-gray-300 leading-relaxed italic line-clamp-4">
                            {String(analyticsData.metrics.find(m => m.key === 'revenue_share_by_product')?.value)}
                          </p>
                          <span className="text-[10px] text-[#1762C7]/50 uppercase font-mono tracking-tighter">Segmental Intelligence</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center opacity-30">
                          <PieChart className="w-8 h-8 mb-2" />
                          <span className="text-[9px]">NO PRODUCT DATA</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
          </div>

          {/* High-Density Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-5">
            {analyticsData.categories[activeCategory as keyof typeof analyticsData.categories]?.map((metric) => (
              <ExpandableMetricCard
                key={metric.key}
                metric={metric}
                getSourceBadge={getSourceBadge}
                getConfidenceBar={getConfidenceBar}
                onOpenDetail={setSelectedMetric}
              />
            ))}
          </div>

          {analyticsData.categories[activeCategory as keyof typeof analyticsData.categories]?.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-600 bg-white/5 rounded-3xl border border-dashed border-[#1762C7]/10">
              <AlertTriangle className="w-8 h-8 mb-4 opacity-50" />
              <p className="text-xs font-mono font-bold tracking-widest uppercase">Insufficient dataset for deep analysis</p>
              <p className="text-[10px] mt-2 italic">Try a deep refresh or verify document upload status.</p>
            </div>
          )}

          {/* Model Note */}
          <div className="mt-12 flex items-center justify-center gap-8 border-t border-[#1762C7]/10 pt-8">
            <div className="flex items-center gap-2 text-[10px] font-bold text-gray-600 font-mono tracking-widest">
              <ShieldCheck className="w-4 h-4 text-emerald-500/50" />
              VERIFIED BY PHI-4 RAG
            </div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-gray-600 font-mono tracking-widest">
              <RefreshCw className="w-4 h-4 text-[#1762C7]/50" />
              AUTO-UPDATED {new Date(analyticsData.generated_at).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Metric Detail Modal */}
      <MetricModal
        metric={selectedMetric}
        isOpen={!!selectedMetric}
        onClose={() => setSelectedMetric(null)}
        getSourceBadge={getSourceBadge}
      />
    </div>
  );
}
