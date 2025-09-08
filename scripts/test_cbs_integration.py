#!/usr/bin/env python3
"""
Test script for CBS Sports Fantasy Hockey Integration
This demonstrates how to use the authenticated CBS Sports integration.
"""

import os
import sys
import subprocess

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🏒 CBS Sports Fantasy Hockey Integration Test")
    print("=" * 50)
    
    # Your league details
    league_id = "uhhp"
    sport = "hockey"
    
    print(f"Testing with league: {league_id}")
    print(f"Sport: {sport}")
    print(f"URL: http://{league_id}.{sport}.cbssports.com")
    
    print("\n🔍 Testing Options:")
    print("1. Test without authentication (public data only)")
    print("2. Test with authentication (requires credentials)")
    print("3. Test with visible browser (for debugging)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Test without authentication
        print("\n🚀 Testing without authentication...")
        cmd = [
            sys.executable, "scripts/cbs_sports_authenticated.py",
            "--league-id", league_id,
            "--sport", sport,
            "--teams-only"
        ]
        
    elif choice == "2":
        # Test with authentication
        print("\n🔐 Testing with authentication...")
        username = input("Enter your CBS Sports email: ").strip()
        password = input("Enter your CBS Sports password: ").strip()
        
        cmd = [
            sys.executable, "scripts/cbs_sports_authenticated.py",
            "--league-id", league_id,
            "--sport", sport,
            "--username", username,
            "--password", password,
            "--teams-only"
        ]
        
    elif choice == "3":
        # Test with visible browser
        print("\n👁️ Testing with visible browser...")
        username = input("Enter your CBS Sports email: ").strip()
        password = input("Enter your CBS Sports password: ").strip()
        
        cmd = [
            sys.executable, "scripts/cbs_sports_authenticated.py",
            "--league-id", league_id,
            "--sport", sport,
            "--username", username,
            "--password", password,
            "--no-headless",
            "--teams-only"
        ]
        
    else:
        print("Invalid choice. Exiting.")
        return
    
    try:
        print(f"\nRunning command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✅ Test completed successfully!")
            print("\nOutput:")
            print(result.stdout)
        else:
            print("❌ Test failed!")
            print("\nError:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running test: {e}")

if __name__ == "__main__":
    main() 