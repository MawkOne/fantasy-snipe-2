#!/usr/bin/env python3
"""
CBS Sports Session Bridge - Transfer browser session to API client
"""

import json
import time
import logging
from pathlib import Path
from cbs_sports_api_client import CBSSportsAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def transfer_browser_session_to_api(league_id: str, sport: str = "hockey"):
    """Transfer session data from browser automation to API client"""
    
    # Path to browser session data
    home_dir = Path.home()
    browser_session_file = home_dir / ".nhl_api" / f"cbs_browser_session_{league_id}.json"
    
    if not browser_session_file.exists():
        logger.error(f"Browser session file not found: {browser_session_file}")
        return False
    
    try:
        # Load browser session data
        with open(browser_session_file, 'r') as f:
            browser_data = json.load(f)
        
        # Extract cookies and endpoints
        cookies = browser_data.get('cookies', {})
        endpoints = browser_data.get('endpoints', {})
        
        # Create API client
        api_client = CBSSportsAPIClient(league_id, sport)
        
        # Transfer session data
        api_client.update_session_from_browser(cookies, endpoints)
        
        # Test authentication
        if api_client.is_authenticated():
            logger.info("Successfully transferred browser session to API client")
            return True
        else:
            logger.warning("Session transfer completed but authentication failed")
            return False
            
    except Exception as e:
        logger.error(f"Error transferring session: {e}")
        return False

def test_api_client_without_browser(league_id: str, sport: str = "hockey"):
    """Test the API client without browser automation"""
    
    logger.info(f"Testing API client for league {league_id}")
    
    # Create API client
    client = CBSSportsAPIClient(league_id, sport)
    
    # Check authentication
    is_auth = client.is_authenticated()
    logger.info(f"Authentication status: {is_auth}")
    
    if not is_auth:
        logger.warning("Not authenticated - API client will have limited functionality")
    
    # Try to get basic data
    try:
        league_info = client.get_league_info()
        logger.info(f"League info: {league_info}")
        
        standings = client.get_standings()
        logger.info(f"Standings teams: {len(standings.get('teams', []))}")
        
        waiver_status = client.get_waiver_status()
        logger.info(f"Waiver status: {waiver_status}")
        
        transactions = client.get_recent_transactions()
        logger.info(f"Recent transactions: {len(transactions)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing API client: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CBS Sports Session Bridge')
    parser.add_argument('--league-id', required=True, help='CBS Sports League ID')
    parser.add_argument('--sport', default='hockey', help='Sport (default: hockey)')
    parser.add_argument('--transfer', action='store_true', help='Transfer browser session to API client')
    parser.add_argument('--test', action='store_true', help='Test API client without browser')
    
    args = parser.parse_args()
    
    if args.transfer:
        success = transfer_browser_session_to_api(args.league_id, args.sport)
        if success:
            print("✅ Session transfer successful")
        else:
            print("❌ Session transfer failed")
    
    if args.test:
        success = test_api_client_without_browser(args.league_id, args.sport)
        if success:
            print("✅ API client test successful")
        else:
            print("❌ API client test failed")

if __name__ == "__main__":
    main() 