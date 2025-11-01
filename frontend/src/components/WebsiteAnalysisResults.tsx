import React from 'react';
import { Download, Share2, RefreshCw, Star, TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { AnalysisResponse } from '../services/analysisService';
import { exportAnalysisReport } from '../utils/reportExporter';

interface WebsiteAnalysisResultsProps {
  result: AnalysisResponse;
  onNewAnalysis: () => void;
}

export default function WebsiteAnalysisResults({ result, onNewAnalysis }: WebsiteAnalysisResultsProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getScoreGradient = (score: number) => {
    if (score >= 80) return 'bg-gradient-to-r from-green-500 to-green-300';
    if (score >= 60) return 'bg-gradient-to-r from-yellow-500 to-yellow-300';
    return 'bg-gradient-to-r from-red-500 to-red-300';
  };

  const getGrade = (score: number) => {
    if (score >= 90) return 'A+';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B';
    if (score >= 60) return 'C';
    if (score >= 50) return 'D';
    return 'F';
  };

  const getTrendIcon = (score: number) => {
    if (score >= 80) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (score >= 60) return <Minus className="w-4 h-4 text-gray-400" />;
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const renderSummaryContent = (summary: string) => {
    const normalized = summary.replace(/\r/g, '').trim();

    if (!normalized) {
      return <p className="text-gray-500">Summary not available.</p>;
    }

    const sanitizeInlineFormatting = (text: string) =>
      text
        .replace(/(\*\*|__)(.*?)\1/g, '$2')
        .replace(/(\*|_)(.*?)\1/g, '$2')
        .replace(/`([^`]*)`/g, '$1')
        .replace(/~~(.*?)~~/g, '$1')
        .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
        .replace(/[\*`_]/g, '')
        .replace(/\s+/g, ' ')
        .trim();

    const lines = normalized.split('\n').map((line) => line.trim());
    const bulletRegex = /^[\-\*•\u2022]/;
    const orderedRegex = /^\d+[\.)]/;

    type SectionType = 'paragraph' | 'unordered' | 'ordered';
    const sections: Array<{ type: SectionType; items: string[] }> = [];

    let currentType: SectionType | null = null;
    let buffer: string[] = [];

    const flushBuffer = () => {
      if (currentType && buffer.length > 0) {
        sections.push({ type: currentType, items: buffer });
      }
      currentType = null;
      buffer = [];
    };

    lines.forEach((line) => {
      if (!line) {
        flushBuffer();
        return;
      }

      if (orderedRegex.test(line)) {
        const item = sanitizeInlineFormatting(line.replace(orderedRegex, '').trim() || line);
        if (!item) {
          return;
        }
        if (currentType !== 'ordered') {
          flushBuffer();
          currentType = 'ordered';
        }
        buffer.push(item);
        return;
      }

      if (bulletRegex.test(line)) {
        const item = sanitizeInlineFormatting(line.replace(bulletRegex, '').trim() || line);
        if (!item) {
          return;
        }
        if (currentType !== 'unordered') {
          flushBuffer();
          currentType = 'unordered';
        }
        buffer.push(item);
        return;
      }

      const sanitized = sanitizeInlineFormatting(line);
      if (!sanitized) {
        return;
      }

      if (currentType !== 'paragraph') {
        flushBuffer();
        currentType = 'paragraph';
      }
      buffer.push(sanitized);
    });

    flushBuffer();

    return (
      <div className="space-y-3 text-gray-700 leading-relaxed">
        {sections.map((section, index) => {
          if (section.type === 'unordered') {
            return (
              <ul key={`summary-unordered-${index}`} className="list-disc pl-6 space-y-1">
                {section.items.map((item, itemIndex) => (
                  <li key={`summary-unordered-${index}-${itemIndex}`}>{item}</li>
                ))}
              </ul>
            );
          }

          if (section.type === 'ordered') {
            return (
              <ol key={`summary-ordered-${index}`} className="list-decimal pl-6 space-y-1">
                {section.items.map((item, itemIndex) => (
                  <li key={`summary-ordered-${index}-${itemIndex}`}>{item}</li>
                ))}
              </ol>
            );
          }

          return (
            <p key={`summary-paragraph-${index}`} className="text-gray-700">
              {section.items.join(' ')}
            </p>
          );
        })}
      </div>
    );
  };

  const handleExportReport = () => {
    exportAnalysisReport(result);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="mb-6 md:mb-0">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Analysis Complete</h2>
            <p className="text-gray-600 mb-2">Results for: <span className="font-medium text-blue-600">{result.metadata.requested_url}</span></p>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Pages Analyzed: <span className="font-medium">{result.metadata.pages_analyzed}</span></span>
              <span>Model: <span className="font-medium">{result.metadata.model_used}</span></span>
              <span>Duration: <span className="font-medium">{result.metadata.analysis_duration}s</span></span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleExportReport}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
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
          <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full text-3xl font-bold mb-4 ${getScoreBg(Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2))} ${getScoreColor(Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2))}`}>
            {getGrade(Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2))}
          </div>
          <h3 className="text-3xl font-bold text-gray-900 mb-2">Overall Score: {Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2)}/100</h3>
          <p className="text-gray-600 mb-6">Your website's overall performance rating</p>
          <div className="max-w-lg mx-auto">
            <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
              <div 
                className={`h-4 rounded-full transition-all duration-1000 ${getScoreGradient(Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2))}`}
                style={{ width: `${Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2)}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
              <Star className="w-4 h-4 text-yellow-500" />
              <span>Based on comprehensive analysis of {result.metadata.pages_analyzed} pages</span>
            </div>
          </div>
        </div>
      </div>

      {/* Score Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">SEO Score</h3>
            {getTrendIcon(result.seo_analysis.overall_score)}
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(result.seo_analysis.overall_score)} mb-2`}>
              {result.seo_analysis.overall_score}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-700 ${getScoreGradient(result.seo_analysis.overall_score)}`}
                style={{ width: `${result.seo_analysis.overall_score}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Search Engine Optimization</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Conversion Score</h3>
            {getTrendIcon(result.conversion_analysis.overall_score)}
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(result.conversion_analysis.overall_score)} mb-2`}>
              {result.conversion_analysis.overall_score}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-700 ${getScoreGradient(result.conversion_analysis.overall_score)}`}
                style={{ width: `${result.conversion_analysis.overall_score}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Lead Generation & Conversion</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Technical Score</h3>
            {getTrendIcon(result.seo_analysis.technical_seo)}
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(result.seo_analysis.technical_seo)} mb-2`}>
              {result.seo_analysis.technical_seo}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-700 ${getScoreGradient(result.seo_analysis.technical_seo)}`}
                style={{ width: `${result.seo_analysis.technical_seo}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Performance & Technical</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Content Score</h3>
            {getTrendIcon(result.seo_analysis.content_quality)}
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(result.seo_analysis.content_quality)} mb-2`}>
              {result.seo_analysis.content_quality}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-700 ${getScoreGradient(result.seo_analysis.content_quality)}`}
                style={{ width: `${result.seo_analysis.content_quality}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Content Quality & Relevance</p>
          </div>
        </div>
      </div>

      {/* Analysis Summary */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Analysis Summary</h3>
        <div className="bg-blue-50 p-6 rounded-xl">
          {renderSummaryContent(result.summary)}
        </div>
        <div className="mt-4 text-sm text-gray-500">
          Analysis completed on: {formatTimestamp(result.metadata.timestamp)}
        </div>
      </div>

      {(result.insights.seo_keyword_insights?.length || result.insights.conversion_highlights?.length) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {result.insights.seo_keyword_insights?.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">High-Value SEO Keywords</h3>
              <p className="text-sm text-gray-500 mb-4">
                Most frequently occurring themes discovered across titles, headings, and on-page copy.
              </p>
              <ul className="space-y-3">
                {result.insights.seo_keyword_insights.map((keyword, index) => (
                  <li key={index} className="flex items-start space-x-3">
                    <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold">
                      {index + 1}
                    </span>
                    <span className="text-sm text-gray-700">{keyword}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.insights.conversion_highlights?.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Conversion Highlights</h3>
              <p className="text-sm text-gray-500 mb-4">
                Key observations about CTAs, forms, and persuasive messaging captured during the crawl.
              </p>
              <ul className="space-y-3">
                {result.insights.conversion_highlights.map((item, index) => (
                  <li key={index} className="flex items-start space-x-3">
                    <span className="w-2 h-2 mt-2 rounded-full bg-amber-500" />
                    <span className="text-sm text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Pages Analyzed Snapshot */}
      {result.insights.pages_analyzed_details?.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Pages Analyzed Snapshot</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Page</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Title</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Word Count</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Load Time (s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.insights.pages_analyzed_details.map((page) => (
                  <tr key={page.url} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-blue-600 truncate max-w-xs" title={page.url}>{page.url}</td>
                    <td className="px-4 py-3 text-gray-700">{page.title || 'Untitled page'}</td>
                    <td className="px-4 py-3 text-gray-700">{page.word_count ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-700">{page.load_time ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Actionable Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-4">
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-red-700 mb-2 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                High Priority
              </h4>
              <ul className="space-y-2 text-sm text-gray-600">
                {result.recommendations
                  .filter(rec => rec.priority === 'High')
                  .map((rec, index) => (
                    <li key={rec.id || index} className="flex items-start space-x-2">
                      <span className="text-red-500 mt-1">•</span>
                      <span>{rec.title}</span>
                    </li>
                  ))}
              </ul>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="border-l-4 border-yellow-500 pl-4">
              <h4 className="font-semibold text-yellow-700 mb-2 flex items-center">
                <Info className="w-5 h-5 mr-2" />
                Medium Priority
              </h4>
              <ul className="space-y-2 text-sm text-gray-600">
                {result.recommendations
                  .filter(rec => rec.priority === 'Medium')
                  .map((rec, index) => (
                    <li key={rec.id || index} className="flex items-start space-x-2">
                      <span className="text-yellow-500 mt-1">•</span>
                      <span>{rec.title}</span>
                    </li>
                  ))}
              </ul>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="border-l-4 border-green-500 pl-4">
              <h4 className="font-semibold text-green-700 mb-2 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                Low Priority
              </h4>
              <ul className="space-y-2 text-sm text-gray-600">
                {result.recommendations
                  .filter(rec => rec.priority === 'Low')
                  .map((rec, index) => (
                    <li key={rec.id || index} className="flex items-start space-x-2">
                      <span className="text-green-500 mt-1">•</span>
                      <span>{rec.title}</span>
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Technical Issues & Content Gaps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Technical Issues</h3>
          {result.technical_issues.length > 0 ? (
            <ul className="space-y-3">
              {result.technical_issues.map((issue, index) => (
                <li key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{issue}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">No critical technical issues found!</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Content Gaps</h3>
          {result.insights.content_gaps.length > 0 ? (
            <ul className="space-y-3">
              {result.insights.content_gaps.map((gap, index) => (
                <li key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <Info className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{gap}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">Content coverage looks good!</p>
            </div>
          )}
        </div>
      </div>

      {/* Pro Tips */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">Pro Tips for Improvement</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 font-bold text-sm">1</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Focus on High Priority Items</h4>
              <p className="text-sm text-gray-600">Address the red-flagged recommendations first for maximum impact.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 font-bold text-sm">2</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Measure & Iterate</h4>
              <p className="text-sm text-gray-600">Re-run analysis after implementing changes to track improvements.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 font-bold text-sm">3</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Technical First</h4>
              <p className="text-sm text-gray-600">Fix technical issues before optimizing content and conversion elements.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 font-bold text-sm">4</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">User Experience</h4>
              <p className="text-sm text-gray-600">Prioritize improvements that enhance user experience and engagement.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
