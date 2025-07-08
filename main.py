from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import time
from typing import Optional

def extract_links_with_playwright(start_url, max_pages=10):
    visited = set()
    to_visit = [start_url]
    domain = urlparse(start_url).netloc
    collected_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while to_visit and len(visited) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue

            try:
                page.goto(current_url, timeout=15000)
                visited.add(current_url)
                collected_links.append(current_url)

                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(current_url, href)
                    parsed = urlparse(full_url)
                    if parsed.netloc == domain and full_url not in visited and full_url not in to_visit:
                        to_visit.append(full_url)
            except:
                continue

        browser.close()
    return collected_links

def analyze_page_with_playwright(url):
    score = 0
    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ').lower()

        # Email capture
        email_forms = soup.find_all('form')
        email_inputs = [inp for inp in soup.find_all('input') if 'email' in inp.get('name', '').lower() or 'email' in inp.get('type', '').lower()]
        results["Email Capture"] = 1 if (email_forms and email_inputs) else 0
        score += 2 if results["Email Capture"] else 0

        # Value offers
        offers_keywords = ['free ebook', 'download', 'checklist', 'template', 'trial', 'demo']
        offers_found = [k for k in offers_keywords if k in text]
        results["Value Offers"] = 1 if offers_found else 0
        score += 2 if results["Value Offers"] else 0

        # CTAs
        cta_keywords = ['sign up', 'subscribe', 'get started', 'join now', 'access now']
        ctas_found = [k for k in cta_keywords if k in text]
        results["CTAs"] = 1 if ctas_found else 0
        score += 2 if results["CTAs"] else 0

        # Popups/Modals
        popup_indicators = ['popup', 'modal', 'lightbox']
        results["Popups"] = 1 if any(p in text for p in popup_indicators) else 0
        score += 1 if results["Popups"] else 0

        # Persuasive Copy
        persuasive_phrases = ['limited time', 'exclusive', 'proven', 'guarantee']
        persuasive_found = [p for p in persuasive_phrases if p in text]
        results["Persuasive Copy"] = 1 if persuasive_found else 0
        score += 1 if results["Persuasive Copy"] else 0

        # Trust Signals
        trust_keywords = ['testimonial', 'as seen on', 'featured in', '1000+ customers']
        results["Trust Signals"] = 1 if any(k in text for k in trust_keywords) else 0
        score += 1 if results["Trust Signals"] else 0

    except:
        results = {key: 0 for key in ["Email Capture", "Value Offers", "CTAs", "Popups", "Persuasive Copy", "Trust Signals"]}

    return score, results

def analyze_full_site(url):
    links = extract_links_with_playwright(url, max_pages=10)
    print(f"✅ Crawled {len(links)} pages.\n")

    combined_scores = {key: 0 for key in ["Email Capture", "Value Offers", "CTAs", "Popups", "Persuasive Copy", "Trust Signals"]}
    total_score = 0

    for link in links:
        score, details = analyze_page_with_playwright(link)
        total_score += score
        for key in combined_scores:
            combined_scores[key] += details.get(key, 0)
        print(f"✓ Analyzed: {link} (Score: {score})")
        time.sleep(1)

    num_pages = len(links)
    if num_pages == 0:
        return 0, {}, 0

    normalized = {k: round((v / num_pages) * 100, 2) for k, v in combined_scores.items()}
    return total_score, normalized, num_pages

def plot_results(
    scores: dict,
    total: int,
    link_count: int,
    url: str,
    *,
    output_file: Optional[str] = None,
    show: bool = True,
) -> None:
    """Generate and optionally save a bar chart of the analysis results."""

    if not scores:
        print("❌ No pages successfully analyzed.")
        return

    plt.figure(figsize=(10, 6))
    plt.barh(list(scores.keys()), list(scores.values()), color="mediumseagreen")
    plt.xlabel("Presence across pages (%)")
    plt.title(
        f"Lead Magnet Score: {total} | Pages Scanned: {link_count}\nAnalyzed URL: {url}"
    )
    plt.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    if output_file:
        plt.savefig(output_file)
    if show:
        plt.show()
    plt.close()

if __name__ == "__main__":
    # Example usage when running this module directly
    target_site = "https://www.technioz.com/"
    final_score, score_breakdown, pages_scanned = analyze_full_site(target_site)
    plot_results(score_breakdown, final_score, pages_scanned, target_site)
    print(f"Final Score: {final_score}")
    print(f"Score Breakdown: {score_breakdown}")
    print(f"Analyzed URL: {target_site}")
