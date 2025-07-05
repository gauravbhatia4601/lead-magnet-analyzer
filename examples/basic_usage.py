#!/usr/bin/env python3
"""
Basic usage example for Lead Magnet Analyzer

This example demonstrates how to use the Lead Magnet Analyzer
to evaluate a website's lead magnet effectiveness.
"""

import sys
import os

# Add the parent directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import analyze_full_site, plot_results

def main():
    """
    Example usage of the Lead Magnet Analyzer
    """
    print("🔍 Lead Magnet Analyzer - Basic Usage Example")
    print("=" * 50)
    
    # Example websites to analyze
    test_sites = [
        "https://www.example.com",
        "https://www.marketingexample.com",
        "https://www.leadmagnetdemo.com"
    ]
    
    for site in test_sites:
        print(f"\n📊 Analyzing: {site}")
        print("-" * 30)
        
        try:
            # Analyze the website
            final_score, score_breakdown, pages_scanned = analyze_full_site(site)
            
            # Display results
            print(f"✅ Analysis complete!")
            print(f"📈 Final Score: {final_score}")
            print(f"📄 Pages Scanned: {pages_scanned}")
            print(f"📊 Score Breakdown:")
            
            for element, percentage in score_breakdown.items():
                print(f"   • {element}: {percentage}%")
            
            # Generate visual chart
            plot_results(score_breakdown, final_score, pages_scanned, site)
            
        except Exception as e:
            print(f"❌ Error analyzing {site}: {str(e)}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 