# API Documentation

## Overview

The Lead Magnet Analyzer provides a comprehensive API for analyzing websites and evaluating their lead magnet effectiveness. This document describes the main functions and their usage.

## Core Functions

### `extract_links_with_playwright(start_url, max_pages=10)`

Extracts all internal links from a website using Playwright.

Parameters:
- `start_url` (str): The starting URL to crawl
- `max_pages` (int, optional): Maximum number of pages to crawl. Default is 10.

Returns:
- `list`: List of URLs found during crawling

Example:
```python
from main import extract_links_with_playwright

links = extract_links_with_playwright("https://example.com", max_pages=5)
print(f"Found {len(links)} pages")
```

### `analyze_page_with_playwright(url)`

Analyzes a single page for lead magnet elements.

Parameters:
- `url` (str): The URL of the page to analyze

Returns:
- `tuple`: (score, results_dict)
  - `score` (int): Total lead magnet score for the page
  - `results_dict` (dict): Dictionary with analysis results for each element

Example:
```python
from main import analyze_page_with_playwright

score, results = analyze_page_with_playwright("https://example.com")
print(f"Page score: {score}")
print(f"Results: {results}")
```

### `analyze_full_site(url)`

Performs a complete analysis of a website by crawling and analyzing all pages.

Parameters:
- `url` (str): The starting URL for the website analysis

Returns:
- `tuple`: (total_score, normalized_scores, pages_scanned)
  - `total_score` (int): Total lead magnet score across all pages
  - `normalized_scores` (dict): Percentage of pages containing each element
  - `pages_scanned` (int): Number of pages successfully analyzed

Example:
```python
from main import analyze_full_site

total_score, breakdown, pages = analyze_full_site("https://example.com")
print(f"Total score: {total_score}")
print(f"Pages analyzed: {pages}")
```

### `plot_results(scores, total, link_count, url)`

Generates a visual chart of the analysis results.

Parameters:
- `scores` (dict): Dictionary of element scores
- `total` (int): Total lead magnet score
- `link_count` (int): Number of pages analyzed
- `url` (str): The analyzed URL

Returns:
- `None`: Displays a matplotlib chart

Example:
```python
from main import plot_results

plot_results(breakdown, total_score, pages_scanned, "https://example.com")
```

## Analysis Elements

The analyzer evaluates the following lead magnet elements:

| Element | Weight | Description |
|---------|--------|-------------|
| Email Capture | 2 points | Email signup forms and input fields |
| Value Offers | 2 points | Free downloads, ebooks, templates, trials |
| CTAs | 2 points | Sign up, subscribe, get started buttons |
| Popups | 1 point | Modal windows and popup forms |
| Persuasive Copy | 1 point | Limited time, exclusive, guarantee language |
| Trust Signals | 1 point | Testimonials, media mentions, customer counts |

## Error Handling

All functions include error handling and will gracefully handle:
- Network timeouts
- Invalid URLs
- Unreachable pages
- Parsing errors

## Configuration

You can modify the analysis parameters by editing the constants in `main.py`:

- `max_pages`: Maximum pages to crawl (default: 10)
- `timeout`: Page load timeout in milliseconds (default: 15000)
- Analysis keywords and scoring weights

## Performance Considerations

- The analyzer uses Playwright for robust web scraping
- Pages are analyzed sequentially to avoid overwhelming servers
- A 1-second delay is added between page analyses
- Headless browser mode is used for efficiency

## Dependencies

Required Python packages:
- `playwright`: Web automation and scraping
- `beautifulsoup4`: HTML parsing
- `matplotlib`: Chart generation
- `requests`: HTTP requests (optional, used by Playwright) 