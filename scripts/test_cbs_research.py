#!/usr/bin/env python3
"""
Simple test script to start CBS Sports research.
This will analyze the page structure without requiring credentials.
"""

import os
import sys
import subprocess

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔍 CBS Sports Fantasy Hockey Research")
    print("=" * 50)
    
    # Test URL
    test_url = "https://uhhp.hockey.cbssports.com/home"
    
    print(f"Testing URL: {test_url}")
    print("\nThis will analyze the page structure without authentication.")
    print("The analysis will help us understand:")
    print("- Whether authentication is required")
    print("- What forms and data structures are available")
    print("- Potential selectors for data extraction")
    print("- Network endpoints that might be useful")
    
    # Check if required packages are installed
    try:
        import requests
        import bs4
        print("\n✅ Required packages are available")
    except ImportError as e:
        print(f"\n❌ Missing packages: {e}")
        print("Install with: pip install -r requirements_scraping.txt")
        return
    
    # Run the analysis
    print("\n🚀 Starting analysis...")
    
    cmd = [
        sys.executable, "scripts/research_cbs_sports.py",
        "--url", test_url,
        "--mode", "analyze",
        "--output", "cbs_analysis_results.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✅ Analysis completed successfully!")
            print(f"Results saved to: cbs_analysis_results.json")
            
            # Show summary
            if os.path.exists("cbs_analysis_results.json"):
                import json
                with open("cbs_analysis_results.json", 'r') as f:
                    data = json.load(f)
                
                print(f"\n📊 Analysis Summary:")
                print(f"Title: {data.get('title', 'N/A')}")
                print(f"Requires Auth: {data.get('requires_auth', 'Unknown')}")
                print(f"Forms Found: {len(data.get('forms', []))}")
                print(f"Links Found: {len(data.get('links', []))}")
                print(f"Scripts Found: {len(data.get('scripts', []))}")
                
                if data.get('data_attributes'):
                    print(f"Data Attributes: {list(data['data_attributes'].keys())}")
                
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running analysis: {e}")

if __name__ == "__main__":
    main() 