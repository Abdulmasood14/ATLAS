'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { Layers, Building2, Briefcase, ChevronRight, Loader2, Sparkles, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface DeepDiveData {
  company_id: string;
  company_name: string;
  detected_sector: string;
  questions: {
    general: string[];
    sector_specific: string[];
    business_specific: string[];
  };
  generated_at: string;
}

interface QuestionAnswer {
  question: string;
  answer: string | null;
  loading: boolean;
}

interface DeepDiveTabProps {
  companyId: string;
  companyName: string;
}

export default function DeepDiveTab({ companyId, companyName }: DeepDiveTabProps) {
  const [deepDiveData, setDeepDiveData] = useState<DeepDiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, QuestionAnswer>>({});

  useEffect(() => {
    loadQuestions();
  }, [companyId]);

  const loadQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/deep-dive/generate-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: companyId, company_name: companyName })
      });

      if (!response.ok) {
        throw new Error('Failed to generate questions');
      }

      const data = await response.json();
      setDeepDiveData(data);
    } catch (err: any) {
      console.error('Failed to load questions:', err);
      setError(err.message || 'Failed to load questions');
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionClick = async (question: string, category: string) => {
    // Toggle expand/collapse
    if (expandedQuestion === question) {
      setExpandedQuestion(null);
      return;
    }

    setExpandedQuestion(question);

    // Check if already answered
    if (questionAnswers[question]?.answer) {
      return;
    }

    // Mark as loading
    setQuestionAnswers(prev => ({
      ...prev,
      [question]: { question, answer: null, loading: true }
    }));

    // Fetch answer from RAG system
    try {
      // Create a temporary session for deep dive questions
      const sessionResponse = await apiClient.createSession(companyId, companyName);
      const response = await apiClient.sendQuery(question, sessionResponse.session_id, companyId);

      setQuestionAnswers(prev => ({
        ...prev,
        [question]: { question, answer: response.answer, loading: false }
      }));
    } catch (error: any) {
      console.error('Failed to get answer:', error);
      setQuestionAnswers(prev => ({
        ...prev,
        [question]: {
          question,
          answer: 'Failed to load answer. Please try again.',
          loading: false
        }
      }));
    }
  };

  const renderQuestionSection = (
    title: string,
    subtitle: string,
    icon: React.ReactNode,
    iconBg: string,
    questions: string[],
    category: string
  ) => (
    <div className="space-y-4">
      {/* Section Header */}
      <div className="flex items-center gap-4 mb-5">
        <div className={`w-12 h-12 rounded-xl ${iconBg} border border-[#1762C7]/30 flex items-center justify-center shadow-lg`}>
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{subtitle}</p>
        </div>
      </div>

      {/* Questions Grid */}
      <div className="space-y-3">
        {questions.map((question, idx) => {
          const isExpanded = expandedQuestion === question;
          const answerData = questionAnswers[question];

          return (
            <div
              key={idx}
              className={`border rounded-xl overflow-hidden transition-all duration-300 bg-white ${
                isExpanded
                  ? 'border-[#1762C7]/50 shadow-lg'
                  : 'border-[#1762C7]/20 hover:border-[#1762C7]/40 hover:shadow-md'
              }`}
            >
              {/* Question Button */}
              <button
                onClick={() => handleQuestionClick(question, category)}
                className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-[#1762C7]/5 transition-all group"
              >
                <div className="flex-1 flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                    answerData?.answer
                      ? 'bg-green-500/20 border border-green-500/30'
                      : 'bg-[#1762C7]/10 border border-[#1762C7]/20 group-hover:bg-[#1762C7]/20'
                  }`}>
                    {answerData?.answer ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <span className="text-xs font-bold text-[#1762C7]">{idx + 1}</span>
                    )}
                  </div>
                  <span className="text-sm text-gray-900 font-medium leading-relaxed">{question}</span>
                </div>
                <ChevronRight
                  className={`w-5 h-5 text-[#1762C7] transition-all flex-shrink-0 ml-3 ${
                    isExpanded ? 'rotate-90 text-[#1FA8A6]' : 'group-hover:translate-x-1'
                  }`}
                />
              </button>

              {/* Answer Panel */}
              {isExpanded && (
                <div className="px-5 py-5 bg-[#eaf4f7]/50 border-t border-[#1762C7]/20 animate-in slide-in-from-top-3 duration-300">
                  {answerData?.loading ? (
                    <div className="flex items-center gap-3 text-[#1762C7] py-8 justify-center">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span className="text-sm font-medium">Analyzing document and generating answer...</span>
                    </div>
                  ) : answerData?.answer ? (
                    <div className="prose prose-sm max-w-none markdown-answer">
                      <div className="text-sm text-gray-700 leading-relaxed bg-white rounded-lg p-5 border border-[#1762C7]/10 shadow-sm">
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
                          }}
                        >
                          {answerData.answer}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4">
          <Loader2 className="w-16 h-16 text-[#1762C7] animate-spin mx-auto" />
          <div>
            <p className="text-lg font-semibold text-gray-900">Generating intelligent questions...</p>
            <p className="text-sm text-gray-600 mt-1">Analyzing {companyName}'s annual report</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4 max-w-md">
          <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto">
            <span className="text-3xl">⚠️</span>
          </div>
          <div>
            <h3 className="text-xl font-bold text-red-600 mb-2">Failed to Load Questions</h3>
            <p className="text-sm text-gray-600">{error}</p>
          </div>
          <button
            onClick={loadQuestions}
            className="px-6 py-3 bg-white hover:shadow-lg border border-[#1762C7]/30 rounded-lg text-[#1762C7] font-medium transition-all"
            style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}
          >
            <span className="text-white">Try Again</span>
          </button>
        </div>
      </div>
    );
  }

  if (!deepDiveData) return null;

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-10">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-4 mb-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg"
                 style={{background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'}}>
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Deep Dive Analysis</h1>
              <p className="text-gray-600 mt-1">
                Explore key insights through curated questions about{' '}
                <span className="text-[#1762C7] font-semibold">{companyName}</span>
              </p>
            </div>
          </div>

          {/* Sector Badge */}
          <div className="flex items-center gap-2 mt-4">
            <div className="px-4 py-2 bg-purple-500/10 border border-purple-500/30 rounded-full">
              <span className="text-xs font-bold text-purple-700 uppercase tracking-wider">
                Detected Sector: {deepDiveData.detected_sector}
              </span>
            </div>
            <div className="px-4 py-2 bg-[#1762C7]/10 border border-[#1762C7]/30 rounded-full">
              <span className="text-xs font-bold text-[#1762C7] uppercase tracking-wider">
                {deepDiveData.questions.general.length + deepDiveData.questions.sector_specific.length + deepDiveData.questions.business_specific.length} Questions Generated
              </span>
            </div>
          </div>
        </div>

        {/* General Questions */}
        {renderQuestionSection(
          'General Questions',
          'Universal questions applicable to all companies',
          <Layers className="w-6 h-6 text-[#1762C7]" />,
          'bg-gradient-to-br from-[#1762C7]/10 to-[#1FA8A6]/10',
          deepDiveData.questions.general,
          'general'
        )}

        <div className="h-px bg-gradient-to-r from-transparent via-[#1762C7]/30 to-transparent my-8"></div>

        {/* Sector-Specific Questions */}
        {renderQuestionSection(
          'Sector-Specific Questions',
          `Tailored for ${deepDiveData.detected_sector} industry`,
          <Building2 className="w-6 h-6 text-purple-600" />,
          'bg-gradient-to-br from-purple-500/10 to-pink-500/10',
          deepDiveData.questions.sector_specific,
          'sector'
        )}

        <div className="h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent my-8"></div>

        {/* Business-Specific Questions */}
        {renderQuestionSection(
          'Business-Specific Questions',
          'Strategic and competitive analysis',
          <Briefcase className="w-6 h-6 text-emerald-600" />,
          'bg-gradient-to-br from-emerald-500/10 to-green-500/10',
          deepDiveData.questions.business_specific,
          'business'
        )}
      </div>
    </div>
  );
}
