#!/usr/bin/env python3
"""
Simple test script for IMDB scraper functionality
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class SimpleIMDBTest:
    def __init__(self, profile_url: str):
        self.profile_url = profile_url
        self.base_url = "https://www.imdb.com"
        self.user_id = self._extract_user_id(profile_url)
        
    def _extract_user_id(self, url: str):
        """Extract user ID from IMDB profile URL"""
        match = re.search(r'/user/(ur\d+)', url)
        return match.group(1) if match else None
    
    async def test_url_access(self):
        """Test if we can access the ratings page"""
        if not self.user_id:
            print("Invalid IMDB profile URL")
            return False
            
        print(f"Extracted User ID: {self.user_id}")
        
        # Test different URL patterns
        test_urls = [
            f"{self.base_url}/user/{self.user_id}/ratings",
            f"{self.base_url}/user/{self.user_id}/ratings?start=1&view=detail",
            f"{self.base_url}/user/{self.user_id}/ratings/?start=1",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(test_urls, 1):
                try:
                    print(f"\nTesting URL {i}: {url}")
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Look for rating items
                            rating_items = self._find_rating_items(soup)
                            print(f"Status: {response.status} - Found {len(rating_items)} rating items")
                            
                            # Test extraction on first few items
                            if rating_items:
                                for j, item in enumerate(rating_items[:3]):
                                    title_data = self._extract_title_and_id(item)
                                    rating = self._extract_user_rating(item)
                                    if title_data and rating:
                                        print(f"   Movie {j+1}: {title_data['title']} (Rating: {rating})")
                                return True
                        else:
                            print(f"Error Status: {response.status}")
                            
                except Exception as e:
                    print(f"Error: {e}")
        
        return False
    
    def _find_rating_items(self, soup):
        """Find rating items using multiple selector strategies"""
        selectors = [
            ('div', {'class': re.compile(r'lister-item')}),
            ('li', {'class': re.compile(r'ipc-metadata-list-summary-item')}),
            ('div', {'class': re.compile(r'titlereference-')}),
        ]
        
        for tag, attrs in selectors:
            items = soup.find_all(tag, attrs)
            if items:
                return items
        
        # Fallback: any div containing movie links
        return soup.find_all('div', lambda x: x and x.find('a', href=re.compile(r'/title/tt\d+')))
    
    def _extract_title_and_id(self, item):
        """Extract movie title and IMDB ID"""
        # Look for title link
        title_link = item.find('a', href=re.compile(r'/title/tt\d+'))
        if title_link:
            href = title_link.get('href', '')
            imdb_id_match = re.search(r'/title/(tt\d+)', href)
            if imdb_id_match:
                return {
                    'title': title_link.get_text(strip=True),
                    'imdb_id': imdb_id_match.group(1)
                }
        return None
    
    def _extract_user_rating(self, item):
        """Extract user rating"""
        # Look for rating spans
        rating_selectors = [
            'span.ipl-rating-star__rating',
            'span[class*="rating"]'
        ]
        
        for selector in rating_selectors:
            rating_elem = item.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if re.match(r'^\d{1,2}$', rating_text):
                    return int(rating_text)
        
        # Fallback: look for any number 1-10
        for elem in item.find_all(['span', 'div']):
            text = elem.get_text(strip=True)
            if re.match(r'^(10|[1-9])$', text):
                return int(text)
        
        return None

async def main():
    """Test the IMDB scraper"""
    print("IMDB Ratings Scraper Test")
    print("=" * 50)
    
    # Use the URL from the .env file
    profile_url = "https://www.imdb.com/user/ur34563842/ratings/?ref_=hm_nv_rat"
    
    tester = SimpleIMDBTest(profile_url)
    success = await tester.test_url_access()
    
    if success:
        print("\nScraper test completed successfully!")
        print("The enhanced scraper should work with your IMDB profile.")
    else:
        print("\nScraper test failed.")
        print("May need to adjust selectors for current IMDB layout.")

if __name__ == "__main__":
    asyncio.run(main())