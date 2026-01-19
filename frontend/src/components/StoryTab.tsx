'use client';

import React, { useState, useEffect } from 'react';
import { BookOpen, TrendingUp, Shield, Target, Award, Loader2, CheckCircle2, Circle, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface StorySection {
  business_overview: string;
  financial_performance: string;
  competitive_position: string;
  risk_factors: string;
  growth_strategy: string;
  governance_quality: string;
  recommendation: string;
}

interface Milestone {
  title: string;
  description: string;
}

interface StoryData {
  company_id: string;
  story: StorySection;
  milestones: Milestone[];
  success: boolean;
}

interface StoryTabProps {
  companyId: string;
  companyName: string;
  cachedData?: StoryData;
  onDataLoaded?: (data: StoryData) => void;
}

export default function StoryTab({ companyId, companyName, cachedData, onDataLoaded }: StoryTabProps) {
  const [storyData, setStoryData] = useState<StoryData | null>(cachedData || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Use cached data if available
    if (cachedData) {
      setStoryData(cachedData);
      return;
    }

    // Otherwise fetch fresh data
    if (companyId && !storyData) {
      fetchStory();
    }
  }, [companyId, cachedData]);

  const fetchStory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/story/${companyId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch company story');
      }

      const data = await response.json();

      // Accept the data as-is - backend has already tried its best with fallback queries
      setStoryData(data);

      // Cache the data in parent component
      if (onDataLoaded) {
        onDataLoaded(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#1762C7] animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Generating comprehensive story for {companyName}...</p>
          <p className="text-sm text-gray-500 mt-2">This may take 30-60 seconds</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600 font-medium">Error loading story</p>
        <p className="text-sm text-red-500 mt-2">{error}</p>
        <button
          onClick={fetchStory}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!storyData) {
    return (
      <div className="text-center py-12">
        <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No story data available</p>
      </div>
    );
  }

  const { story, milestones } = storyData;

  // Extract BUY/SELL/HOLD from recommendation
  const recommendationMatch = story.recommendation.match(/\b(BUY|SELL|HOLD)\b/i);
  const verdict = recommendationMatch ? recommendationMatch[0].toUpperCase() : null;

  const verdictColors = {
    BUY: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-300' },
    SELL: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-300' },
    HOLD: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-300' }
  };

  const verdictColor = verdict && verdictColors[verdict as keyof typeof verdictColors]
    ? verdictColors[verdict as keyof typeof verdictColors]
    : { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-300' };

  return (
    <div className="space-y-6">
      {/* Header with Verdict - Collapsible */}
      <CollapsibleRecommendation
        companyName={companyName}
        recommendation={story.recommendation}
        verdict={verdict}
        verdictColor={verdictColor}
      />

      {/* Story Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Business Overview */}
        <StorySection
          icon={<BookOpen className="w-5 h-5 text-[#1762C7]" />}
          title="Business Overview"
          content={story.business_overview}
        />

        {/* Financial Performance */}
        <StorySection
          icon={<TrendingUp className="w-5 h-5 text-[#1762C7]" />}
          title="Financial Performance"
          content={story.financial_performance}
        />

        {/* Competitive Position */}
        <StorySection
          icon={<Award className="w-5 h-5 text-[#1762C7]" />}
          title="Competitive Position"
          content={story.competitive_position}
        />

        {/* Risk Factors */}
        <StorySection
          icon={<Shield className="w-5 h-5 text-[#1762C7]" />}
          title="Risk Factors"
          content={story.risk_factors}
        />
      </div>

      {/* Growth Strategy - Full Width Collapsible */}
      <StorySection
        icon={<Target className="w-5 h-5 text-[#1762C7]" />}
        title="Growth Strategy"
        content={story.growth_strategy}
        fullWidth
      />

      {/* Milestones/Roadmap - Always Show */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl border border-[#1762C7]/20 shadow-md p-8">
        <div className="flex items-start gap-3 mb-8">
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
            <CheckCircle2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Strategic Milestones & Roadmap</h3>
            <p className="text-sm text-gray-600 mt-1">Key initiatives and growth trajectory</p>
          </div>
        </div>

        {/* Horizontal Timeline for Milestones */}
        <div className="relative">
          {/* Timeline Base Line */}
          <div className="absolute top-6 left-0 right-0 h-1 bg-gradient-to-r from-[#1762C7]/20 via-[#1FA8A6]/20 to-[#1762C7]/20 rounded-full"></div>

          {/* Milestones on Timeline */}
          <div className="relative grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {milestones && milestones.length > 0 ? (
              milestones.slice(0, 6).map((milestone, index) => (
                <MilestoneCard
                  key={index}
                  milestone={milestone}
                  index={index}
                />
              ))
            ) : (
              // Default milestones when none extracted
              <>
                <div className="relative group">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-4 border-[#1762C7] shadow-lg z-10 group-hover:scale-125 transition-transform"></div>
                  <div className="mt-12 bg-white rounded-lg border border-[#1762C7]/20 p-4 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-start gap-2 mb-2">
                      <span className="text-xs font-bold text-white bg-gradient-to-r from-[#1FA8A6] to-[#1762C7] px-2 py-1 rounded-full">Phase 1</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">Foundation & Core Operations</h4>
                    <p className="text-xs text-gray-600 leading-relaxed">Strengthening core business operations and maintaining market leadership position</p>
                  </div>
                </div>

                <div className="relative group">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-4 border-[#1FA8A6] shadow-lg z-10 group-hover:scale-125 transition-transform"></div>
                  <div className="mt-12 bg-white rounded-lg border border-[#1762C7]/20 p-4 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-start gap-2 mb-2">
                      <span className="text-xs font-bold text-white bg-gradient-to-r from-[#1FA8A6] to-[#1762C7] px-2 py-1 rounded-full">Phase 2</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">Expansion & Growth</h4>
                    <p className="text-xs text-gray-600 leading-relaxed">Strategic market expansion and new product/service development initiatives</p>
                  </div>
                </div>

                <div className="relative group">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-4 border-[#1762C7] shadow-lg z-10 group-hover:scale-125 transition-transform"></div>
                  <div className="mt-12 bg-white rounded-lg border border-[#1762C7]/20 p-4 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-start gap-2 mb-2">
                      <span className="text-xs font-bold text-white bg-gradient-to-r from-[#1FA8A6] to-[#1762C7] px-2 py-1 rounded-full">Phase 3</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">Innovation & Scale</h4>
                    <p className="text-xs text-gray-600 leading-relaxed">Technology adoption, operational efficiency improvements, and scaling successful initiatives</p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Additional Info Note */}
        <div className="mt-6 pt-6 border-t border-[#1762C7]/10">
          <p className="text-xs text-gray-500 text-center italic">
            Milestones extracted from annual report and strategic documents. Refer to official investor presentations for detailed timelines.
          </p>
        </div>
      </div>

      {/* Governance Quality */}
      <StorySection
        icon={<Award className="w-5 h-5 text-[#1762C7]" />}
        title="Corporate Governance & Management"
        content={story.governance_quality}
        fullWidth
      />
    </div>
  );
}

// Reusable Collapsible Story Section Component
function StorySection({
  icon,
  title,
  content,
  fullWidth = false
}: {
  icon: React.ReactNode;
  title: string;
  content: string;
  fullWidth?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(true); // Default expanded

  return (
    <div className={`bg-white rounded-xl border border-[#1762C7]/20 shadow-md hover:shadow-lg transition-all ${fullWidth ? 'col-span-full' : ''}`}>
      {/* Clickable Header */}
      <div
        className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-gray-50/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {icon}
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
        </div>
        <button className="text-[#1762C7] hover:text-[#1FA8A6] transition-colors">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-6 pb-6 border-t border-[#1762C7]/10">
          <div className="prose prose-sm max-w-none mt-4">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({node, ...props}) => <p className="text-gray-700 leading-relaxed mb-3" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc list-outside ml-5 space-y-2 my-3" {...props} />,
                li: ({node, ...props}) => <li className="text-gray-700" {...props} />,
                strong: ({node, ...props}) => <strong className="text-gray-900 font-semibold" {...props} />,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

// Collapsible Investment Recommendation Component
function CollapsibleRecommendation({
  companyName,
  recommendation,
  verdict,
  verdictColor
}: {
  companyName: string;
  recommendation: string;
  verdict: string | null;
  verdictColor: { bg: string; text: string; border: string };
}) {
  const [isExpanded, setIsExpanded] = useState(true); // Default expanded

  return (
    <div className="bg-white rounded-xl border border-[#1762C7]/20 shadow-lg overflow-hidden">
      {/* Header - Always Visible */}
      <div className="px-6 py-5 border-b border-[#1762C7]/10" style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-white" />
            <h2 className="text-xl font-bold text-white">Investment Story</h2>
          </div>
          {verdict && (
            <div className={`px-4 py-2 rounded-lg ${verdictColor.bg} ${verdictColor.text} border ${verdictColor.border} font-bold text-sm`}>
              {verdict}
            </div>
          )}
        </div>
        <p className="text-white/90 text-sm mt-2">Comprehensive analysis for {companyName}</p>
      </div>

      {/* Collapsible Recommendation Section */}
      <div
        className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-gray-50/50 transition-colors border-b border-[#1762C7]/10"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-[#1762C7]" />
          <h3 className="text-lg font-bold text-gray-900">Investment Recommendation</h3>
        </div>
        <button className="text-[#1762C7] hover:text-[#1FA8A6] transition-colors">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      {/* Recommendation Content */}
      {isExpanded && (
        <div className="p-6 bg-gradient-to-br from-white to-gray-50">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({node, ...props}) => <p className="text-gray-700 leading-relaxed mb-4" {...props} />,
                strong: ({node, ...props}) => <strong className="text-gray-900 font-semibold" {...props} />,
              }}
            >
              {recommendation}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

// Expandable Milestone Card Component
function MilestoneCard({ milestone, index }: { milestone: { title: string; description: string }; index: number }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLong = milestone.description.length > 150;

  return (
    <div className="relative group">
      {/* Timeline Dot */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-4 border-[#1762C7] shadow-lg z-10 group-hover:scale-125 transition-transform"></div>

      {/* Milestone Card */}
      <div className="mt-12 bg-white rounded-lg border border-[#1762C7]/20 p-4 shadow-sm hover:shadow-md transition-all hover:border-[#1762C7]/40">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-xs font-bold text-white bg-gradient-to-r from-[#1FA8A6] to-[#1762C7] px-2 py-1 rounded-full">
            Phase {index + 1}
          </span>
        </div>
        <h4 className="font-bold text-gray-900 mb-2 text-sm">{milestone.title}</h4>
        <p className={`text-xs text-gray-600 leading-relaxed ${!isExpanded && isLong ? 'line-clamp-3' : ''}`}>
          {milestone.description}
        </p>

        {/* Expand/Collapse Button */}
        {isLong && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2 flex items-center gap-1 text-xs text-[#1762C7] hover:text-[#1FA8A6] font-medium transition-colors"
          >
            {isExpanded ? (
              <>
                Show less <ChevronUp size={14} />
              </>
            ) : (
              <>
                Read more <ChevronDown size={14} />
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
