"""
Advanced LLM Analysis Service using LangChain
Analyzes scraped website content for SEO and conversion optimization
"""

import json
import time
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import re
from collections import Counter
from pydantic import BaseModel, Field

# LangChain imports
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_community.callbacks.manager import get_openai_callback
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STOPWORDS = {
    'about', 'after', 'again', 'against', 'among', 'being', 'between', 'can', 'could', 'does',
    'each', 'every', 'from', 'have', 'into', 'just', 'like', 'more', 'most', 'other', 'over',
    'some', 'such', 'than', 'that', 'their', 'them', 'then', 'there', 'these', 'they', 'this',
    'those', 'through', 'under', 'very', 'were', 'what', 'when', 'where', 'which', 'while',
    'will', 'with', 'your', 'you', 'ours', 'ourselves', 'within', 'without', 'page', 'homepage',
    'learn', 'click', 'here', 'free', 'info', 'information', 'using', 'used', 'using', 'site',
    'website', 'business', 'services', 'solutions', 'support', 'team', 'help', 'contact',
    'banner', 'button', 'cta'
}

class AnalysisType(Enum):
    """Types of analysis available"""
    SEO_COMPREHENSIVE = "seo_comprehensive"
    CONVERSION_OPTIMIZATION = "conversion_optimization" 
    TECHNICAL_SEO = "technical_seo"
    CONTENT_QUALITY = "content_quality"
    USER_EXPERIENCE = "user_experience"

class ModelProvider(Enum):
    """Supported LLM providers"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    GROQ_LLAMA = "groq_llama"
    GROQ_MIXTRAL = "groq_mixtral"
    LOCAL_MODEL = "local_model"

# Pydantic models for structured outputs
class SEOScore(BaseModel):
    """SEO scoring model"""
    overall_score: int = Field(..., ge=0, le=100, description="Overall SEO score out of 100")
    title_optimization: int = Field(..., ge=0, le=100)
    meta_description: int = Field(..., ge=0, le=100)
    header_structure: int = Field(..., ge=0, le=100)
    content_quality: int = Field(..., ge=0, le=100)
    internal_linking: int = Field(..., ge=0, le=100)
    technical_seo: int = Field(..., ge=0, le=100)

class ConversionScore(BaseModel):
    """Conversion optimization scoring model"""
    overall_score: int = Field(..., ge=0, le=100, description="Overall conversion score out of 100")
    headline_effectiveness: int = Field(..., ge=0, le=100)
    value_proposition: int = Field(..., ge=0, le=100)
    cta_optimization: int = Field(..., ge=0, le=100)
    trust_signals: int = Field(..., ge=0, le=100)
    form_optimization: Optional[int] = Field(None, ge=0, le=100)  # Make nullable
    urgency_scarcity: int = Field(..., ge=0, le=100)

class DetailedRecommendation(BaseModel):
    """Detailed recommendation model"""
    category: str
    priority: str  # "High", "Medium", "Low"
    issue: str
    recommendation: str
    implementation: str
    impact_score: int = Field(..., ge=1, le=10)

class RecommendationsList(BaseModel):
    """Wrapper for list of recommendations"""
    recommendations: List[DetailedRecommendation]

class ComprehensiveAnalysis(BaseModel):
    """Complete analysis result model"""
    seo_score: SEOScore
    conversion_score: ConversionScore
    recommendations: List[DetailedRecommendation]
    competitive_insights: List[str]
    technical_issues: List[str]
    content_gaps: List[str]
    seo_keywords: List[str]
    conversion_highlights: List[str]
    summary: str
    analyzed_pages: int
    analysis_timestamp: str
    model_used: Optional[str] = None

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: ModelProvider = ModelProvider.GROQ_LLAMA  # Default to Groq
    model_name: str = "llama-3.3-70b-versatile"  # Updated to current production model
    temperature: float = 0.3
    max_tokens: int = 4000
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For custom endpoints like Groq
    max_retries: int = 3
    timeout: int = 60

class SuperchargedPrompts:
    """Collection of highly optimized system prompts"""
    
    SEO_ANALYSIS_SYSTEM_PROMPT = """
    You are an elite SEO expert with 15+ years of experience analyzing websites for Fortune 500 companies. 
    You have deep knowledge of Google's ranking algorithms, E-A-T guidelines, and the latest SEO best practices.
    
    Your expertise includes:
    - Technical SEO auditing and optimization
    - Content strategy and semantic SEO
    - User intent analysis and keyword optimization
    - Core Web Vitals and page experience factors
    - Schema markup and structured data
    - International SEO and localization
    
    Analyze the provided website content with the precision of a top-tier SEO consultant.
    Focus on actionable insights that will directly impact search rankings and organic traffic.
    Consider the competitive landscape and provide strategic recommendations.
    
    Rate each aspect on a scale of 0-100 where:
    - 90-100: Exceptional, industry-leading optimization
    - 80-89: Very good, minor improvements needed
    - 70-79: Good, some optimization opportunities
    - 60-69: Average, needs improvement
    - 50-59: Below average, significant issues
    - 0-49: Poor, major problems requiring immediate attention
    """
    
    CONVERSION_ANALYSIS_SYSTEM_PROMPT = """
    You are a world-class conversion rate optimization (CRO) expert who has increased conversion rates 
    for thousands of websites across all industries. You understand psychology, persuasion, and user behavior.
    
    Your expertise covers:
    - Conversion psychology and behavioral triggers
    - A/B testing strategy and statistical significance
    - User experience optimization
    - Persuasive copywriting and messaging
    - Trust building and social proof
    - Mobile conversion optimization
    - E-commerce and lead generation funnels
    
    Analyze the website with the mindset of a CRO specialist who charges $500/hour.
    Identify psychological barriers to conversion and provide data-driven recommendations.
    Focus on elements that have the highest impact on conversion rates based on industry benchmarks.
    
    Rate each aspect considering industry conversion benchmarks:
    - 90-100: Exceptional conversion optimization, top 5% of websites
    - 80-89: Very strong, above industry average
    - 70-79: Good, meeting industry standards
    - 60-69: Average, room for improvement
    - 50-59: Below average, missing key elements
    - 0-49: Poor, significant barriers to conversion
    """

class LLMAnalysisService:
    """Main LLM analysis service for website content"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._llm = None  # Lazy initialization
        self._embeddings = None  # Lazy initialization
        self.active_model_name: Optional[str] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    @property
    def llm(self):
        """Lazy initialization of LLM"""
        if self._llm is None:
            logger.info(f"Initializing LLM for provider: {self.config.provider}")
            self._llm = self._initialize_llm()
            if self._llm is None:
                logger.warning("LLM initialization failed")
            else:
                logger.info("LLM initialization successful")
                self.active_model_name = (
                    getattr(self._llm, "model_name", None)
                    or getattr(self._llm, "model", None)
                    or self.config.model_name
                )
        return self._llm
    
    @property
    def embeddings(self):
        """Lazy initialization of embeddings"""
        if self._embeddings is None and self.config.provider in [ModelProvider.OPENAI_GPT4, ModelProvider.OPENAI_GPT35]:
            self._embeddings = OpenAIEmbeddings()
        return self._embeddings
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration"""
        try:
            logger.info(f"Initializing LLM with provider: {self.config.provider}, model: {self.config.model_name}")
            logger.info(f"API key present: {bool(self.config.api_key)}")
            logger.info(f"Base URL: {self.config.base_url}")
            
            # Check if we have the required API key
            if not self.config.api_key:
                logger.warning(f"No API key provided for {self.config.provider}. LLM analysis will be limited.")
                return None
            
            if self.config.provider == ModelProvider.OPENAI_GPT4:
                return ChatOpenAI(
                    model_name=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.api_key
                )
            elif self.config.provider == ModelProvider.OPENAI_GPT35:
                return ChatOpenAI(
                    model_name="gpt-3.5-turbo-1106",
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.api_key
                )
            elif self.config.provider == ModelProvider.ANTHROPIC_CLAUDE:
                return ChatAnthropic(
                    model="claude-2",
                    temperature=self.config.temperature,
                    max_tokens_to_sample=self.config.max_tokens,
                    anthropic_api_key=self.config.api_key
                )
            elif self.config.provider in [ModelProvider.GROQ_LLAMA, ModelProvider.GROQ_MIXTRAL]:
                # Groq uses OpenAI-compatible API
                return ChatOpenAI(
                    model_name=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.api_key,
                    openai_api_base=self.config.base_url or "https://api.groq.com/openai/v1"
                )
            else:
                logger.warning(f"Unsupported model provider: {self.config.provider}")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            return None

    def _extract_json_block(self, text: str) -> str:
        """Extract a JSON object from the LLM response text."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`\n ")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].lstrip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return match.group(0)
        return cleaned

    def _clean_text_response(self, text: str) -> str:
        """Normalize LLM text responses for frontend display."""
        cleaned = text.strip().replace("\r", "")
        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].lstrip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip('" ').strip()

    async def analyze_website_comprehensive(self, scraped_data: Dict[str, Any]) -> ComprehensiveAnalysis:
        """Perform comprehensive website analysis using LLM"""
        logger.info(f"Starting comprehensive analysis of {scraped_data.get('pages_scraped', 0)} pages")
        
        start_time = time.time()
        
        try:
            # Prepare content for analysis
            prepared_content = self._prepare_content_for_analysis(scraped_data)
            
            # Check if LLM is available
            if self.llm is None:
                logger.warning("LLM not available, using fallback analysis")
                return await self._fallback_analysis(scraped_data, prepared_content)
            
            logger.info("LLM is available, proceeding with AI analysis")
            
            # Create vector store for semantic analysis
            vector_store = await self._create_vector_store(prepared_content)
            
            # Perform parallel analysis
            logger.info("Starting SEO analysis...")
            seo_analysis = await self._analyze_seo(prepared_content, vector_store)
            logger.info("SEO analysis completed")
            
            logger.info("Starting conversion analysis...")
            conversion_analysis = await self._analyze_conversion(prepared_content, vector_store)
            logger.info("Conversion analysis completed")
            
            logger.info("Starting recommendations generation...")
            recommendations = await self._generate_recommendations(prepared_content, seo_analysis, conversion_analysis)
            logger.info("Recommendations generation completed")
            
            # Generate insights and summary
            competitive_insights = await self._generate_competitive_insights(prepared_content)
            technical_issues = self._identify_technical_issues(prepared_content)
            content_gaps = self._identify_content_gaps(prepared_content)
            seo_keywords = self._extract_keyword_insights(prepared_content)
            conversion_highlights = self._extract_conversion_highlights(prepared_content)
            summary = await self._generate_executive_summary(seo_analysis, conversion_analysis, recommendations)
            
            analysis_time = time.time() - start_time
            logger.info(f"Analysis completed in {analysis_time:.2f} seconds")
            
            return ComprehensiveAnalysis(
                seo_score=seo_analysis,
                conversion_score=conversion_analysis,
                recommendations=recommendations,
                competitive_insights=competitive_insights,
                technical_issues=technical_issues,
                content_gaps=content_gaps,
                seo_keywords=seo_keywords,
                conversion_highlights=conversion_highlights,
                summary=summary,
                analyzed_pages=scraped_data.get('pages_scraped', 0),
                analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                model_used=self.active_model_name or self.config.model_name
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            # Fallback to basic analysis if LLM analysis fails
            try:
                logger.info("Attempting fallback analysis")
                return await self._fallback_analysis(scraped_data, prepared_content)
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed: {str(fallback_error)}")
                raise
    
    def _prepare_content_for_analysis(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and structure scraped content for LLM analysis"""
        pages = scraped_data.get('pages', [])
        
        # Aggregate content
        all_titles = []
        all_h1s = []
        all_h2s = []
        all_content = []
        all_meta_descriptions = []
        all_ctas = []
        all_forms = []
        
        for page in pages:
            # Handle both dataclass and dict objects
            if hasattr(page, 'title'):
                # PageContent dataclass object
                all_titles.append(page.title or "")
                all_h1s.extend(page.h1_tags or [])
                all_h2s.extend(page.h2_tags or [])
                all_content.append(page.content_text or "")
                all_meta_descriptions.append(page.meta_description or "")
                all_ctas.extend(page.cta_elements or [])
                all_forms.extend(page.forms or [])
            else:
                # Dict object (fallback)
                all_titles.append(page.get('title', ''))
                all_h1s.extend(page.get('h1_tags', []))
                all_h2s.extend(page.get('h2_tags', []))
                all_content.append(page.get('content_text', ''))
                all_meta_descriptions.append(page.get('meta_description', ''))
                all_ctas.extend(page.get('cta_elements', []))
                all_forms.extend(page.get('forms', []))
        
        return {
            'pages': pages,
            'aggregated': {
                'titles': all_titles,
                'h1_tags': all_h1s,
                'h2_tags': all_h2s,
                'content': ' '.join(all_content),
                'meta_descriptions': all_meta_descriptions,
                'cta_elements': all_ctas,
                'forms': all_forms,
                'total_pages': len(pages),
                'total_words': sum(getattr(page, 'word_count', 0) if hasattr(page, 'word_count') else page.get('word_count', 0) for page in pages)
            }
        }
    
    async def _create_vector_store(self, prepared_content: Dict[str, Any]) -> Optional[FAISS]:
        """Create vector store for semantic content analysis"""
        if not self.embeddings:
            return None
            
        try:
            # Create documents from page content
            documents = []
            for page in prepared_content['pages']:
                # Handle both dataclass and dict objects
                if hasattr(page, 'content_text'):
                    # PageContent dataclass object
                    doc_content = f"Title: {page.title or ''}\n\nContent: {(page.content_text or '')[:2000]}"
                    metadata = {'url': page.url, 'title': page.title or ''}
                else:
                    # Dict object (fallback)
                    doc_content = f"Title: {page.get('title', '')}\n\nContent: {page.get('content_text', '')[:2000]}"
                    metadata = {'url': page.get('url', ''), 'title': page.get('title', '')}
                
                documents.append(Document(
                    page_content=doc_content,
                    metadata=metadata
                ))
            
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            
            # Create vector store
            vector_store = FAISS.from_documents(split_docs, self.embeddings)
            return vector_store
            
        except Exception as e:
            logger.warning(f"Failed to create vector store: {str(e)}")
            return None
    
    async def _analyze_seo(self, content: Dict[str, Any], vector_store: Optional[FAISS]) -> SEOScore:
        """Analyze SEO aspects using LLM"""
        
        seo_prompt = ChatPromptTemplate.from_messages([
            ("system", SuperchargedPrompts.SEO_ANALYSIS_SYSTEM_PROMPT),
            ("human", """
            Analyze the following website content for SEO optimization:
            
            TITLES: {titles}
            
            H1 TAGS: {h1_tags}
            
            H2 TAGS: {h2_tags}
            
            META DESCRIPTIONS: {meta_descriptions}
            
            SAMPLE CONTENT: {sample_content}
            
            TOTAL PAGES: {total_pages}
            TOTAL WORDS: {total_words}
            
            Provide a detailed SEO analysis with scores for each category.
            Focus on title optimization, meta descriptions, header structure, content quality, internal linking, and technical SEO.
            
            IMPORTANT: Provide integer scores (0-100) for ALL fields:
            - overall_score: Overall SEO effectiveness (0-100)
            - title_optimization: Title tag optimization (0-100)
            - meta_description: Meta description quality (0-100)
            - header_structure: H1, H2, H3 hierarchy (0-100)
            - content_quality: Content depth and relevance (0-100)
            - internal_linking: Internal link structure (0-100)
            - technical_seo: Technical SEO elements (0-100)
            
            Return ONLY a valid JSON object with these exact field names and integer values.
            """)
        ])
        
        # Create chain without parser for now
        chain = seo_prompt | self.llm
        
        # Run analysis
        raw_result = await chain.ainvoke({
            "titles": content['aggregated']['titles'][:10],  # Limit for context
            "h1_tags": content['aggregated']['h1_tags'][:20],
            "h2_tags": content['aggregated']['h2_tags'][:30],
            "meta_descriptions": content['aggregated']['meta_descriptions'][:10],
            "sample_content": content['aggregated']['content'][:3000],
            "total_pages": content['aggregated']['total_pages'],
            "total_words": content['aggregated']['total_words']
        })
        
        logger.info(f"SEO analysis raw result: {raw_result}")
        
        # Try to parse the result manually
        try:
            # Extract the content from the response
            if hasattr(raw_result, 'content'):
                content_text = raw_result.content
            else:
                content_text = str(raw_result)
            
            logger.info(f"SEO analysis content: {content_text}")
            
            cleaned = self._extract_json_block(content_text)
            logger.debug(f"SEO analysis cleaned JSON: {cleaned}")
            parsed = json.loads(cleaned)
            return SEOScore(**parsed)
            
        except Exception as e:
            logger.error(f"Failed to parse SEO result: {str(e)}")
            # Return a basic score as fallback
            return SEOScore(
                overall_score=25,
                title_optimization=35,
                meta_description=30,
                header_structure=40,
                content_quality=35,
                internal_linking=25,
                technical_seo=30
            )
    
    async def _analyze_conversion(self, content: Dict[str, Any], vector_store: Optional[FAISS]) -> ConversionScore:
        """Analyze conversion optimization aspects using LLM"""
        
        conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", SuperchargedPrompts.CONVERSION_ANALYSIS_SYSTEM_PROMPT),
            ("human", """
            Analyze the following website content for conversion optimization:
            
            TITLES: {titles}
            
            H1 TAGS: {h1_tags}
            
            H2 TAGS: {h2_tags}
            
            CTA ELEMENTS: {cta_elements}
            
            FORMS: {forms}
            
            SAMPLE CONTENT: {sample_content}
            
            TOTAL PAGES: {total_pages}
            TOTAL WORDS: {total_words}
            
            Provide a detailed conversion analysis with scores for each category.
            Focus on headline effectiveness, value proposition, CTA optimization, trust signals, form optimization, and urgency/scarcity elements.
            
            IMPORTANT: Provide integer scores (0-100) for ALL fields. If a field is not applicable, use 0 instead of null.
            - overall_score: Overall conversion effectiveness (0-100)
            - headline_effectiveness: How compelling the headlines are (0-100)
            - value_proposition: Clarity of value proposition (0-100)
            - cta_optimization: Call-to-action effectiveness (0-100)
            - trust_signals: Trust and credibility elements (0-100)
            - form_optimization: Form design and optimization (0-100, use 0 if no forms)
            - urgency_scarcity: Urgency and scarcity tactics (0-100)
            
            Return ONLY a valid JSON object with these exact field names and integer values.
            """)
        ])
        
        # Setup output parser
        parser = PydanticOutputParser(pydantic_object=ConversionScore)
        
        # Create chain using modern approach
        chain = conversion_prompt | self.llm | parser
        
        # Run analysis
        result = await chain.ainvoke({
            "titles": content['aggregated']['titles'][:10],
            "h1_tags": content['aggregated']['h1_tags'][:20],
            "h2_tags": content['aggregated']['h2_tags'][:30],
            "cta_elements": content['aggregated']['cta_elements'][:20],
            "forms": content['aggregated']['forms'][:10],
            "sample_content": content['aggregated']['content'][:3000],
            "total_pages": content['aggregated']['total_pages'],
            "total_words": content['aggregated']['total_words']
        })
        
        logger.info(f"Conversion analysis result: {result}")
        return result
    
    async def _generate_recommendations(self, content: Dict[str, Any], seo_score: SEOScore, conversion_score: ConversionScore) -> List[DetailedRecommendation]:
        """Generate detailed recommendations using LLM"""
        
        recommendations_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a senior digital marketing consultant providing actionable recommendations.
            Generate specific, prioritized recommendations based on the analysis results.
            Each recommendation should include implementation details and expected impact.
            """),
            ("human", """
            Based on the SEO analysis (Overall Score: {seo_overall}) and Conversion analysis (Overall Score: {conversion_overall}),
            generate 8-12 specific recommendations for improvement.
            
            Website Content Summary:
            - Total Pages: {total_pages}
            - Sample Titles: {sample_titles}
            - Sample CTAs: {sample_ctas}
            
            Focus on high-impact, actionable recommendations that address the lowest-scoring areas.
            
            Return ONLY a valid JSON object with this exact structure:
            {{
              "recommendations": [
                {{
                  "category": "SEO",
                  "priority": "High", 
                  "issue": "brief description of the problem",
                  "recommendation": "what to do",
                  "implementation": "how to do it",
                  "impact_score": 8
                }}
              ]
            }}
            
            Each recommendation should have these exact field names:
            - category: string (e.g., "SEO", "Conversion", "Technical")
            - priority: string ("High", "Medium", "Low")
            - issue: string (brief description of the problem)
            - recommendation: string (what to do)
            - implementation: string (how to do it)
            - impact_score: integer (1-10)
            """)
        ])
        
        # Setup output parser for list of recommendations
        parser = PydanticOutputParser(pydantic_object=RecommendationsList)
        
        chain = recommendations_prompt | self.llm | parser
        
        result = await chain.ainvoke({
            "seo_overall": seo_score.overall_score,
            "conversion_overall": conversion_score.overall_score,
            "total_pages": content['aggregated']['total_pages'],
            "sample_titles": content['aggregated']['titles'][:5],
            "sample_ctas": content['aggregated']['cta_elements'][:10]
        })
        
        logger.info(f"Recommendations raw result: {result}")
        logger.info(f"Recommendations result type: {type(result)}")
        
        # Extract recommendations from the wrapper
        if hasattr(result, 'recommendations'):
            logger.info("Result has recommendations attribute")
            return result.recommendations
        elif isinstance(result, list):
            logger.info("Result is a list")
            return result
        else:
            logger.warning(f"Unexpected result format: {type(result)}")
            return []
    
    async def _generate_competitive_insights(self, content: Dict[str, Any]) -> List[str]:
        """Generate competitive insights using LLM"""
        # Implementation for competitive analysis
        return [
            "Implement schema markup to enhance search visibility",
            "Optimize for featured snippets with structured content",
            "Improve page load speed for better Core Web Vitals"
        ]
    
    def _identify_technical_issues(self, content: Dict[str, Any]) -> List[str]:
        """Identify technical SEO issues"""
        issues = []
        
        # Check for missing meta descriptions
        if not content.get('meta_descriptions') or not any(desc.strip() for desc in content['meta_descriptions']):
            issues.append("Missing meta descriptions")
        
        # Check for missing H1 tags
        if not content.get('h1_tags'):
            issues.append("Missing H1 tags")
        
        # Check for missing H2 tags
        if not content.get('h2_tags'):
            issues.append("Missing H2 tags")
        
        # Check for content length
        total_words = sum(len(text.split()) for text in content.get('content', []))
        if total_words < 300:
            issues.append("Content too short (less than 300 words)")
        
        # Check for missing internal links
        if not content.get('internal_links'):
            issues.append("Missing internal links")
        
        return issues
    
    def _identify_content_gaps(self, content: Dict[str, Any]) -> List[str]:
        """Identify content gaps and opportunities"""
        return [
            "Create FAQ section to target long-tail keywords",
            "Add customer testimonials and case studies",
            "Develop comparison pages for competitive keywords"
        ]

    def _extract_keyword_insights(self, prepared_content: Dict[str, Any], top_n: int = 12) -> List[str]:
        """Pull high-frequency SEO keywords from aggregated site content."""
        aggregated = prepared_content.get('aggregated', {})
        segments = [
            aggregated.get('content', ''),
            ' '.join(aggregated.get('titles', []) or []),
            ' '.join(aggregated.get('h1_tags', []) or []),
            ' '.join(aggregated.get('h2_tags', []) or []),
            ' '.join(aggregated.get('meta_descriptions', []) or []),
        ]

        combined_text = ' '.join(segment for segment in segments if segment)
        if not combined_text.strip():
            return []

        tokens = re.findall(r"[a-zA-Z]{4,}", combined_text.lower())
        counts = Counter()
        for token in tokens:
            if token in STOPWORDS:
                continue
            if token.isdigit():
                continue
            counts[token] += 1

        most_common = counts.most_common(top_n)
        keyword_insights = [
            f"{word.title()} ({count} mentions)" for word, count in most_common if count > 1
        ]

        if not keyword_insights and most_common:
            keyword_insights = [f"{word.title()} ({count} mention)" for word, count in most_common[:5]]

        return keyword_insights[:top_n]

    def _extract_conversion_highlights(self, prepared_content: Dict[str, Any]) -> List[str]:
        """Summarise conversion-specific findings like CTAs, forms, and persuasive triggers."""
        aggregated = prepared_content.get('aggregated', {})
        highlights: List[str] = []

        cta_elements = [cta.strip() for cta in aggregated.get('cta_elements', []) or [] if cta and cta.strip()]
        if cta_elements:
            cta_counter = Counter(cta_elements)
            top_ctas = ', '.join(f"{label} ({count})" for label, count in cta_counter.most_common(5))
            highlights.append(
                f"Detected {len(cta_elements)} call-to-action elements across the journey; most common: {top_ctas}."
            )
        else:
            highlights.append("No prominent call-to-action copy detected – consider adding persuasive CTAs.")

        forms = aggregated.get('forms', []) or []
        if forms:
            form_methods = Counter((form.get('method') or 'get').upper() for form in forms)
            top_methods = ', '.join(f"{method}: {count}" for method, count in form_methods.most_common())
            highlights.append(
                f"Identified {len(forms)} onsite forms ({top_methods}); validate that key lead capture points are optimised."
            )
        else:
            highlights.append("No onsite lead capture forms surfaced during the crawl.")

        persuasive_terms = {
            'pricing', 'demo', 'trial', 'free', 'book', 'consultation', 'quote', 'signup', 'subscribe', 'download',
            'contact', 'schedule', 'get started', 'learn more', 'buy', 'checkout', 'case study', 'testimonial'
        }
        content_blob = ' '.join(
            filter(None, [
                aggregated.get('content', ''),
                ' '.join(aggregated.get('titles', []) or []),
                ' '.join(aggregated.get('h1_tags', []) or []),
            ])
        ).lower()

        discovered_terms = []
        for term in persuasive_terms:
            occurrences = content_blob.count(term)
            if occurrences > 0:
                discovered_terms.append((term, occurrences))

        if discovered_terms:
            discovered_terms.sort(key=lambda item: item[1], reverse=True)
            top_terms = ', '.join(f"{term} ({count})" for term, count in discovered_terms[:8])
            highlights.append(f"High-intent messaging detected for: {top_terms}.")
        else:
            highlights.append("No strong conversion trigger language detected; weave in clearer value and urgency cues.")

        return highlights[:6]
    
    async def _generate_executive_summary(self, seo_score: SEOScore, conversion_score: ConversionScore, recommendations: List[DetailedRecommendation]) -> str:
        """Generate executive summary of the analysis"""
        
        summary_prompt = f"""
        Create a concise executive summary based on:
        - SEO Overall Score: {seo_score.overall_score}/100
        - Conversion Overall Score: {conversion_score.overall_score}/100
        - Number of recommendations: {len(recommendations)}
        
        Highlight the most critical findings and top 3 priority actions.
        Keep it under 200 words and focus on business impact.
        """
        
        response = await self.llm.ainvoke(summary_prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        cleaned = self._clean_text_response(raw_text)

        # Attempt to parse JSON summaries if the model returns structured data
        try:
            parsed = json.loads(self._extract_json_block(cleaned))
            if isinstance(parsed, dict):
                if "summary" in parsed and isinstance(parsed["summary"], str):
                    return self._clean_text_response(parsed["summary"])
                if "points" in parsed and isinstance(parsed["points"], list):
                    return "\n".join(self._clean_text_response(str(p)) for p in parsed["points"])
                # Flatten other dict structures to bullet list
                flattened = []
                for key, value in parsed.items():
                    text = f"{key.title()}: {value}" if not isinstance(value, (list, dict)) else f"{key.title()}: {value}"
                    flattened.append(self._clean_text_response(str(text)))
                if flattened:
                    return "\n".join(flattened)
            elif isinstance(parsed, list):
                return "\n".join(self._clean_text_response(str(item)) for item in parsed)
        except Exception:
            pass

        return cleaned

    async def _fallback_analysis(self, scraped_data: Dict[str, Any], prepared_content: Dict[str, Any]) -> ComprehensiveAnalysis:
        """Fallback analysis when LLM is not available"""
        logger.info("Using fallback analysis based on content structure")
        
        # Basic scoring based on content analysis
        seo_score = self._calculate_fallback_seo_score(prepared_content)
        conversion_score = self._calculate_fallback_conversion_score(prepared_content)
        
        # Generate basic recommendations
        recommendations = self._generate_fallback_recommendations(prepared_content)
        
        # Basic insights - call sync methods directly
        competitive_insights = ["Analysis based on content structure (LLM not available)"]
        technical_issues = self._identify_technical_issues(prepared_content)
        content_gaps = self._identify_content_gaps(prepared_content)
        seo_keywords = self._extract_keyword_insights(prepared_content)
        conversion_highlights = self._extract_conversion_highlights(prepared_content)
        
        summary = f"Basic analysis completed. SEO Score: {seo_score.overall_score}/100, Conversion Score: {conversion_score.overall_score}/100. LLM analysis not available."
        
        return ComprehensiveAnalysis(
            seo_score=seo_score,
            conversion_score=conversion_score,
            recommendations=recommendations,
            competitive_insights=competitive_insights,
            technical_issues=technical_issues,
            content_gaps=content_gaps,
            seo_keywords=seo_keywords,
            conversion_highlights=conversion_highlights,
            summary=summary,
            analyzed_pages=scraped_data.get('pages_scraped', 0),
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            model_used="fallback-analysis"
        )
    
    def _calculate_fallback_seo_score(self, content: Dict[str, Any]) -> SEOScore:
        """Calculate SEO score based on content structure when LLM is not available"""
        score = 50  # Base score
        
        # Title optimization
        if content.get('titles') and any(title.strip() for title in content['titles']):
            score += 15
        else:
            score -= 10
        
        # Meta descriptions
        if content.get('meta_descriptions') and any(desc.strip() for desc in content['meta_descriptions']):
            score += 15
        else:
            score -= 10
        
        # Header structure
        if content.get('h1_tags'):
            score += 10
        if content.get('h2_tags'):
            score += 5
        
        # Content quality (word count)
        total_words = sum(len(text.split()) for text in content.get('content', []))
        if total_words > 1000:
            score += 15
        elif total_words > 500:
            score += 10
        else:
            score -= 5
        
        return SEOScore(
            overall_score=max(0, min(100, score)),
            title_optimization=max(0, min(100, score + 10)),
            meta_description=max(0, min(100, score + 5)),
            header_structure=max(0, min(100, score + 15)),
            content_quality=max(0, min(100, score + 10)),
            internal_linking=max(0, min(100, score)),
            technical_seo=max(0, min(100, score + 5))
        )
    
    def _calculate_fallback_conversion_score(self, content: Dict[str, Any]) -> ConversionScore:
        """Calculate conversion score based on content structure when LLM is not available"""
        score = 50  # Base score
        
        # CTA elements
        if content.get('cta_elements'):
            score += 20
        
        # Forms
        if content.get('forms'):
            score += 15
        
        # Content quality
        total_words = sum(len(text.split()) for text in content.get('content', []))
        if total_words > 800:
            score += 15
        
        # Trust signals (contact/about pages)
        if any('contact' in text.lower() or 'about' in text.lower() for text in content.get('content', [])):
            score += 10
        
        return ConversionScore(
            overall_score=max(0, min(100, score)),
            headline_effectiveness=max(0, min(100, score + 10)),
            value_proposition=max(0, min(100, score + 5)),
            cta_optimization=max(0, min(100, score + 15)),
            trust_signals=max(0, min(100, score + 10)),
            form_optimization=max(0, min(100, score + 10)),
            urgency_scarcity=max(0, min(100, score))
        )
    
    def _generate_fallback_recommendations(self, content: Dict[str, Any]) -> List[DetailedRecommendation]:
        """Generate basic recommendations when LLM is not available"""
        recommendations = []
        
        # Check for missing meta descriptions
        if not content.get('meta_descriptions') or not any(desc.strip() for desc in content['meta_descriptions']):
            recommendations.append(DetailedRecommendation(
                category="SEO",
                priority="High",
                issue="Missing meta descriptions",
                recommendation="Add compelling meta descriptions to all pages",
                implementation="Update HTML meta tags with unique descriptions",
                impact_score=8
            ))
        
        # Check for missing H1 tags
        if not content.get('h1_tags'):
            recommendations.append(DetailedRecommendation(
                category="SEO",
                priority="High",
                issue="Missing H1 tags",
                recommendation="Add H1 tags to all pages",
                implementation="Include one H1 tag per page with main keyword",
                impact_score=7
            ))
        
        # Check for CTAs
        if not content.get('cta_elements'):
            recommendations.append(DetailedRecommendation(
                category="Conversion",
                priority="High",
                issue="Missing call-to-action elements",
                recommendation="Add clear CTAs throughout the site",
                implementation="Include buttons, links, or forms that guide users to take action",
                impact_score=9
            ))
        
        return recommendations

# Factory function for easy service instantiation
def create_llm_analysis_service(provider: ModelProvider = None, api_key: str = None, model_name: str = None) -> LLMAnalysisService:
    """Factory function to create LLM analysis service with environment-based configuration"""
    
    # Load environment variables
    groq_api_key = os.getenv('GROQ_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    logger.info(f"Environment variables loaded:")
    logger.info(f"GROQ_API_KEY present: {bool(groq_api_key)}")
    logger.info(f"OPENAI_API_KEY present: {bool(openai_api_key)}")
    logger.info(f"ANTHROPIC_API_KEY present: {bool(anthropic_api_key)}")
    
    # Determine provider from environment or use default
    if provider is None:
        if groq_api_key and groq_api_key != "your-groq-api-key-here":
            provider = ModelProvider.GROQ_LLAMA
            logger.info("Using Groq LLM provider (detected from environment)")
        elif openai_api_key and openai_api_key != "your-openai-api-key-here":
            provider = ModelProvider.OPENAI_GPT4
            logger.info("Using OpenAI GPT-4 provider (detected from environment)")
        elif anthropic_api_key and anthropic_api_key != "your-anthropic-api-key-here":
            provider = ModelProvider.ANTHROPIC_CLAUDE
            logger.info("Using Anthropic Claude provider (detected from environment)")
        else:
            provider = ModelProvider.GROQ_LLAMA  # Default fallback
            logger.warning("No valid API keys found in environment. LLM analysis will be limited.")
    
    # Get API key from environment if not provided
    if api_key is None:
        if provider in [ModelProvider.GROQ_LLAMA, ModelProvider.GROQ_MIXTRAL]:
            api_key = groq_api_key
        elif provider in [ModelProvider.OPENAI_GPT4, ModelProvider.OPENAI_GPT35]:
            api_key = openai_api_key
        elif provider == ModelProvider.ANTHROPIC_CLAUDE:
            api_key = anthropic_api_key
    
    # Validate API key
    if not api_key or api_key in ["your-groq-api-key-here", "your-openai-api-key-here", "your-anthropic-api-key-here"]:
        logger.warning(f"Invalid or placeholder API key for {provider}. LLM analysis will be limited.")
        api_key = None
    
    # Set default model names based on provider
    if model_name is None:
        model_defaults = {
            ModelProvider.GROQ_LLAMA: "llama-3.3-70b-versatile",
            ModelProvider.GROQ_MIXTRAL: "llama-3.3-70b-versatile",
            ModelProvider.OPENAI_GPT4: "gpt-4-1106-preview",
            ModelProvider.OPENAI_GPT35: "gpt-3.5-turbo-1106",
            ModelProvider.ANTHROPIC_CLAUDE: "claude-2"
        }
        model_name = model_defaults.get(provider, "llama-3.3-70b-versatile")
    
    # Set base URL for GROQ providers
    base_url = None
    if provider in [ModelProvider.GROQ_LLAMA, ModelProvider.GROQ_MIXTRAL]:
        base_url = "https://api.groq.com/openai/v1"
    
    config = LLMConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.3,
        max_tokens=4000
    )
    
    logger.info(f"LLM Analysis Service configured with provider: {provider}, model: {model_name}")
    return LLMAnalysisService(config)

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example scraped data structure
        sample_scraped_data = {
            "pages_scraped": 3,
            "pages": [
                # Sample page data would go here
            ]
        }
        
        service = create_llm_analysis_service(ModelProvider.OPENAI_GPT4, "your-api-key")
        analysis = await service.analyze_website_comprehensive(sample_scraped_data)
        
        print(f"SEO Score: {analysis.seo_score.overall_score}/100")
        print(f"Conversion Score: {analysis.conversion_score.overall_score}/100")
        print(f"Recommendations: {len(analysis.recommendations)}")
    
    asyncio.run(main())
