# diagnose.py
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def test_problematic_url():
    url = "http://www.vermelhodepaixao.com.br/search?updated-max=2017-05-26T10:55:00-03:00&max-results=56&start=8952&by-date=false"
    
    print(f"Testing URL: {url}")
    print("=" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for posts
        posts = soup.find_all('div', class_='post hentry uncustomized-post-template')
        print(f"Posts found: {len(posts)}")
        
        # Check for older posts link
        older_link = soup.find('a', class_='blog-pager-older-link')
        if not older_link:
            older_link = soup.find('a', id='Blog1_blog-pager-older-link')
        
        if older_link:
            print(f"Older Posts link found: {older_link.get('href')}")
        else:
            print("No Older Posts link found")
        
        # Check if page looks like a captcha or blocked page
        if "captcha" in response.text.lower() or "blocked" in response.text.lower():
            print("WARNING: Page might be blocking with captcha")
        
        # Show sample of page title
        title = soup.find('title')
        if title:
            print(f"Page title: {title.get_text()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_problematic_url()