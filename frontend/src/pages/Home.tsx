import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Users, Target, Star, ArrowRight, BarChart3, Zap } from 'lucide-react';
import AnalysisProgress from '../components/AnalysisProgress';
import WebsiteAnalysisResults from '../components/WebsiteAnalysisResults';
import Hero from '../components/Hero';
import { AnalysisService, getMockAnalysisResult, AnalysisRequest, AnalysisResponse, AnalysisHistoryEntry, SessionManager } from '../services/analysisService';

type AppState = 'hero' | 'analyzing' | 'results';

export default function Home() {
  const [state, setState] = useState<AppState>('hero');
  const [analysisStep, setAnalysisStep] = useState(0);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const analysisSteps = [
    'Scanning website structure',
    'Analyzing page content',
    'Evaluating SEO elements',
    'Checking conversion optimization',
    'Reviewing technical performance',
    'Assessing mobile responsiveness',
    'Measuring page load speed',
    'Analyzing content quality',
    'Generating AI insights',
    'Compiling recommendations'
  ];

  const handleAnalyze = async (url: string, analysisType: string, maxPages: number) => {
    setAnalysisError(null);
    setState('analyzing');
    setAnalysisStep(0);

    let progressInterval: ReturnType<typeof setInterval> | null = null;
    const stopProgress = () => {
      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }
    };

    try {
      progressInterval = setInterval(() => {
        setAnalysisStep(prev => (prev >= analysisSteps.length - 1 ? prev : prev + 1));
      }, 800);

      const request: AnalysisRequest = {
        url,
        analysis_type: analysisType as 'comprehensive' | 'basic' | 'ai',
        max_pages: maxPages,
        include_technical_seo: true,
        include_competitor_insights: true
      };

      let analysisResult: AnalysisResponse | null = null;
      let apiError: unknown = null;

      try {
        analysisResult = await AnalysisService.analyzeWebsite(request);
      } catch (error) {
        apiError = error;
        console.warn('API call failed', error);
        const allowMock = import.meta.env.VITE_ENABLE_MOCK_DATA === 'true';
        if (allowMock) {
          analysisResult = getMockAnalysisResult(url, analysisType);
        } else {
          throw error;
        }
      }

      if (!analysisResult) {
        throw apiError || new Error('Analysis response was empty');
      }

      stopProgress();
      setResults(analysisResult);
      setTimeout(() => setState('results'), 500);
      loadHistory();
    } catch (error) {
      console.error('Analysis failed:', error);
      stopProgress();
      setResults(null);
      setState('hero');
      const message = error instanceof Error ? error.message : 'Unable to analyze the website.';
      setAnalysisError(message);
    } finally {
      stopProgress();
    }
  };

  const handleNewAnalysis = () => {
    setState('hero');
    setAnalysisStep(0);
    setResults(null);
    setAnalysisError(null);
    loadHistory();
  };

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      await SessionManager.ensureValidSession();
      const entries = await AnalysisService.getAnalysisHistory();
      setHistory(entries);
      setHistoryError(null);
    } catch (error) {
      console.error('Failed to load analysis history', error);
      setHistory([]);
      const message = error instanceof Error ? error.message : 'Unable to load previous analyses.';
      setHistoryError(message);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleViewHistoricalAnalysis = async (analysisId: string) => {
    setAnalysisError(null);
    setState('analyzing');
    setAnalysisStep(analysisSteps.length - 1);

    try {
      await SessionManager.ensureValidSession();
      const analysisResult = await AnalysisService.getAnalysisById(analysisId);
      setResults(analysisResult);
      setState('results');
    } catch (error) {
      console.error('Failed to load analysis', error);
      const message = error instanceof Error ? error.message : 'Unable to load the selected analysis.';
      setAnalysisError(message);
      setResults(null);
      setState('hero');
    }
  };

  if (state === 'analyzing') {
    return (
      <div className="pt-24 pb-16">
        <div className="container mx-auto px-6">
          <AnalysisProgress 
            currentStep={analysisStep}
            totalSteps={analysisSteps.length}
            steps={analysisSteps}
          />
        </div>
      </div>
    );
  }

  if (state === 'results' && results) {
    return (
      <div className="pt-24 pb-16">
        <div className="container mx-auto px-6">
          <WebsiteAnalysisResults 
            result={results}
            onNewAnalysis={handleNewAnalysis}
          />
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Hero Section */}
      <section className="pt-24 pb-16 bg-gradient-to-br from-blue-50 via-white to-blue-50">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Analyze Your Website for
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-blue-700"> Maximum Performance</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Get comprehensive website analysis with AI-powered insights. Evaluate SEO, conversion optimization, and technical performance in minutes.
            </p>

            {analysisError && (
              <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-left text-sm text-red-700">
                {analysisError}
              </div>
            )}
            
            <Hero onAnalyze={handleAnalyze} />
          </div>
        </div>
      </section>

      <section className="py-12 bg-white">
        <div className="container mx-auto px-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Your Recent Analyses</h2>
                <p className="text-sm text-gray-500">Pick up where you left off and export reports anytime.</p>
              </div>
              {!historyLoading && history.length > 0 && (
                <button
                  onClick={loadHistory}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-2"
                >
                  <span>Refresh</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>

            {historyLoading && (
              <div className="p-6 rounded-2xl border border-dashed border-blue-200 bg-blue-50 text-sm text-blue-600">
                Loading your previous analyses...
              </div>
            )}

            {!historyLoading && historyError && (
              <div className="p-6 rounded-2xl border border-dashed border-red-200 bg-red-50 text-sm text-red-600">
                {historyError}
              </div>
            )}

            {!historyLoading && !historyError && history.length === 0 && (
              <div className="p-6 rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-600 text-center">
                No saved analyses yet. Run your first website analysis to see it here.
              </div>
            )}

            {!historyLoading && history.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {history.map((entry) => (
                  <div key={entry.analysis_id} className="rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow bg-white">
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-medium text-blue-600 uppercase tracking-wide">{new Date(entry.created_at).toLocaleString()}</span>
                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                          {entry.seo_overall_score ?? '--'}/100 SEO
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 truncate" title={entry.requested_url}>
                        {entry.requested_url}
                      </h3>
                      {entry.summary && (
                        <p className="text-sm text-gray-600 mt-2 max-h-16 overflow-hidden">{entry.summary}</p>
                      )}

                      <div className="flex items-center justify-between mt-6">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          {entry.seo_overall_score != null && (
                            <span>SEO: <span className="font-medium text-gray-700">{entry.seo_overall_score}</span></span>
                          )}
                          {entry.conversion_overall_score != null && (
                            <span>Conversion: <span className="font-medium text-gray-700">{entry.conversion_overall_score}</span></span>
                          )}
                        </div>
                        <button
                          onClick={() => handleViewHistoricalAnalysis(entry.analysis_id)}
                          className="inline-flex items-center space-x-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
                        >
                          <span>View Report</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Overview */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Comprehensive Website Analysis
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered tool evaluates every aspect of your website to maximize performance and conversions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Deep Analytics</h3>
              <p className="text-gray-600">
                Analyze 8+ key metrics including SEO optimization, conversion elements, and technical performance.
              </p>
            </div>

            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-green-50 to-green-100 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Actionable Insights</h3>
              <p className="text-gray-600">
                Get prioritized recommendations with clear action steps to improve your website performance immediately.
              </p>
            </div>

            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-purple-100 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Instant Results</h3>
              <p className="text-gray-600">
                Complete analysis in under 60 seconds with detailed scoring and professional reporting.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How Magentix Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Three simple steps to analyze and optimize your website performance.
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-6">
                  1
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Enter Your URL</h3>
                <p className="text-gray-600">
                  Simply paste your website URL into our analyzer and click "Analyze Now" to begin the process.
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-6">
                  2
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">AI Analysis</h3>
                <p className="text-gray-600">
                  Our AI scans your website across 8+ key metrics to evaluate your overall performance and optimization opportunities.
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-6">
                  3
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Get Results</h3>
                <p className="text-gray-600">
                  Receive detailed scores, insights, and prioritized recommendations to boost your website performance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Trusted by Growing Businesses
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Join thousands of businesses that have improved their website performance with Magentix.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-gray-50 p-8 rounded-2xl">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4">
                "Magentix helped us identify critical issues with our website. We saw a 40% increase in performance within the first month."
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                  S
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Sarah Johnson</p>
                  <p className="text-sm text-gray-600">Marketing Director, TechStart</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-8 rounded-2xl">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4">
                "The insights were incredibly detailed and actionable. Our website performance improved significantly after implementing the recommendations."
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                  M
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Michael Chen</p>
                  <p className="text-sm text-gray-600">CEO, GrowthLab</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-8 rounded-2xl">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4">
                "Easy to use and incredibly powerful. The mobile optimization insights alone were worth the investment."
              </p>
              <div className="flex items-center">
                <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                  E
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Emily Rodriguez</p>
                  <p className="text-sm text-gray-600">Founder, DigitalBoost</p>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className="flex justify-center items-center space-x-8 text-gray-600">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">10,000+</div>
                <div className="text-sm">Websites Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">35%</div>
                <div className="text-sm">Average Conversion Increase</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">4.9/5</div>
                <div className="text-sm">Customer Rating</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Analyze Your Website?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Start analyzing your website today and discover opportunities to improve your performance.
          </p>
          <button 
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="bg-white text-blue-600 px-8 py-4 rounded-2xl font-semibold text-lg hover:bg-gray-100 transition-colors inline-flex items-center space-x-2"
          >
            <span>Get Started Free</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>
    </>
  );
}
