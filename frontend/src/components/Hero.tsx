import React, { useState } from 'react';
import { TrendingUp, Users, Target, Zap } from 'lucide-react';

interface HeroProps {
  onAnalyze: (url: string, analysisType: string, maxPages: number) => void;
}

export default function Hero({ onAnalyze }: HeroProps) {
  const [url, setUrl] = useState('');
  const [analysisType, setAnalysisType] = useState('comprehensive');
  const [maxPages, setMaxPages] = useState(10);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onAnalyze(url, analysisType, maxPages);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto mb-12">
      <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Analysis Type</label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="comprehensive">Comprehensive (AI + Basic)</option>
              <option value="ai">AI Analysis Only</option>
              <option value="basic">Basic Analysis</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Pages</label>
            <input
              type="number"
              min="1"
              max="50"
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Website URL</label>
            <div className="relative">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://yoursite.com"
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-4 px-6 rounded-xl hover:bg-blue-700 transition-colors font-semibold text-lg flex items-center justify-center space-x-2"
        >
          <Zap className="w-5 h-5" />
          <span>Analyze Website</span>
        </button>
      </div>

      <div className="flex justify-center items-center space-x-8 text-gray-600">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <span className="text-sm">SEO Optimization</span>
        </div>
        <div className="flex items-center space-x-2">
          <Users className="w-5 h-5 text-blue-600" />
          <span className="text-sm">Conversion Analysis</span>
        </div>
        <div className="flex items-center space-x-2">
          <Target className="w-5 h-5 text-blue-600" />
          <span className="text-sm">Technical Insights</span>
        </div>
      </div>
    </form>
  );
}