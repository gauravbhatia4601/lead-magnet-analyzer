# Lead Magnet Analyzer 🔍

A powerful web scraping and analysis tool that evaluates websites for lead magnet effectiveness using Playwright and BeautifulSoup.

## 🚀 Features

- Automated Web Crawling: Uses Playwright to crawl websites and extract all internal links
- Lead Magnet Analysis: Evaluates pages for key lead magnet elements:
  - Email capture forms
  - Value offers (free ebooks, downloads, checklists, etc.)
  - Call-to-action buttons
  - Popup/modals
  - Persuasive copy
  - Trust signals
- Visual Analytics: Generates beautiful charts showing lead magnet effectiveness
- Comprehensive Scoring: Provides detailed breakdown of lead magnet elements across all pages

## 📊 What It Analyzes

The tool scans websites for these critical lead magnet components:

| Element | Weight | Description |
|---------|--------|-------------|
| Email Capture | 2 points | Email signup forms and input fields |
| Value Offers | 2 points | Free downloads, ebooks, templates, trials |
| CTAs | 2 points | Sign up, subscribe, get started buttons |
| Popups | 1 point | Modal windows and popup forms |
| Persuasive Copy | 1 point | Limited time, exclusive, guarantee language |
| Trust Signals | 1 point | Testimonials, media mentions, customer counts |

## 🛠️ Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/lead-magnet-analyzer.git
   cd lead-magnet-analyzer
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers
   ```bash
   playwright install
   ```

## 🎯 Usage

### Basic Usage

```python
from main import analyze_full_site, plot_results

# Analyze a website
target_url = "https://example.com"
final_score, score_breakdown, pages_scanned = analyze_full_site(target_url)

# Display results
plot_results(score_breakdown, final_score, pages_scanned, target_url)
print(f"Final Score: {final_score}")
print(f"Score Breakdown: {score_breakdown}")
```

### Command Line Usage

```bash
python main.py
```

The script will analyze the predefined target site and display results.

## 📈 Output

The analyzer provides:

1. Crawl Results: Number of pages successfully crawled
2. Individual Page Scores: Score for each analyzed page
3. Overall Score: Total lead magnet effectiveness score
4. Visual Chart: Bar chart showing presence of each element across pages
5. Detailed Breakdown: Percentage of pages containing each lead magnet element

## 🔧 Configuration

You can modify the analysis parameters in `main.py`:

- `max_pages`: Maximum number of pages to crawl (default: 10)
- `timeout`: Page load timeout in milliseconds (default: 15000)
- Analysis keywords and scoring weights

## 📋 Requirements

- Python 3.7+
- Playwright
- BeautifulSoup4
- Matplotlib
- Requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and analysis purposes only. Always respect websites' robots.txt files and terms of service. Use responsibly and ethically.

## 🐛 Issues

If you encounter any issues or have suggestions, please [open an issue](https://github.com/yourusername/lead-magnet-analyzer/issues).

## 📞 Support

For support, email support@example.com or join our Slack channel.

Made with ❤️ for digital marketers and growth hackers