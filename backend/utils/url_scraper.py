"""
URL Scraper - Extract content from web pages using BeautifulSoup
Add this as: backend/utils/url_scraper.py
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def is_valid_url(url):
    """Check if string is a valid URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def scrape_url(url, timeout=10):
    """
    Scrape content from URL using BeautifulSoup
    
    Args:
        url: Web page URL
        timeout: Request timeout in seconds
    
    Returns:
        dict: {
            "url": url,
            "title": page_title,
            "content": extracted_text,
            "status": "success" or "error",
            "error": error_message (if any)
        }
    """
    print(f"[URL Scraper] Fetching: {url}")
    
    try:
        # Send request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = '\n'.join(lines)
        
        print(f"[URL Scraper] ✓ Scraped {len(content)} characters from {url}")
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "status": "success",
            "length": len(content)
        }
        
    except requests.exceptions.Timeout:
        error = f"Timeout: Could not fetch URL within {timeout} seconds"
        print(f"[URL Scraper] ✗ {error}")
        return {
            "url": url,
            "status": "error",
            "error": error
        }
    except requests.exceptions.RequestException as e:
        error = f"Request failed: {str(e)}"
        print(f"[URL Scraper] ✗ {error}")
        return {
            "url": url,
            "status": "error",
            "error": error
        }
    except Exception as e:
        error = f"Scraping failed: {str(e)}"
        print(f"[URL Scraper] ✗ {error}")
        return {
            "url": url,
            "status": "error",
            "error": error
        }


def scrape_multiple_urls(urls, timeout=10):
    """
    Scrape multiple URLs
    
    Args:
        urls: List of URLs
        timeout: Request timeout per URL
    
    Returns:
        list: List of scraping results
    """
    results = []
    
    for url in urls:
        if is_valid_url(url):
            result = scrape_url(url, timeout)
            results.append(result)
        else:
            print(f"[URL Scraper] ✗ Invalid URL: {url}")
            results.append({
                "url": url,
                "status": "error",
                "error": "Invalid URL format"
            })
    
    return results