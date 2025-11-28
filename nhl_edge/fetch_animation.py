import requests
import json
import sys
import os

def fetch_animation(url, output_file=None):
    """
    Fetches the protected animation JSON from wsr.nhle.com using browser headers.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nhl.com/"
    }
    
    print(f"Fetching: {url}")
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if not output_file:
            # Auto-name: ev{EventID}.json
            parts = url.split('/')
            output_file = parts[-1]
            
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Success! Saved {len(data)} frames to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_animation.py <ANIMATION_URL> [OUTPUT_FILENAME]")
    else:
        url = sys.argv[1]
        outfile = sys.argv[2] if len(sys.argv) > 2 else None
        fetch_animation(url, outfile)

