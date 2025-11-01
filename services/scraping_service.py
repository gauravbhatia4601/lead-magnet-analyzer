"""
Advanced Web Scraping Service with Intelligence and Security
"""

import asyncio
import aiohttp
import time
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import deque
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
from bs4 import BeautifulSoup
import hashlib
import logging
from contextlib import asynccontextmanager
import redis
from pydantic import BaseModel, HttpUrl, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PageContent:
    """Structured page content data"""
    url: str
    title: str
    meta_description: str
    h1_tags: List[str]
    h2_tags: List[str]
    content_text: str
    word_count: int
    internal_links: List[str]
    external_links: List[str]
    images: List[Dict[str, str]]
    forms: List[Dict[str, str]]
    cta_elements: List[str]
    schema_markup: List[Dict]
    page_load_time: float
    status_code: int
    scraped_at: str

class ScrapingConfig(BaseModel):
    """Scraping configuration with validation"""
    max_pages: int = 10
    max_depth: int = 3
    timeout: int = 30000
    delay_between_requests: float = 1.0
    respect_robots_txt: bool = True
    user_agent: str = "SEO-Analyzer-Bot/1.0"
    allowed_domains: Optional[List[str]] = None
    blocked_paths: List[str] = ["/admin", "/wp-admin", "/login"]
    
    @validator('max_pages')
    def validate_max_pages(cls, v):
        if v > 50:  # Security limit
            raise ValueError('max_pages cannot exceed 50')
        return v

class IntelligentScraper:
    """Advanced web scraper with security and intelligence features"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.robots_rules: Dict[str, Dict[str, List[str]]] = {}

    def _canonical_domain(self, netloc: str) -> str:
        """Return canonical representation of a host for comparison."""
        return netloc.lower().lstrip("www.")

    def _normalize_url(self, raw_url: str) -> str:
        """Normalize URLs to reduce duplicates while preserving meaningful structure."""
        parsed = urlparse(raw_url)
        if not parsed.scheme or not parsed.netloc:
            return raw_url

        path = re.sub(r"/+", "/", parsed.path or "/")
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_pairs = [
            (k, v) for k, v in query_pairs
            if k.lower() not in {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
        ]
        filtered_pairs.sort()
        query = urlencode(filtered_pairs)

        normalized = parsed._replace(path=path, params="", query=query, fragment="")
        return urlunparse(normalized)

    async def _load_robots_rules(self, start_url: str) -> None:
        """Fetch and parse robots.txt rules for the target domain."""
        if not self.config.respect_robots_txt:
            return

        parsed = urlparse(start_url)
        domain_key = self._canonical_domain(parsed.netloc)
        if not domain_key or domain_key in self.robots_rules:
            return

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        logger.info(f"Fetching robots.txt from {robots_url}")

        rules: Dict[str, List[str]] = {"disallow": [], "allow": []}

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {"User-Agent": self.config.user_agent}
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(robots_url, headers=headers) as response:
                    if response.status != 200:
                        self.robots_rules[domain_key] = rules
                        return
                    body = await response.text()
        except Exception as exc:
            logger.debug(f"robots.txt fetch failed ({robots_url}): {exc}")
            self.robots_rules[domain_key] = rules
            return

        active_agent = None
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            key, _, value = line.partition(':')
            if not _:
                continue
            key_lower = key.strip().lower()
            rule_value = value.strip()

            if key_lower == 'user-agent':
                active_agent = rule_value.lower()
            elif key_lower == 'disallow' and rule_value:
                if active_agent in (None, '*') or active_agent == self.config.user_agent.lower():
                    rules['disallow'].append(rule_value)
            elif key_lower == 'allow' and rule_value:
                if active_agent in (None, '*') or active_agent == self.config.user_agent.lower():
                    rules['allow'].append(rule_value)

        self.robots_rules[domain_key] = rules

    def _path_matches_rule(self, path: str, rule: str) -> bool:
        if not rule:
            return False
        if rule == '/':
            return True
        if not rule.startswith('/'):
            rule = f"/{rule}"
        return path.startswith(rule)

    def _is_allowed_by_robots(self, url: str) -> bool:
        if not self.config.respect_robots_txt:
            return True

        parsed = urlparse(url)
        domain_key = self._canonical_domain(parsed.netloc)
        if not domain_key:
            return False

        rules = self.robots_rules.get(domain_key)
        if not rules:
            return True

        path = parsed.path or '/'
        for allow_rule in rules.get('allow', []):
            if self._path_matches_rule(path, allow_rule):
                return True
        for disallow_rule in rules.get('disallow', []):
            if self._path_matches_rule(path, disallow_rule):
                return False
        return True
    
    async def scrape_website(self, start_url: str) -> Dict[str, any]:
        """Main scraping orchestrator"""
        logger.info(f"Starting intelligent scrape of {start_url}")
        
        # Validate URL
        if not self._is_valid_url(start_url):
            raise ValueError(f"Invalid URL: {start_url}")
        
        # Check rate limiting
        if not self._check_rate_limit(start_url):
            raise Exception("Rate limit exceeded for this domain")
        
        await self._load_robots_rules(start_url)

        self.visited_urls.clear()
        self.failed_urls.clear()

        scraped_pages = []
        start_time = time.time()
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                user_agent=self.config.user_agent,
                viewport={'width': 1280, 'height': 720},
                java_script_enabled=True,
            )
            context.set_default_navigation_timeout(self.config.timeout)
            
            try:
                # Get all URLs to scrape
                urls_to_scrape = await self._discover_urls(context, start_url)
                
                # Scrape each page
                for url in urls_to_scrape[:self.config.max_pages]:
                    try:
                        if not self._is_allowed_by_robots(url):
                            logger.info(f"Skipping {url} due to robots.txt restrictions")
                            continue

                        page_data = await self._scrape_single_page(context, url)
                        if page_data:
                            scraped_pages.append(page_data)
                            logger.info(f"Successfully scraped: {url}")
                        
                        # Respectful delay
                        await asyncio.sleep(self.config.delay_between_requests)
                        
                    except Exception as e:
                        logger.error(f"Failed to scrape {url}: {str(e)}")
                        self.failed_urls.add(url)
                        continue
                        
            finally:
                await context.close()
                await browser.close()
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "pages_scraped": len(scraped_pages),
            "pages_failed": len(self.failed_urls),
            "total_time": round(total_time, 2),
            "pages": scraped_pages,
            "metadata": {
                "session_id": self.session_id,
                "start_url": start_url,
                "config": self.config.model_dump()
            }
        }
    
    async def _discover_urls(self, context, start_url: str) -> List[str]:
        """Intelligent URL discovery with depth control"""
        normalized_start = self._normalize_url(start_url)
        discovered_urls: Set[str] = set()
        ordered_urls: List[str] = []
        to_visit = deque([(normalized_start, 0)])  # (url, depth)
        discovered_urls.add(normalized_start)
        ordered_urls.append(normalized_start)
        domain = self._canonical_domain(urlparse(normalized_start).netloc)

        max_discovery = min(self.config.max_pages * max(3, self.config.max_depth + 1), 500)

        page = await context.new_page()

        try:
            while to_visit and len(discovered_urls) < max_discovery:
                current_url, depth = to_visit.popleft()

                if depth > self.config.max_depth:
                    continue
                
                if current_url in self.visited_urls:
                    continue
                    
                if not self._is_allowed_by_robots(current_url):
                    logger.info(f"Discovery skipping {current_url} (robots disallow)")
                    continue

                try:
                    await page.goto(current_url)
                    self.visited_urls.add(current_url)
                    
                    # Extract links
                    links = await page.evaluate("""
                        () => {
                            return Array.from(document.querySelectorAll('a[href]'))
                                .map(a => a.href)
                                .filter(href => href.startsWith('http'));
                        }
                    """)
                    
                    for link in links:
                        parsed = urlparse(link)

                        target_domain = self._canonical_domain(parsed.netloc)
                        if not target_domain or target_domain != domain:
                            continue
                            
                        clean_url = self._normalize_url(link)
                        parsed_clean = urlparse(clean_url)

                        # Skip blocked paths
                        if any(blocked in parsed_clean.path for blocked in self.config.blocked_paths):
                            continue

                        if not self._is_allowed_by_robots(clean_url):
                            continue
                            
                        if clean_url not in discovered_urls:
                            discovered_urls.add(clean_url)
                            ordered_urls.append(clean_url)
                            if depth < self.config.max_depth:
                                to_visit.append((clean_url, depth + 1))
                            
                except Exception as e:
                    logger.warning(f"Failed to discover URLs from {current_url}: {str(e)}")
                    continue
                    
        finally:
            await page.close()
            
        return ordered_urls

    async def _scrape_single_page(self, context, url: str) -> Optional[PageContent]:
        """Scrape individual page with comprehensive content extraction"""
        page_start_time = time.time()
        
        page = await context.new_page()
        
        try:
            # Navigate to page
            response = await page.goto(url, wait_until="domcontentloaded")
            
            if not response or response.status >= 400:
                return None
            
            # Wait for dynamic content
            await page.wait_for_timeout(2000)
            
            # Extract comprehensive page data
            page_data = await page.evaluate("""
                () => {
                    // Helper function to extract text content
                    const getTextContent = (elements) => {
                        return Array.from(elements).map(el => el.textContent.trim()).filter(text => text.length > 0);
                    };
                    
                    // Helper function to extract element attributes
                    const getElementData = (selector, attributes) => {
                        return Array.from(document.querySelectorAll(selector)).map(el => {
                            const data = {};
                            attributes.forEach(attr => {
                                data[attr] = el.getAttribute(attr) || el[attr] || '';
                            });
                            return data;
                        });
                    };
                    
                    return {
                        title: document.title || '',
                        meta_description: (document.querySelector('meta[name="description"]') || {}).content || '',
                        h1_tags: getTextContent(document.querySelectorAll('h1')),
                        h2_tags: getTextContent(document.querySelectorAll('h2')),
                        content_text: document.body.innerText || '',
                        internal_links: Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => href.includes(window.location.hostname)),
                        external_links: Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => !href.includes(window.location.hostname) && href.startsWith('http')),
                        images: getElementData('img', ['src', 'alt', 'title']),
                        forms: getElementData('form', ['action', 'method', 'id', 'class']),
                        cta_elements: getTextContent(document.querySelectorAll('button, .btn, .cta, [class*="button"], [class*="cta"]')),
                        schema_markup: Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                            .map(script => {
                                try { return JSON.parse(script.textContent); }
                                catch(e) { return null; }
                            }).filter(data => data !== null)
                    };
                }
            """)
            
            page_load_time = time.time() - page_start_time
            
            return PageContent(
                url=url,
                title=page_data['title'],
                meta_description=page_data['meta_description'],
                h1_tags=page_data['h1_tags'],
                h2_tags=page_data['h2_tags'],
                content_text=page_data['content_text'],
                word_count=len(page_data['content_text'].split()),
                internal_links=page_data['internal_links'],
                external_links=page_data['external_links'],
                images=page_data['images'],
                forms=page_data['forms'],
                cta_elements=page_data['cta_elements'],
                schema_markup=page_data['schema_markup'],
                page_load_time=round(page_load_time, 2),
                status_code=response.status,
                scraped_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
            
        finally:
            await page.close()
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL security and format"""
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in ['http', 'https'],
                parsed.netloc,
                not any(blocked in parsed.netloc.lower() for blocked in ['localhost', '127.0.0.1', '0.0.0.0'])
            ])
        except:
            return False
    
    def _check_rate_limit(self, url: str) -> bool:
        """Check rate limiting per domain"""
        domain = urlparse(url).netloc
        key = f"rate_limit:{domain}"
        
        try:
            current_count = self.redis_client.get(key)
            if current_count and int(current_count) >= 100:  # Max 100 requests per hour per domain
                return False
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 3600)  # 1 hour expiry
            pipe.execute()
            
            return True
        except:
            # If Redis is unavailable, allow the request but log warning
            logger.warning("Redis unavailable for rate limiting")
            return True

# Factory function for easy instantiation
async def scrape_website_intelligent(url: str, config: Optional[ScrapingConfig] = None) -> Dict[str, any]:
    """Factory function to scrape a website with intelligent features"""
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright is not available in the current environment")

    if config is None:
        config = ScrapingConfig()
    
    scraper = IntelligentScraper(config)
    return await scraper.scrape_website(url)

# Example usage
if __name__ == "__main__":
    async def main():
        config = ScrapingConfig(
            max_pages=5,
            max_depth=2,
            delay_between_requests=1.5
        )
        
        result = await scrape_website_intelligent("https://technioz.com", config)
        print(f"Scraped {result['pages_scraped']} pages in {result['total_time']} seconds")
        
        # Print first page data as example
        if result['pages']:
            page = result['pages'][0]
            print(f"Title: {page.title}")
            print(f"Word count: {page.word_count}")
            print(f"H1 tags: {page.h1_tags}")
    
    asyncio.run(main())
