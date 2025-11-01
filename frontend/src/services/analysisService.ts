export interface AnalysisRequest {
  url: string;
  analysis_type: 'comprehensive' | 'basic' | 'ai';
  max_pages: number;
  include_technical_seo?: boolean;
  include_competitor_insights?: boolean;
}

export interface AnalysisMetadata {
  analysis_id: string;
  requested_url: string;
  pages_analyzed: number;
  pages_failed: number;
  analysis_duration: number;
  timestamp: string;
  user_tier: string;
  model_used: string;
}

export interface ScoreDetails {
  overall_score: number;
  title_optimization: number;
  meta_description: number;
  header_structure: number;
  content_quality: number;
  internal_linking: number;
  technical_seo: number;
}

export interface ConversionDetails {
  overall_score: number;
  headline_effectiveness: number;
  value_proposition: number;
  cta_optimization: number;
  trust_signals: number;
  form_optimization: number;
  urgency_scarcity: number;
}

export interface RecommendationItem {
  id: string;
  category: string;
  priority: 'High' | 'Medium' | 'Low';
  title: string;
  description: string;
  implementation: string;
  impact_score: number;
  estimated_effort: string;
  expected_improvement: string;
}

export interface InsightDetails {
  competitive_insights: string[];
  content_gaps: string[];
  seo_keyword_insights?: string[];
  conversion_highlights?: string[];
  pages_analyzed_details: Array<{
    url: string;
    title: string;
    word_count: number;
    load_time: number;
  }>;
}

export interface CompetitiveAnalysis {
  market_position: string;
  opportunities: string[];
  threats: string[];
}

export interface AnalysisResponse {
  success: boolean;
  metadata: AnalysisMetadata;
  seo_analysis: ScoreDetails;
  conversion_analysis: ConversionDetails;
  recommendations: RecommendationItem[];
  insights: InsightDetails;
  technical_issues: string[];
  competitive_analysis: CompetitiveAnalysis;
  summary: string;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  expires_at: string;
  last_accessed_at: string;
  is_active: boolean;
}

export interface AnalysisHistoryEntry {
  analysis_id: string;
  session_id: string;
  requested_url: string;
  seo_overall_score?: number;
  conversion_overall_score?: number;
  headline?: string;
  summary?: string;
  created_at: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export class AnalysisService {
  private static async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include',
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        if (response.status === 401) {
          SessionManager.clearSession();
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      if (response.status === 204 || response.status === 205) {
        return undefined as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`API request failed: ${error.message}`);
      }
      throw new Error('API request failed: Unknown error');
    }
  }

  static async analyzeWebsite(request: AnalysisRequest): Promise<AnalysisResponse> {
    const sessionId = await SessionManager.ensureValidSession();
    return this.makeRequest<AnalysisResponse>(`/analyze?session_id=${sessionId}`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  static async getAnalysisHistory(): Promise<AnalysisHistoryEntry[]> {
    const sessionId = await SessionManager.ensureValidSession();
    return this.makeRequest<AnalysisHistoryEntry[]>(`/analysis/history?session_id=${sessionId}`);
  }

  static async getAnalysisById(analysisId: string): Promise<AnalysisResponse> {
    const sessionId = await SessionManager.ensureValidSession();
    return this.makeRequest<AnalysisResponse>(`/analysis/${analysisId}?session_id=${sessionId}`);
  }

  static async deleteAnalysis(analysisId: string): Promise<void> {
    const sessionId = await SessionManager.ensureValidSession();
    return this.makeRequest<void>(`/analysis/${analysisId}?session_id=${sessionId}`, {
      method: 'DELETE',
    });
  }

  static async createSession(): Promise<SessionResponse> {
    return this.makeRequest<SessionResponse>('/session/create', {
      method: 'POST',
      body: JSON.stringify({ ttl_minutes: 60 }),
    });
  }

  static async extendSession(sessionId: string): Promise<SessionResponse> {
    return this.makeRequest<SessionResponse>(`/session/${sessionId}/extend`, {
      method: 'PUT',
      body: JSON.stringify({ extend_minutes: 60 }),
    });
  }
}

// Utility functions for session management
export const SessionManager = {
  getSessionId(): string | null {
    return localStorage.getItem('magentix_session_id');
  },

  setSessionId(sessionId: string): void {
    localStorage.setItem('magentix_session_id', sessionId);
  },

  getSessionIdFromCookie(): string | null {
    if (typeof document === 'undefined') {
      return null;
    }
    const cookies = document.cookie?.split(';') ?? [];
    for (const cookie of cookies) {
      const [key, value] = cookie.trim().split('=');
      if (key === 'magentix_session_id' && value) {
        return decodeURIComponent(value);
      }
    }
    return null;
  },

  clearSession(): void {
    localStorage.removeItem('magentix_session_id');
  },

  isSessionValid(): boolean {
    const sessionId = this.getSessionId();
    return !!sessionId;
  },

  async ensureValidSession(): Promise<string> {
    let sessionId = this.getSessionId();

    if (!sessionId) {
      const cookieSession = this.getSessionIdFromCookie();
      if (cookieSession) {
        sessionId = cookieSession;
        this.setSessionId(sessionId);
      }
    }

    if (!sessionId) {
      try {
        const session = await AnalysisService.createSession();
        sessionId = session.session_id;
        this.setSessionId(sessionId);
      } catch (error) {
        console.error('Failed to create session:', error);
        throw new Error('Failed to create user session');
      }
    }

    return sessionId;
  }
};

const hashString = (input: string): number => {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0;
  }
  return hash || 1;
};

const createSeededGenerator = (seed: number) => {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
};

const createDeterministicId = (prefix: string, key: string) => {
  const hash = hashString(`${prefix}:${key}`);
  return `${prefix}_${hash.toString(16)}`;
};

// Mock data for development/testing
export const getMockAnalysisResult = (url: string, analysisType: string): AnalysisResponse => {
  const seedKey = `${url}|${analysisType}`;
  const seededRandom = createSeededGenerator(hashString(seedKey));
  const nextInt = (min: number, max: number) => Math.floor(seededRandom() * (max - min + 1)) + min;
  const nextFloat = (min: number, max: number, decimals = 2) =>
    parseFloat((seededRandom() * (max - min) + min).toFixed(decimals));

  const baseScore = nextInt(60, 95);
  const seoScore = nextInt(60, 95);
  const conversionScore = nextInt(60, 95);
  const pagesAnalyzed = nextInt(3, 7);

  return {
    success: true,
    metadata: {
      analysis_id: createDeterministicId('analysis', seedKey),
      requested_url: url,
      pages_analyzed,
      pages_failed: 0,
      analysis_duration: nextFloat(5, 15),
      timestamp: new Date().toISOString(),
      user_tier: 'premium',
      model_used: analysisType === 'basic' ? 'fallback-analysis' : 'llama-3.3-70b-versatile',
    },
    seo_analysis: {
      overall_score: seoScore,
      title_optimization: Math.min(100, seoScore + 5),
      meta_description: Math.min(100, seoScore + 3),
      header_structure: Math.min(100, seoScore + 7),
      content_quality: Math.min(100, seoScore + 4),
      internal_linking: Math.min(100, seoScore - 2),
      technical_seo: Math.min(100, seoScore + 6),
    },
    conversion_analysis: {
      overall_score: conversionScore,
      headline_effectiveness: Math.min(100, conversionScore + 6),
      value_proposition: Math.min(100, conversionScore + 4),
      cta_optimization: Math.min(100, conversionScore + 8),
      trust_signals: Math.min(100, conversionScore + 5),
      form_optimization: Math.min(100, conversionScore + 3),
      urgency_scarcity: Math.min(100, conversionScore - 4),
    },
    recommendations: [
      {
        id: createDeterministicId('rec', `${seedKey}:high`),
        category: 'SEO',
        priority: 'High',
        title: 'Optimize page loading speed by compressing images',
        description: 'Large image assets are slowing the site down.',
        implementation: 'Compress hero and gallery images using modern formats.',
        impact_score: 8,
        estimated_effort: 'Medium',
        expected_improvement: '80% potential improvement',
      },
      {
        id: createDeterministicId('rec', `${seedKey}:medium`),
        category: 'Conversion',
        priority: 'Medium',
        title: 'Add customer testimonials for social proof',
        description: 'Social proof increases trust and conversion.',
        implementation: 'Showcase three client testimonials on the homepage.',
        impact_score: 6,
        estimated_effort: 'Low',
        expected_improvement: '60% potential improvement',
      },
      {
        id: createDeterministicId('rec', `${seedKey}:low`),
        category: 'SEO',
        priority: 'Low',
        title: 'Implement breadcrumb navigation',
        description: 'Breadcrumbs improve crawlability and UX.',
        implementation: 'Add schema-enabled breadcrumbs on product pages.',
        impact_score: 4,
        estimated_effort: 'Low',
        expected_improvement: '40% potential improvement',
      },
    ],
    insights: {
      competitive_insights: [
        'Competitors publish weekly blog updates.',
        'Top competitors feature comparison tables.',
        'Competitor landing pages highlight customer logos.',
      ],
      content_gaps: [
        'Limited FAQ section for common questions',
        'Missing case studies or success stories',
        'Could benefit from more detailed product descriptions',
      ],
      seo_keyword_insights: [
        'Lead Generation (42 mentions)',
        'Automation (31 mentions)',
        'Workflow (27 mentions)',
      ],
      conversion_highlights: [
        'Detected 12 call-to-action elements across the site; most common: “Get Started”, “Book a Demo”.',
        'Identified 3 lead capture forms (POST: 2, GET: 1); ensure value propositions align to each stage.',
        'High-intent messaging detected for: demo, pricing, free trial.',
      ],
      pages_analyzed_details: [
        {
          url,
          title: 'Homepage',
          word_count: nextInt(800, 1200),
          load_time: nextFloat(1, 3),
        },
      ],
    },
    technical_issues: [
      'Images are not optimized for web',
      'Missing alt text on several images',
      'JavaScript files could be minified further',
    ],
    competitive_analysis: {
      market_position: 'Analysis based on content structure and optimization patterns',
      opportunities: [
        'Improve technical SEO for faster load times',
        'Increase trust signals through testimonials',
        'Add structured data for products',
      ],
      threats: [
        'Competitor sites may have better technical SEO',
        'Missing key conversion elements',
      ],
    },
    summary: `This is a comprehensive analysis of ${url}. The website shows ${baseScore >= 80 ? 'excellent' : baseScore >= 60 ? 'good' : 'room for improvement'} performance across key metrics. Focus on implementing the high-priority recommendations to see immediate improvements.`,
  };
};
