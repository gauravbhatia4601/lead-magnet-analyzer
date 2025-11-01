import React from 'react';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

interface AnalysisProgressProps {
  currentStep: number;
  totalSteps: number;
  steps: string[];
}

export default function AnalysisProgress({ currentStep, totalSteps, steps }: AnalysisProgressProps) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Analyzing Your Website</h3>
          <p className="text-gray-600">Please wait while we evaluate your lead magnet performance...</p>
        </div>

        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                {index < currentStep ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : index === currentStep ? (
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Circle className="w-6 h-6 text-gray-300" />
                )}
              </div>
              <span className={`text-sm font-medium ${
                index < currentStep ? 'text-green-600' : 
                index === currentStep ? 'text-blue-600' : 
                'text-gray-400'
              }`}>
                {step}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round((currentStep / totalSteps) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
}