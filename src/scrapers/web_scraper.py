import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from requests.exceptions import RequestException
import random
from fake_useragent import UserAgent
from typing import Tuple, Optional, Set, Dict, List
import time
from extruct.w3cmicrodata import MicrodataExtractor
from extruct.jsonld import JsonLdExtractor
import json

def get_random_user_agent():
    """Return a random user agent using fake-useragent library"""
    try:
        ua = UserAgent()
        return ua.random
    except:
        # Fallback to our list if fake-useragent fails
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        ]
        return random.choice(user_agents)

def make_request(url: str, timeout: int = 10) -> Tuple[requests.Response, Optional[str]]:
    """Make a request with proper headers and error handling"""
    session = requests.Session()
    
    # Enhanced headers
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    # Add random referers
    referers = [
        'https://www.google.com/',
        'https://www.bing.com/',
        'https://www.yahoo.com/',
        'https://duckduckgo.com/'
    ]
    headers['Referer'] = random.choice(referers)
    
    try:
        # Respect robots.txt
        session.headers.update(headers)
        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Get last modified date if available
        last_modified = response.headers.get('last-modified')
        
        return response, last_modified
    except requests.exceptions.HTTPError as e:
        raise RequestException(f"HTTP Error: {e.response.status_code}")
    except requests.exceptions.ConnectionError:
        raise RequestException("Connection Error")
    except requests.exceptions.Timeout:
        raise RequestException("Timeout Error")
    except requests.exceptions.RequestException as e:
        raise RequestException(f"Request Error: {str(e)}")

def extract_emails_from_text(text: str) -> set:
    """Extract email addresses from text using regex patterns"""
    email_pattern = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    return set(re.findall(email_pattern, text))

def extract_emails_from_links(soup: BeautifulSoup) -> set:
    """Extract email addresses from mailto: links"""
    emails = set()
    for link in soup.select('a[href^="mailto:"]'):
        href = link.get('href')
        if href:
            email = href.replace('mailto:', '').split('?')[0].strip()
            emails.add(email)
    return emails

def clean_and_validate_email(email: str) -> Optional[str]:
    """Clean and validate an email address, removing common false positives"""
    # Remove common prefixes that might get caught
    prefixes_to_remove = [
        r'\d{1,2}:\d{2}(?:am|pm|AM|PM)?',  # Remove time patterns like "12:30pm"
        r'\d{1,4}',  # Remove numbers
        r'[A-Za-z]+(?=info@|hello@|contact@|support@)',  # Remove words directly before common email starts
        r'York',  # Remove specific problematic words
        r'[^\w\s@\.]',  # Remove special characters except @ and .
    ]
    
    cleaned_email = email.strip()
    for prefix in prefixes_to_remove:
        cleaned_email = re.sub(prefix, '', cleaned_email)
    
    # Remove any remaining whitespace
    cleaned_email = re.sub(r'\s+', '', cleaned_email)
    
    # Basic validation
    if re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', cleaned_email):
        return cleaned_email
    return None

def extract_social_media(soup: BeautifulSoup, base_url: str) -> dict:
    """Extract social media links from the page"""
    social_media = {
        'facebook': None,
        'twitter': None,
        'instagram': None,
        'linkedin': None
    }
    
    social_patterns = {
        'facebook': r'facebook\.com|fb\.com',
        'twitter': r'twitter\.com|x\.com',
        'instagram': r'instagram\.com',
        'linkedin': r'linkedin\.com'
    }
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href:
            continue
        
        # Make relative URLs absolute
        if not href.startswith(('http://', 'https://')):
            href = urljoin(base_url, href)
            
        for platform, pattern in social_patterns.items():
            if re.search(pattern, href, re.I):
                social_media[platform] = href
                
    return social_media

def extract_contact_info(soup: BeautifulSoup) -> dict:
    """Extract additional contact information"""
    contact_info = {
        'phone_numbers': [],
        'addresses': [],
        'business_hours': None
    }
    
    # Phone number patterns
    phone_patterns = [
        r'\b(?:\+?1[-.]?)?\s*(?:\([0-9]{3}\)|[0-9]{3})[-.]?\s*[0-9]{3}[-.]?\s*[0-9]{4}\b',
        r'\b[0-9]{3}[-.]?[0-9]{3}[-.]?[0-9]{4}\b'
    ]
    
    # Extract text content
    text = soup.get_text()
    
    # Find phone numbers
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        contact_info['phone_numbers'].extend(phones)
    
    # Look for business hours
    hours_keywords = ['hours', 'business hours', 'opening hours', 'open']
    for keyword in hours_keywords:
        hours_section = soup.find(lambda tag: tag.name and keyword.lower() in tag.get_text().lower())
        if hours_section:
            contact_info['business_hours'] = hours_section.get_text().strip()
            break
    
    return contact_info

def extract_meta_info(soup: BeautifulSoup) -> dict:
    """Extract meta information from the page"""
    meta_info = {
        'title': None,
        'description': None,
        'keywords': None
    }
    
    # Get title
    title_tag = soup.find('title')
    if title_tag:
        meta_info['title'] = title_tag.string
    
    # Get meta description and keywords
    for meta in soup.find_all('meta'):
        if meta.get('name', '').lower() == 'description':
            meta_info['description'] = meta.get('content')
        elif meta.get('name', '').lower() == 'keywords':
            meta_info['keywords'] = meta.get('content')
    
    return meta_info

def get_internal_links(soup: BeautifulSoup, base_url: str) -> Set[str]:
    """Extract all internal links from a page"""
    internal_links = set()
    base_domain = urlparse(base_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href:
            continue
            
        # Make relative URLs absolute
        if not href.startswith(('http://', 'https://')):
            href = urljoin(base_url, href)
            
        # Check if it's an internal link
        if urlparse(href).netloc == base_domain:
            internal_links.add(href)
            
    return internal_links

def extract_structured_data(soup: BeautifulSoup, url: str) -> Dict:
    """Extract structured data (schema.org, JSON-LD, Microdata)"""
    mde = MicrodataExtractor()
    jlde = JsonLdExtractor()
    
    data = {
        'products': [],
        'services': [],
        'organization': None
    }
    
    # Extract Microdata
    microdata = mde.extract(soup.prettify(), url)
    if microdata:
        for item in microdata:
            if item.get('type') == 'http://schema.org/Product':
                data['products'].append(item)
            elif item.get('type') == 'http://schema.org/Service':
                data['services'].append(item)
            elif item.get('type') == 'http://schema.org/Organization':
                data['organization'] = item
    
    # Extract JSON-LD
    jsonld = jlde.extract(soup.prettify())
    if jsonld:
        for item in jsonld:
            if isinstance(item, dict):
                if item.get('@type') == 'Product':
                    data['products'].append(item)
                elif item.get('@type') == 'Service':
                    data['services'].append(item)
                elif item.get('@type') == 'Organization':
                    data['organization'] = item
    
    return data

def crawl_website(url: str, max_pages: int = 10) -> Dict:
    """Crawl a website and extract information from all pages"""
    visited_urls = set()
    to_visit = {url}
    all_data = {
        'emails': set(),
        'products': [],
        'services': [],
        'social_media': {},
        'contact_info': {},
        'meta_info': {},
        'pages_checked': []
    }
    
    while to_visit and len(visited_urls) < max_pages:
        current_url = to_visit.pop()
        if current_url in visited_urls:
            continue
            
        try:
            response, _ = make_request(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract information from current page
            page_data = {
                'url': current_url,
                'emails': extract_emails_from_text(response.text) | extract_emails_from_links(soup),
                'structured_data': extract_structured_data(soup, current_url),
                'social_media': extract_social_media(soup, current_url),
                'contact_info': extract_contact_info(soup),
                'meta_info': extract_meta_info(soup)
            }
            
            # Update all_data with page information
            all_data['emails'].update(page_data['emails'])
            all_data['products'].extend(page_data['structured_data']['products'])
            all_data['services'].extend(page_data['structured_data']['services'])
            all_data['social_media'].update(page_data['social_media'])
            all_data['contact_info'].update(page_data['contact_info'])
            all_data['meta_info'].update(page_data['meta_info'])
            all_data['pages_checked'].append(current_url)
            
            # Get new links to visit
            new_links = get_internal_links(soup, current_url)
            to_visit.update(new_links - visited_urls)
            
            visited_urls.add(current_url)
            
            # Be nice to the server
            time.sleep(1)
            
        except RequestException as e:
            print(f"Error crawling {current_url}: {str(e)}")
            continue
    
    # Convert sets to lists for JSON serialization
    all_data['emails'] = list(all_data['emails'])
    
    return all_data 