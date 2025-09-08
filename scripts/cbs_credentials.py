#!/usr/bin/env python3
"""
CBS Sports Credentials Management
Secure handling of CBS Sports login credentials.
"""

import os
import sys
import json
import getpass
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CBSCredentials:
    """Secure CBS Sports credentials management"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".nhl_api"
        self.credentials_file = self.config_dir / "cbs_credentials.json"
        self.credentials = {}
    
    def setup_config_directory(self):
        """Create configuration directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        # Set restrictive permissions
        self.config_dir.chmod(0o700)
    
    def save_credentials(self, username: str, password: str):
        """Save credentials securely"""
        self.setup_config_directory()
        
        self.credentials = {
            "username": username,
            "password": password,
            "saved_at": str(Path().cwd())
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(self.credentials, f, indent=2)
        
        # Set restrictive file permissions
        self.credentials_file.chmod(0o600)
        
        print(f"✅ Credentials saved to: {self.credentials_file}")
        print("🔒 File permissions set to owner-only access")
    
    def load_credentials(self) -> tuple:
        """Load saved credentials"""
        if not self.credentials_file.exists():
            return None, None
        
        try:
            with open(self.credentials_file, 'r') as f:
                self.credentials = json.load(f)
            
            return self.credentials.get("username"), self.credentials.get("password")
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None, None
    
    def clear_credentials(self):
        """Remove saved credentials"""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
            print("✅ Credentials cleared")
        else:
            print("ℹ️ No saved credentials found")
    
    def get_credentials_interactive(self) -> tuple:
        """Get credentials interactively"""
        print("🔐 CBS Sports Credentials")
        print("=" * 30)
        
        # Check for saved credentials first
        saved_username, saved_password = self.load_credentials()
        if saved_username and saved_password:
            use_saved = input(f"Found saved credentials for: {saved_username}\nUse saved credentials? (y/n): ").strip().lower()
            if use_saved == 'y':
                return saved_username, saved_password
        
        # Get new credentials
        username = input("Enter CBS Sports email: ").strip()
        password = getpass.getpass("Enter CBS Sports password: ").strip()
        
        if username and password:
            save_creds = input("Save credentials for future use? (y/n): ").strip().lower()
            if save_creds == 'y':
                self.save_credentials(username, password)
        
        return username, password

def main():
    """Interactive credentials management"""
    creds = CBSCredentials()
    
    print("🔐 CBS Sports Credentials Manager")
    print("=" * 40)
    print("1. Save new credentials")
    print("2. Load saved credentials")
    print("3. Clear saved credentials")
    print("4. Test credentials")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        username = input("Enter CBS Sports email: ").strip()
        password = getpass.getpass("Enter CBS Sports password: ").strip()
        
        if username and password:
            creds.save_credentials(username, password)
        else:
            print("❌ Username and password are required")
    
    elif choice == "2":
        username, password = creds.load_credentials()
        if username and password:
            print(f"✅ Loaded credentials for: {username}")
        else:
            print("❌ No saved credentials found")
    
    elif choice == "3":
        creds.clear_credentials()
    
    elif choice == "4":
        username, password = creds.get_credentials_interactive()
        if username and password:
            print(f"✅ Credentials ready for testing")
            print(f"Username: {username}")
            print(f"Password: {'*' * len(password)}")
        else:
            print("❌ No credentials provided")
    
    elif choice == "5":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 