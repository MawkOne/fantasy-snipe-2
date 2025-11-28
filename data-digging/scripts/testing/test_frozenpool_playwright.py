#!/usr/bin/env python3

import asyncio
from playwright.async_api import async_playwright
import json

async def test_frozenpool_playwright():
    """Test FrozenPool scraping with Playwright to handle dynamic content"""
    
    url = "https://frozenpool.dobbersports.com/frozenpool_depthchart.php?team=EDM"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Testing FrozenPool with Playwright: {url}")
            
            # Navigate to the page
            await page.goto(url, wait_until="networkidle")
            
            # Wait a bit for dynamic content to load
            await page.wait_for_timeout(3000)
            
            # Get page content
            content = await page.content()
            
            # Look for depth chart elements
            depth_chart_selectors = [
                'div[class*="depth"]',
                'table[class*="depth"]',
                'div[class*="lineup"]',
                'table[class*="lineup"]',
                'div[class*="roster"]',
                'table[class*="roster"]'
            ]
            
            found_content = False
            for selector in depth_chart_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    for i, element in enumerate(elements[:2]):  # Show first 2
                        text = await element.text_content()
                        print(f"  Element {i+1}: {text[:200]}...")
                    found_content = True
            
            # Look for any tables
            tables = await page.query_selector_all('table')
            print(f"Found {len(tables)} tables total")
            
            # Look for player links
            player_links = await page.query_selector_all('a[href*="player"]')
            print(f"Found {len(player_links)} player links")
            
            if player_links:
                print("Sample player links:")
                for i, link in enumerate(player_links[:5]):
                    text = await link.text_content()
                    href = await link.get_attribute('href')
                    print(f"  - {text.strip()}: {href}")
            
            # Look for any text containing player names
            body_text = await page.text_content('body')
            if 'McDavid' in body_text or 'Draisaitl' in body_text:
                print("Found Oilers players in page content!")
                # Extract lines containing player names
                lines = body_text.split('\n')
                player_lines = [line.strip() for line in lines if 'McDavid' in line or 'Draisaitl' in line or 'Hyman' in line]
                for line in player_lines[:5]:
                    print(f"  - {line}")
            
            # Check if there's any JavaScript that loads the content
            scripts = await page.query_selector_all('script')
            print(f"Found {len(scripts)} script tags")
            
            # Look for any data attributes or JSON
            data_elements = await page.query_selector_all('[data-*]')
            print(f"Found {len(data_elements)} elements with data attributes")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(test_frozenpool_playwright())
    print(f"\nFrozenPool Playwright test {'SUCCESSFUL' if success else 'FAILED'}")
