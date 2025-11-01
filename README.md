# AI-Powered Website SEO & Conversion Analyzer 🚀

A sophisticated AI-driven tool that analyzes websites for SEO optimization and conversion effectiveness using advanced LLM technology (Groq, OpenAI, Anthropic) and intelligent web scraping.

## 🎯 What This Tool Does

This tool accepts a website URL and provides comprehensive analysis by:

1. Intelligent Web Scraping: Crawls the entire website to find public pages and extract content
2. AI-Powered Analysis: Feeds scraped content to advanced LLMs using LangChain
3. Supercharged System Prompts: Uses expert-level prompts to analyze SEO and conversion parameters
4. Comprehensive Scoring: Provides detailed scores for SEO and conversion optimization
5. Actionable Recommendations: Generates prioritized improvement suggestions

## 🔍 Analysis Parameters

### SEO Analysis (0-100 Scale)
- Title Optimization: Meta title effectiveness and keyword targeting
- Meta Description: Meta description quality and click-through potential
- Header Structure: H1, H2, H3 hierarchy and semantic organization
- Content Quality: Content depth, relevance, and value
- Internal Linking: Internal link structure and navigation
- Technical SEO: Core Web Vitals, schema markup, and technical elements

### Conversion Analysis (0-100 Scale)
- Headline Effectiveness: Compelling and persuasive headlines
- Value Proposition: Clarity of value and benefits
- CTA Optimization: Call-to-action button effectiveness
- Trust Signals: Testimonials, social proof, and credibility
- Form Optimization: Lead capture form design and UX
- Urgency & Scarcity: Time-sensitive and limited offers

## 🚀 Features

- Multi-LLM Support: Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant), OpenAI GPT-4, Anthropic Claude
- Intelligent Scraping: Respects robots.txt, configurable depth and page limits
- Real-time Analysis: Fast processing with configurable timeouts
- Structured Output: JSON responses formatted for frontend integration
- Smart Fallback: Automatic fallback to basic analysis when AI services unavailable
- Scalable Architecture: Microservices design with API Gateway

## 🛠️ Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd Magentix
   ```

2. Create virtual environment
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables
   ```bash
   export GROQ_API_KEY="your-groq-api-key"
   export JWT_SECRET="your-jwt-secret"
   export ENVIRONMENT="development"
   ```

## 🎯 Usage

### Start the Server

```bash
python3 -m uvicorn api.main_api:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Main Analysis Endpoint (Recommended)
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://technioz.com",
    "analysis_type": "comprehensive",
    "max_pages": 10,
    "include_technical_seo": true,
    "include_competitor_insights": true
  }'
```

Analysis Types:
- `"comprehensive"` (default): Tries AI analysis first, falls back to basic if no API keys
- `"basic": Scraping + basic scoring (no AI processing)
- `"ai": AI analysis only (if API keys available)

Request Parameters:
- `url`: Website URL to analyze (required)
- `analysis_type`: Type of analysis to perform
- `max_pages`: Maximum pages to scrape (1-50, default: 10)
- `include_technical_seo`: Include technical SEO analysis (default: true)
- `include_competitor_insights`: Include competitive insights (default: true)

### Example Response

```json
{
  "success": true,
  "metadata": {
    "analysis_id": "uuid",
    "requested_url": "https://example.com",
    "pages_analyzed": 5,
    "analysis_duration": 12.5,
    "model_used": "llama-3.3-70b-versatile"
  },
  "seo_analysis": {
    "overall_score": 75,
    "title_optimization": 80,
    "meta_description": 70,
    "header_structure": 85,
    "content_quality": 75,
    "internal_linking": 65,
    "technical_seo": 70
  },
  "conversion_analysis": {
    "overall_score": 68,
    "headline_effectiveness": 75,
    "value_proposition": 70,
    "cta_optimization": 60,
    "trust_signals": 80,
    "form_optimization": 65,
    "urgency_scarcity": 55
  },
  "recommendations": [
    {
      "category": "SEO",
      "priority": "High",
      "issue": "Missing meta descriptions",
      "recommendation": "Add compelling meta descriptions to all pages",
      "implementation": "Update HTML meta tags with unique descriptions",
      "impact_score": 8
    }
  ]
}
```

## 🔧 Configuration

### Scraping Configuration
```python
scraping_config = ScrapingConfig(
    max_pages=5,           # Maximum pages to scrape
    max_depth=3,           # Maximum crawl depth
    delay_between_requests=1.0,  # Delay between requests
    respect_robots_txt=True      # Respect robots.txt
)
```

### LLM Configuration
```python
llm_config = LLMConfig(
    provider=ModelProvider.GROQ_LLAMA,  # Groq, OpenAI, or Anthropic
    model_name="llama-3.3-70b-versatile",  # Model to use
    temperature=0.3,                    # Creativity vs consistency
    max_tokens=4000                     # Maximum response length
)
```

## 🏗️ Architecture

- API Gateway: FastAPI-based main application
- Scraping Service: Intelligent web scraping with BeautifulSoup
- LLM Analysis Service: LangChain-powered AI analysis with smart fallback
- Security Service: JWT authentication and rate limiting
- Data Layer: Redis caching and PostgreSQL storage (planned)

## 🔑 API Keys

### Groq (Recommended)
- API Key: Get from [Groq Console](https://console.groq.com/)
- Models: llama-3.3-70b-versatile, llama-3.1-8b-instant
- Cost: Very affordable, fast inference

### OpenAI
- API Key: Get from [OpenAI Platform](https://platform.openai.com/)
- Models: GPT-4, GPT-3.5-turbo
- Cost: Higher cost, excellent quality

### Anthropic
- API Key: Get from [Anthropic Console](https://console.anthropic.com/)
- Models: Claude-2, Claude-3
- Cost: Competitive pricing, high quality

## 🚀 Quick Start

1. Set your API key
   ```bash
   export GROQ_API_KEY="your-key-here"
   ```

2. Start the server
   ```bash
   python3 -m uvicorn api.main_api:app --reload
   ```

3. Test with a website
   ```bash
   curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://technioz.com", "analysis_type": "comprehensive"}'
   ```

## 📊 Use Cases

- SEO Audits: Comprehensive website SEO analysis
- Conversion Optimization: Identify conversion barriers and opportunities
- Competitive Analysis: Benchmark against industry standards
- Content Strategy: Identify content gaps and optimization opportunities
- Technical SEO: Find technical issues affecting rankings
- Marketing Agencies: Provide detailed client reports

## 🔒 Security & Ethics

- Rate Limiting: Built-in request throttling
- Robots.txt Respect: Follows website crawling guidelines
- User Authentication: JWT-based secure access
- Input Validation: Comprehensive URL and input sanitization
- Audit Logging: Track all analysis requests

## 🐛 Troubleshooting

### Common Issues

1. LLM Service Not Available
   - Check API key configuration
   - Verify model availability
   - Check API rate limits
   - Note: Service will automatically fall back to basic analysis

2. Scraping Failures
   - Verify URL accessibility
   - Check robots.txt restrictions
   - Increase timeout values

3. Memory Issues
   - Reduce max_pages in scraping config
   - Lower max_tokens in LLM config
   - Use smaller models for large sites

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for educational and analysis purposes. Always respect websites' terms of service and robots.txt files. Use responsibly and ethically.

Built using FastAPI, LangChain, and Groq LLM

Transform your website analysis with AI-powered insights!
