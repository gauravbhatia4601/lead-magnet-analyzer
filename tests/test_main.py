"""
Tests for the Lead Magnet Analyzer main module.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import analyze_page_with_playwright, plot_results


class TestAnalyzePageWithPlaywright:
    """Test cases for the analyze_page_with_playwright function."""

    @patch('main.sync_playwright')
    def test_analyze_page_with_email_capture(self, mock_playwright):
        """Test analysis of a page with email capture elements."""
        # Mock the Playwright context
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        # Mock the page content with email form
        mock_page.content.return_value = '''
        <html>
            <body>
                <form>
                    <input type="email" name="email" />
                    <button type="submit">Subscribe</button>
                </form>
            </body>
        </html>
        '''
        
        mock_browser.new_page.return_value = mock_page
        mock_context.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_context
        
        score, results = analyze_page_with_playwright("https://example.com")
        
        assert score > 0
        assert results["Email Capture"] == 1
        assert "Email Capture" in results

    @patch('main.sync_playwright')
    def test_analyze_page_with_value_offers(self, mock_playwright):
        """Test analysis of a page with value offers."""
        # Mock the Playwright context
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        # Mock the page content with value offers
        mock_page.content.return_value = '''
        <html>
            <body>
                <h1>Free Ebook Download</h1>
                <p>Get your free checklist now!</p>
                <a href="/download">Download Template</a>
            </body>
        </html>
        '''
        
        mock_browser.new_page.return_value = mock_page
        mock_context.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_context
        
        score, results = analyze_page_with_playwright("https://example.com")
        
        assert score > 0
        assert results["Value Offers"] == 1
        assert "Value Offers" in results

    @patch('main.sync_playwright')
    def test_analyze_page_with_ctas(self, mock_playwright):
        """Test analysis of a page with call-to-action elements."""
        # Mock the Playwright context
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        # Mock the page content with CTAs
        mock_page.content.return_value = '''
        <html>
            <body>
                <h1>Join Now</h1>
                <p>Sign up for our newsletter</p>
                <button>Get Started</button>
                <a href="/subscribe">Subscribe Now</a>
            </body>
        </html>
        '''
        
        mock_browser.new_page.return_value = mock_page
        mock_context.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_context
        
        score, results = analyze_page_with_playwright("https://example.com")
        
        assert score > 0
        assert results["CTAs"] == 1
        assert "CTAs" in results

    @patch('main.sync_playwright')
    def test_analyze_page_with_trust_signals(self, mock_playwright):
        """Test analysis of a page with trust signals."""
        # Mock the Playwright context
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        # Mock the page content with trust signals
        mock_page.content.return_value = '''
        <html>
            <body>
                <h1>Our Product</h1>
                <p>As seen on TV</p>
                <div class="testimonial">Great product!</div>
                <p>Join 1000+ customers</p>
            </body>
        </html>
        '''
        
        mock_browser.new_page.return_value = mock_page
        mock_context.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_context
        
        score, results = analyze_page_with_playwright("https://example.com")
        
        assert score > 0
        assert results["Trust Signals"] == 1
        assert "Trust Signals" in results

    @patch('main.sync_playwright')
    def test_analyze_page_error_handling(self, mock_playwright):
        """Test error handling when page analysis fails."""
        # Mock Playwright to raise an exception
        mock_playwright.side_effect = Exception("Connection failed")
        
        score, results = analyze_page_with_playwright("https://example.com")
        
        # Should return zero scores when analysis fails
        assert score == 0
        assert all(value == 0 for value in results.values())


class TestPlotResults:
    """Test cases for the plot_results function."""

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.figure')
    def test_plot_results_with_valid_data(self, mock_figure, mock_show):
        """Test plotting results with valid data."""
        scores = {
            "Email Capture": 50.0,
            "Value Offers": 75.0,
            "CTAs": 25.0
        }
        
        # This should not raise any exceptions
        plot_results(scores, 150, 4, "https://example.com")
        
        # Verify that matplotlib functions were called
        mock_figure.assert_called_once()
        mock_show.assert_called_once()

    def test_plot_results_with_empty_data(self):
        """Test plotting results with empty data."""
        scores = {}
        
        # Should handle empty data gracefully
        plot_results(scores, 0, 0, "https://example.com")
        # No assertion needed - just checking it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__]) 