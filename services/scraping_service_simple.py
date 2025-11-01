"""
Simplified Web Scraping Service for Testing
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl
from collections import deque
import re

@dataclass
class PageContent:
    """Simplified page content data"""
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

@dataclass
class ScrapingConfig:
    """Scraping configuration"""
    max_pages: int = 10
    max_depth: int = 3
    timeout: int = 30
    delay_between_requests: float = 1.0
    respect_robots_txt: bool = True
    user_agent: str = "SEO-Analyzer-Bot/1.0"

def scrape_single_page_simple(url: str) -> Optional[PageContent]:
    """Simple page scraping using requests + BeautifulSoup"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        load_time = time.time() - start_time
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract content
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ""
        
        h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text().strip() for h2 in soup.find_all('h2')]
        
        # Get all text content
        content_text = soup.get_text(separator=' ', strip=True)
        word_count = len(content_text.split())
        
        # Find links
        internal_links = []
        external_links = []
        domain = _canonical_domain(urlparse(url).netloc)

        seen_internal: Set[str] = set()
        seen_external: Set[str] = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            if not parsed_url.scheme.startswith('http'):
                continue
            normalized = _normalize_url(full_url)
            target_domain = _canonical_domain(parsed_url.netloc)

            if target_domain == domain:
                if normalized not in seen_internal:
                    internal_links.append(normalized)
                    seen_internal.add(normalized)
            elif parsed_url.netloc:
                if normalized not in seen_external:
                    external_links.append(normalized)
                    seen_external.add(normalized)
        
        # Find images
        images = []
        for img in soup.find_all('img'):
            images.append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        # Find forms
        forms = []
        for form in soup.find_all('form'):
            forms.append({
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'id': form.get('id', ''),
                'class': ' '.join(form.get('class', []))
            })
        
        # Find potential CTAs
        cta_elements = []
        cta_selectors = ['button', '.btn', '.cta', '[class*="button"]', '[class*="cta"]']
        for selector in cta_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text:
                    cta_elements.append(text)
        
        return PageContent(
            url=url,
            title=title_text,
            meta_description=meta_description,
            h1_tags=h1_tags,
            h2_tags=h2_tags,
            content_text=content_text,
            word_count=word_count,
            internal_links=internal_links,
            external_links=external_links,
            images=images[:5],  # Limit to first 5
            forms=forms,
            cta_elements=cta_elements[:10],  # Limit to first 10
            schema_markup=[],  # Simplified - no schema parsing
            page_load_time=round(load_time, 2),
            status_code=response.status_code,
            scraped_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def _normalize_url(raw_url: str) -> str:
    """Normalize URLs for consistent comparison."""
    parsed = urlparse(raw_url)
    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
    query_pairs.sort()
    query = "&".join(f"{k}={v}" for k, v in query_pairs)
    normalized = parsed._replace(path=path, params="", query=query, fragment="")
    return urlunparse(normalized)


def _canonical_domain(netloc: str) -> str:
    """Return canonical representation of a host for comparison."""
    return netloc.lower().lstrip("www.")


async def scrape_website_intelligent(url: str, config: Optional[ScrapingConfig] = None) -> Dict[str, Any]:
    """Simplified website scraping"""
    if config is None:
        config = ScrapingConfig()
    
    print(f"Scraping {url} (simplified mode)...")
    
    pages: List[PageContent] = []
    pages_failed = 0
    start_time = time.time()

    normalized_start = _normalize_url(url)
    domain = _canonical_domain(urlparse(normalized_start).netloc)
    queue: deque[Tuple[str, int]] = deque([(normalized_start, 0)])
    queued: Set[str] = {normalized_start}
    visited: Set[str] = set()

    while queue and len(pages) < config.max_pages:
        current_url, depth = queue.popleft()
        if current_url in visited:
            continue

        page_data = scrape_single_page_simple(current_url)
        visited.add(current_url)

        if page_data:
            pages.append(page_data)
            print(f"✓ Scraped: {current_url}")

            if depth < config.max_depth:
                for link in page_data.internal_links:
                    normalized_link = _normalize_url(link)
                    parsed_link = urlparse(normalized_link)
                    if parsed_link.scheme not in ("http", "https"):
                        continue
                    if _canonical_domain(parsed_link.netloc) != domain:
                        continue
                    if normalized_link in visited or normalized_link in queued:
                        continue
                    queue.append((normalized_link, depth + 1))
                    queued.add(normalized_link)
        else:
            pages_failed += 1
            print(f"✗ Failed: {current_url}")

        if queue and config.delay_between_requests > 0:
            time.sleep(config.delay_between_requests)
    
    total_time = time.time() - start_time
    
    return {
        "success": len(pages) > 0,
        "pages_scraped": len(pages),
        "pages_failed": pages_failed,
        "total_time": round(total_time, 2),
        "pages": pages,
        "metadata": {
            "start_url": url,
            "config": config.__dict__
        }
    }

# For compatibility with existing code
def extract_links_with_playwright(start_url, max_pages=10):
    """Compatibility function"""
    return [start_url]

def analyze_page_with_playwright(url):
    """Compatibility function"""
    page_data = scrape_single_page_simple(url)
    if not page_data:
        return 0, {}
    
    score = 0
    results = {}
    
    # Simple scoring based on content
    results["Email Capture"] = 1 if any('email' in form.get('action', '').lower() for form in page_data.forms) else 0
    results["Value Offers"] = 1 if any(keyword in page_data.content_text.lower() for keyword in ['free', 'download', 'trial']) else 0
    results["CTAs"] = 1 if page_data.cta_elements else 0
    results["Popups"] = 0  # Can't detect without JavaScript
    results["Persuasive Copy"] = 1 if any(word in page_data.content_text.lower() for word in ['exclusive', 'limited', 'guarantee']) else 0
    results["Trust Signals"] = 1 if 'testimonial' in page_data.content_text.lower() else 0
    
    score = sum(results.values())
    return score, results

def analyze_full_site(url):
    """Compatibility function for existing code"""
    import asyncio
    result = asyncio.run(scrape_website_intelligent(url, ScrapingConfig(max_pages=5)))
    
    if not result['success']:
        return 0, {}, 0
    
    total_score = 0
    combined_scores = {
        "Email Capture": 0,
        "Value Offers": 0,
        "CTAs": 0,
        "Popups": 0,
        "Persuasive Copy": 0,
        "Trust Signals": 0,
    }
    
    for page in result['pages']:
        score, details = analyze_page_with_playwright(page.url)
        total_score += score
        for key in combined_scores:
            combined_scores[key] += details.get(key, 0)
    
    num_pages = len(result['pages'])
    normalized = {k: round((v / num_pages) * 100, 2) for k, v in combined_scores.items()}
    
    return total_score, normalized, num_pages
