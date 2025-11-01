import React from 'react';
import { Download, Share2, RefreshCw, Star } from 'lucide-react';
import ScoreCard from './ScoreCard';

interface ResultsDashboardProps {
  url: string;
  overallScore: number;
  scores: {
    leadMagnet: number;
    valueProposition: number;
    callToAction: number;
    formOptimization: number;
    trustSignals: number;
    mobileResponsive: number;
    loadSpeed: number;
    contentQuality: number;
  };
  onNewAnalysis: () => void;
}

export default function ResultsDashboard({ url, overallScore, scores, onNewAnalysis }: ResultsDashboardProps) {
  const getOverallGrade = () => {
    if (overallScore >= 90) return { grade: 'A+', color: 'text-green-600', bg: 'bg-green-100' };
    if (overallScore >= 80) return { grade: 'A', color: 'text-green-600', bg: 'bg-green-100' };
    if (overallScore >= 70) return { grade: 'B', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (overallScore >= 60) return { grade: 'C', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { grade: 'D', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const grade = getOverallGrade();

  const scoreCards = [
    {
      title: 'Lead Magnet Presence',
      score: scores.leadMagnet,
      maxScore: 100,
      description: 'Visibility and effectiveness of your lead magnets',
      trend: scores.leadMagnet >= 70 ? 'up' : scores.leadMagnet >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Value Proposition',
      score: scores.valueProposition,
      maxScore: 100,
      description: 'Clarity and compelling nature of your value proposition',
      trend: scores.valueProposition >= 70 ? 'up' : scores.valueProposition >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Call-to-Action',
      score: scores.callToAction,
      maxScore: 100,
      description: 'Effectiveness and placement of your CTAs',
      trend: scores.callToAction >= 70 ? 'up' : scores.callToAction >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Form Optimization',
      score: scores.formOptimization,
      maxScore: 100,
      description: 'User-friendliness and conversion optimization of forms',
      trend: scores.formOptimization >= 70 ? 'up' : scores.formOptimization >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Trust Signals',
      score: scores.trustSignals,
      maxScore: 100,
      description: 'Presence of testimonials, reviews, and credibility indicators',
      trend: scores.trustSignals >= 70 ? 'up' : scores.trustSignals >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Mobile Responsive',
      score: scores.mobileResponsive,
      maxScore: 100,
      description: 'Mobile-friendliness and responsive design quality',
      trend: scores.mobileResponsive >= 70 ? 'up' : scores.mobileResponsive >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Load Speed',
      score: scores.loadSpeed,
      maxScore: 100,
      description: 'Page loading performance and optimization',
      trend: scores.loadSpeed >= 70 ? 'up' : scores.loadSpeed >= 40 ? 'neutral' : 'down'
    },
    {
      title: 'Content Quality',
      score: scores.contentQuality,
      maxScore: 100,
      description: 'Relevance, quality, and engagement of your content',
      trend: scores.contentQuality >= 70 ? 'up' : scores.contentQuality >= 40 ? 'neutral' : 'down'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="mb-6 md:mb-0">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analysis Complete</h2>
            <p className="text-gray-600">Results for: <span className="font-medium">{url}</span></p>
          </div>
          <div className="flex items-center space-x-4">
            <button className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              <Download className="w-4 h-4" />
              <span>Export PDF</span>
            </button>
            <button className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              <Share2 className="w-4 h-4" />
              <span>Share</span>
            </button>
            <button 
              onClick={onNewAnalysis}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>New Analysis</span>
            </button>
          </div>
        </div>
      </div>

      {/* Overall Score */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full text-3xl font-bold mb-4 ${grade.bg} ${grade.color}`}>
            {grade.grade}
          </div>
          <h3 className="text-3xl font-bold text-gray-900 mb-2">Overall Score: {overallScore}/100</h3>
          <p className="text-gray-600 mb-6">Your website's lead generation effectiveness</p>
          <div className="max-w-lg mx-auto">
            <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-1000"
                style={{ width: `${overallScore}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
              <Star className="w-4 h-4 text-yellow-500" />
              <span>Based on 8 key performance indicators</span>
            </div>
          </div>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
        {scoreCards.map((card, index) => (
          <ScoreCard
            key={index}
            title={card.title}
            score={card.score}
            maxScore={card.maxScore}
            description={card.description}
            trend={card.trend as 'up' | 'down' | 'neutral'}
          />
        ))}
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Actionable Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-red-700 mb-2">High Priority</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Add prominent lead magnets above the fold</li>
                <li>• Optimize form fields to reduce friction</li>
                <li>• Improve mobile responsiveness</li>
              </ul>
            </div>
            <div className="border-l-4 border-yellow-500 pl-4">
              <h4 className="font-semibold text-yellow-700 mb-2">Medium Priority</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Add customer testimonials and reviews</li>
                <li>• Strengthen value proposition messaging</li>
                <li>• Optimize page loading speed</li>
              </ul>
            </div>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-green-500 pl-4">
              <h4 className="font-semibold text-green-700 mb-2">Low Priority</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Enhance content quality and relevance</li>
                <li>• Add more trust signals and certifications</li>
                <li>• Improve call-to-action button design</li>
              </ul>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-700 mb-2">Pro Tip</h4>
              <p className="text-sm text-blue-600">
                Focus on implementing high-priority recommendations first for maximum impact on your conversion rates.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}