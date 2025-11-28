#!/usr/bin/env python3
"""
CBS Sports Integration Setup
This script helps you set up CBS Sports integration with secure credentials.
"""

import os
import sys
import subprocess

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🏒 CBS Sports Integration Setup")
    print("=" * 40)
    
    # Your league details
    league_id = "uhhp"
    sport = "hockey"
    
    print(f"League ID: {league_id}")
    print(f"Sport: {sport}")
    print(f"URL: http://{league_id}.{sport}.cbssports.com")
    
    print("\n🔧 Setup Options:")
    print("1. Save CBS Sports credentials securely")
    print("2. Test integration with saved credentials")
    print("3. Test integration with manual login")
    print("4. View saved credentials")
    print("5. Clear saved credentials")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        print("\n🔐 Setting up secure credentials...")
        cmd = [sys.executable, "scripts/cbs_credentials.py"]
        subprocess.run(cmd)
    
    elif choice == "2":
        print("\n🧪 Testing with saved credentials...")
        cmd = [
            sys.executable, "scripts/cbs_sports_authenticated.py",
            "--league-id", league_id,
            "--sport", sport,
            "--use-saved-creds",
            "--teams-only"
        ]
        subprocess.run(cmd)
    
    elif choice == "3":
        print("\n🧪 Testing with manual login...")
        cmd = [
            sys.executable, "scripts/cbs_sports_authenticated.py",
            "--league-id", league_id,
            "--sport", sport,
            "--teams-only"
        ]
        subprocess.run(cmd)
    
    elif choice == "4":
        print("\n📋 Viewing saved credentials...")
        try:
            from cbs_credentials import CBSCredentials
            creds = CBSCredentials()
            username, password = creds.load_credentials()
            if username and password:
                print(f"✅ Saved credentials found for: {username}")
                print(f"Password: {'*' * len(password)}")
            else:
                print("❌ No saved credentials found")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif choice == "5":
        print("\n🗑️ Clearing saved credentials...")
        try:
            from cbs_credentials import CBSCredentials
            creds = CBSCredentials()
            creds.clear_credentials()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif choice == "6":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 