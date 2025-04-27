import pandas as pd
from typing import List, Dict, Optional
import time
import random
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url

from .models.data_models import WebsiteStatus, Product, Service, BusinessAnalysis
from .utils.setup_validator import load_environment
from .scrapers.web_scraper import (
    make_request,
    extract_emails_from_text,
    extract_emails_from_links,
    clean_and_validate_email,
    extract_social_media,
    extract_contact_info,
    extract_meta_info
)
from .analyzers.ai_analyzer import (
    analyze_product_with_ai,
    analyze_service_with_ai,
    analyze_business_with_ai
)

class SiteInfoExtractor:
    def __init__(self):
        """Initialize the SiteInfoExtractor"""
        # Verify environment setup
        load_environment()
    
    def extract_structured_data(self, html: str, url: str) -> dict:
        """Extract structured data using extruct library"""
        base_url = get_base_url(html, url)
        structured_data = extruct.extract(
            html,
            base_url=base_url,
            syntaxes=['json-ld', 'microdata', 'opengraph', 'microformat'],
            uniform=True
        )
        return structured_data
    
    def extract_products_and_services(self, soup: BeautifulSoup, url: str, structured_data: dict) -> dict:
        """Extract products, services, and related information with AI enhancement"""
        products_and_services = {
            'products': [],
            'services': [],
            'categories': set(),
            'price_ranges': [],
            'featured_items': []
        }
        
        # Extract from structured data first (most reliable)
        for data_type, data in structured_data.items():
            for item in data:
                if isinstance(item, dict):
                    # Handle Product schema
                    if item.get('@type', '').lower() in ['product', 'service']:
                        product_info = {
                            'name': item.get('name'),
                            'description': item.get('description'),
                            'price': item.get('offers', {}).get('price'),
                            'category': item.get('category'),
                            'url': item.get('url'),
                            'image': item.get('image')
                        }
                        if item.get('@type').lower() == 'product':
                            products_and_services['products'].append(product_info)
                        else:
                            products_and_services['services'].append(product_info)
                    
                    # Handle category information
                    if item.get('@type', '').lower() in ['itemlist', 'breadcrumblist']:
                        for list_item in item.get('itemListElement', []):
                            if isinstance(list_item, dict):
                                category = list_item.get('name')
                                if category:
                                    products_and_services['categories'].add(category)
        
        # Enhance with AI analysis
        enhanced_products = []
        for product in products_and_services['products']:
            try:
                analyzed_product = analyze_product_with_ai(product)
                enhanced_products.append(analyzed_product.dict())
            except Exception as e:
                print(f"Error analyzing product: {str(e)}")
                enhanced_products.append(product)
        
        enhanced_services = []
        for service in products_and_services['services']:
            try:
                analyzed_service = analyze_service_with_ai(service)
                enhanced_services.append(analyzed_service.dict())
            except Exception as e:
                print(f"Error analyzing service: {str(e)}")
                enhanced_services.append(service)
        
        products_and_services['products'] = enhanced_products
        products_and_services['services'] = enhanced_services
        products_and_services['categories'] = list(products_and_services['categories'])
        
        return products_and_services
    
    def process_website(self, url: str) -> WebsiteStatus:
        """Process a single website and extract all available information"""
        website_status = WebsiteStatus()
        
        try:
            # Make request
            response, last_modified = make_request(url)
            website_status.status_code = response.status_code
            website_status.is_success = True
            website_status.pages_checked.append({"url": url, "status": response.status_code})
            website_status.last_modified = last_modified
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract structured data
            structured_data = self.extract_structured_data(response.text, url)
            
            # Extract emails
            text_emails = extract_emails_from_text(soup.get_text())
            link_emails = extract_emails_from_links(soup)
            all_emails = text_emails.union(link_emails)
            
            # Clean and validate emails
            valid_emails = set()
            for email in all_emails:
                cleaned_email = clean_and_validate_email(email)
                if cleaned_email:
                    valid_emails.add(cleaned_email)
            
            # Extract additional information
            website_status.emails_found = list(valid_emails)
            website_status.social_media = extract_social_media(soup, url)
            website_status.contact_info = extract_contact_info(soup)
            website_status.meta_info = extract_meta_info(soup)
            website_status.products_and_services = self.extract_products_and_services(soup, url, structured_data)
            
            # AI-powered business analysis
            try:
                website_status.business_analysis = analyze_business_with_ai(
                    soup.get_text(),
                    structured_data
                ).dict()
                website_status.business_type = website_status.business_analysis.get('business_type')
            except Exception as e:
                print(f"Error performing business analysis: {str(e)}")
            
            # Random delay between requests
            time.sleep(random.uniform(3, 7))
            
        except Exception as e:
            website_status.error_message = str(e)
            website_status.is_success = False
            website_status.pages_checked.append({"url": url, "status": str(e)})
        
        return website_status
    
    def process_businesses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process multiple businesses from a DataFrame"""
        results = []
        
        for _, row in df.iterrows():
            if pd.isna(row['website']) or not row['website']:
                print(f"\nSkipping {row['name']}: No website provided")
                results.append({
                    'name': row['name'],
                    'address': row['address'],
                    'phone': row['phone_number'],
                    'website': row['website'],
                    'status': 'skipped',
                    'reason': 'no_website'
                })
                continue
            
            print(f"\nProcessing: {row['name']}")
            print(f"Website: {row['website']}")
            
            website_status = self.process_website(row['website'])
            
            result = {
                'name': row['name'],
                'address': row['address'],
                'phone': row['phone_number'],
                'website': row['website'],
                'emails': website_status.emails_found,
                'status_code': website_status.status_code,
                'error_message': website_status.error_message,
                'pages_checked': website_status.pages_checked,
                'social_media': website_status.social_media,
                'contact_info': website_status.contact_info,
                'meta_info': website_status.meta_info,
                'products_and_services': website_status.products_and_services,
                'business_analysis': website_status.business_analysis,
                'business_type': website_status.business_type,
                'last_modified': website_status.last_modified,
                'crawl_timestamp': website_status.crawl_timestamp
            }
            
            print(f"Status Code: {website_status.status_code}")
            print(f"Pages Checked: {len(website_status.pages_checked)}")
            print(f"Emails Found: {len(website_status.emails_found)}")
            print(f"Products Found: {len(website_status.products_and_services['products'])}")
            print(f"Services Found: {len(website_status.products_and_services['services'])}")
            print(f"Categories Found: {len(website_status.products_and_services['categories'])}")
            if website_status.business_analysis:
                print(f"Business Type: {website_status.business_type}")
                print(f"Target Audience: {website_status.business_analysis.get('target_audience')}")
                print(f"Business Model: {website_status.business_analysis.get('business_model')}")
            
            results.append(result)
        
        return pd.DataFrame(results) 