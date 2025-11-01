import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreCardProps {
  title: string;
  score: number;
  maxScore: number;
  description: string;
  trend?: 'up' | 'down' | 'neutral';
}

export default function ScoreCard({ title, score, maxScore, description, trend = 'neutral' }: ScoreCardProps) {
  const percentage = (score / maxScore) * 100;
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getScoreColor = () => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBarColor = () => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-2">
          {getTrendIcon()}
          <span className={`text-2xl font-bold ${getScoreColor()}`}>
            {score}
          </span>
          <span className="text-gray-400">/{maxScore}</span>
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Score</span>
          <span>{Math.round(percentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-700 ${getBarColor()}`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
    </div>
  );
}