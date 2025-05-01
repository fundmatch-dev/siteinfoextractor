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
from datetime import datetime

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

def extract_business_profile(soup: BeautifulSoup, url: str) -> dict:
    """Extract business profile information from HTML"""
    profile = {
        'primary_category': None,
        'industry': None,
        'business_size': None,
        'years_in_business': None,
        'main_offerings': [],
        'price_range': None,
        'target_segments': [],
        'sales_model': None,
        'distribution_channels': [],
        'service_delivery': [],
        'locations': [],
        'service_areas': []
    }
    
    # 1. Extract from structured data (most reliable)
    structured_data = extract_structured_data(soup, url)
    if structured_data.get('organization'):
        org_data = structured_data['organization']
        if isinstance(org_data, dict):
            profile['primary_category'] = org_data.get('@type', '').replace('http://schema.org/', '')
            profile['industry'] = org_data.get('industry')
            profile['locations'] = [org_data.get('address', {}).get('streetAddress', '')]
            if org_data.get('foundingDate'):
                try:
                    founding_year = int(org_data['foundingDate'][:4])
                    current_year = datetime.now().year
                    profile['years_in_business'] = current_year - founding_year
                except:
                    pass
    
    # 2. Extract from common HTML patterns
    # Look for about us section
    about_sections = soup.find_all(['section', 'div'], class_=lambda x: x and any(
        term in x.lower() for term in ['about', 'company', 'business', 'story']
    ))
    
    for section in about_sections:
        text = section.get_text().lower()
        # Look for business size indicators
        if any(term in text for term in ['small business', 'local business']):
            profile['business_size'] = 'small'
        elif any(term in text for term in ['medium', 'mid-sized']):
            profile['business_size'] = 'medium'
        elif any(term in text for term in ['large', 'enterprise', 'corporation']):
            profile['business_size'] = 'large'
        
        # Look for years in business
        year_pattern = r'(\d+)\s+(?:year|yr)s?\s+(?:in business|of experience)'
        match = re.search(year_pattern, text)
        if match:
            profile['years_in_business'] = int(match.group(1))
    
    # 3. Extract from navigation and footer
    nav_links = soup.find_all(['nav', 'footer'])
    for nav in nav_links:
        for link in nav.find_all('a'):
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            # Look for service areas
            if any(term in href for term in ['locations', 'areas', 'regions']):
                profile['service_areas'].append(text)
            
            # Look for distribution channels
            if any(term in href for term in ['online', 'store', 'shop']):
                if 'online' in href:
                    profile['distribution_channels'].append('online')
                if 'store' in href or 'shop' in href:
                    profile['distribution_channels'].append('physical')
    
    # 4. Extract from product/service pages
    product_pages = soup.find_all(['section', 'div'], class_=lambda x: x and any(
        term in x.lower() for term in ['product', 'service', 'offering']
    ))
    
    for page in product_pages:
        # Look for price range indicators
        text = page.get_text().lower()
        if any(term in text for term in ['premium', 'luxury', 'high-end']):
            profile['price_range'] = 'premium'
        elif any(term in text for term in ['budget', 'affordable', 'cheap']):
            profile['price_range'] = 'budget'
        elif any(term in text for term in ['mid-range', 'standard']):
            profile['price_range'] = 'mid-range'
        
        # Look for sales model indicators
        if any(term in text for term in ['subscription', 'membership']):
            profile['sales_model'] = 'subscription'
        elif any(term in text for term in ['marketplace', 'platform']):
            profile['sales_model'] = 'marketplace'
        elif any(term in text for term in ['direct', 'buy now']):
            profile['sales_model'] = 'direct'
    
    # 5. Extract from contact/service pages
    contact_pages = soup.find_all(['section', 'div'], class_=lambda x: x and any(
        term in x.lower() for term in ['contact', 'service', 'delivery']
    ))
    
    for page in contact_pages:
        text = page.get_text().lower()
        # Look for service delivery methods
        if any(term in text for term in ['in-person', 'onsite', 'at your location']):
            profile['service_delivery'].append('in-person')
        if any(term in text for term in ['remote', 'online', 'virtual']):
            profile['service_delivery'].append('remote')
    
    # Clean up and deduplicate lists
    profile['distribution_channels'] = list(set(profile['distribution_channels']))
    profile['service_delivery'] = list(set(profile['service_delivery']))
    profile['service_areas'] = list(set(profile['service_areas']))
    
    return profile

def extract_products_services(soup: BeautifulSoup, url: str) -> List[dict]:
    """Extract simple product and service information from HTML"""
    products_services = []
    
    # 1. Extract from structured data first
    structured_data = extract_structured_data(soup, url)
    for item in structured_data.get('products', []) + structured_data.get('services', []):
        if isinstance(item, dict):
            product_service = {
                'name': item.get('name', ''),
                'type': 'product' if 'Product' in str(item.get('@type', '')) else 'service',
                'category': item.get('category'),
                'price_range': None,
                'description': item.get('description')
            }
            products_services.append(product_service)
    
    # 2. Extract from common product/service sections
    product_sections = soup.find_all(['section', 'div'], class_=lambda x: x and any(
        term in x.lower() for term in ['product', 'service', 'offering', 'item', 'package']
    ))
    
    for section in product_sections:
        # Try to find name
        name_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not name_elem:
            continue
            
        name = name_elem.get_text().strip()
        if not name:
            continue
            
        # Determine if it's a product or service
        section_type = 'service' if any(term in section.get('class', []) for term in ['service', 'offering']) else 'product'
        
        # Try to find description
        description = None
        desc_elem = section.find(['p', 'div'], class_=lambda x: x and any(
            term in x.lower() for term in ['description', 'desc', 'details']
        ))
        if desc_elem:
            description = desc_elem.get_text().strip()
        
        # Try to find category
        category = None
        category_elem = section.find(['span', 'div'], class_=lambda x: x and any(
            term in x.lower() for term in ['category', 'type', 'class']
        ))
        if category_elem:
            category = category_elem.get_text().strip()
        
        # Try to determine price range
        price_range = None
        price_text = section.get_text().lower()
        if any(term in price_text for term in ['premium', 'luxury', 'high-end']):
            price_range = 'premium'
        elif any(term in price_text for term in ['budget', 'affordable', 'cheap']):
            price_range = 'budget'
        elif any(term in price_text for term in ['mid-range', 'standard']):
            price_range = 'mid-range'
        
        product_service = {
            'name': name,
            'type': section_type,
            'category': category,
            'price_range': price_range,
            'description': description
        }
        
        # Only add if we have at least a name
        if product_service['name']:
            products_services.append(product_service)
    
    return products_services

def crawl_website(url: str, max_pages: int = 10) -> Dict:
    """Crawl a website and extract information from all pages"""
    visited_urls = set()
    to_visit = {url}
    all_data = {
        'emails': set(),
        'products_services': [],
        'social_media': {},
        'contact_info': {},
        'meta_info': {},
        'business_profile': {},
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
                'products_services': extract_products_services(soup, current_url),
                'social_media': extract_social_media(soup, current_url),
                'contact_info': extract_contact_info(soup),
                'meta_info': extract_meta_info(soup),
                'business_profile': extract_business_profile(soup, current_url)
            }
            
            # Update all_data with page information
            all_data['emails'].update(page_data['emails'])
            all_data['products_services'].extend(page_data['products_services'])
            all_data['social_media'].update(page_data['social_media'])
            all_data['contact_info'].update(page_data['contact_info'])
            all_data['meta_info'].update(page_data['meta_info'])
            all_data['business_profile'].update(page_data['business_profile'])
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