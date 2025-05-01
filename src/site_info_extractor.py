import pandas as pd
from typing import List, Dict, Optional
import time
import random
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
import json

from .models.data_models import WebsiteStatus, BusinessProfile, BusinessAnalysis, ProductService
from .utils.setup_validator import load_environment
from .scrapers.web_scraper import (
    make_request,
    extract_emails_from_text,
    extract_emails_from_links,
    clean_and_validate_email,
    extract_social_media,
    extract_contact_info,
    extract_meta_info,
    extract_business_profile,
    extract_products_services,
    crawl_website
)
from .analyzers.ai_analyzer import (
    analyze_business_profile_with_ai,
    analyze_business_with_ai,
    analyze_product_service_with_ai
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
    
    def process_website(self, url: str) -> WebsiteStatus:
        """Process a single website and extract all available information"""
        website_status = WebsiteStatus()
        
        try:
            # First, crawl the entire website
            print(f"\nCrawling website: {url}")
            crawled_data = crawl_website(url)
            website_status.pages_checked = crawled_data['pages_checked']
            
            # Extract structured data only from the main page
            print("Extracting structured data...")
            try:
                response, _ = make_request(url)
                structured_data = self.extract_structured_data(response.text, url)
            except Exception as e:
                print(f"Error extracting structured data: {str(e)}")
                structured_data = {
                    'json-ld': [],
                    'microdata': [],
                    'opengraph': [],
                    'microformat': []
                }
            
            # Extract and process business profile
            print("Extracting business profile...")
            business_profile = crawled_data['business_profile']
            
            # Process products and services
            print("Processing products and services...")
            products_services = crawled_data['products_services']
            
            # Combine only essential data for AI analysis
            print("Performing AI analysis...")
            try:
                # Prepare minimal context for AI analysis
                business_context = {
                    'profile': {
                        'name': business_profile.get('name', ''),
                        'primary_category': business_profile.get('primary_category', ''),
                        'industry': business_profile.get('industry', ''),
                        'main_offerings': business_profile.get('main_offerings', [])[:5],  # Limit to top 5
                        'price_range': business_profile.get('price_range', ''),
                        'target_segments': business_profile.get('target_segments', [])[:5]  # Limit to top 5
                    },
                    'products_services': [{
                        'name': ps.get('name', ''),
                        'type': ps.get('type', ''),
                        'category': ps.get('category', '')
                    } for ps in products_services[:5]]  # Limit to top 5
                }
                
                # Do single AI analysis for business profile
                enhanced_profile = analyze_business_profile_with_ai(
                    business_context['profile'],
                    json.dumps(business_context)
                )
                website_status.business_profile = enhanced_profile
                
                # Do single AI analysis for business insights
                website_status.business_analysis = analyze_business_with_ai(
                    json.dumps(business_context),
                    json.dumps(crawled_data)
                )
                
            except Exception as e:
                print(f"Error during AI analysis: {str(e)}")
                website_status.business_profile = business_profile
            
            # Update status
            website_status.is_success = True
            website_status.status_code = 200
            
        except Exception as e:
            website_status.error_message = str(e)
            website_status.is_success = False
            if not website_status.pages_checked:
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
                'status_code': website_status.status_code,
                'error_message': website_status.error_message,
                'pages_checked': website_status.pages_checked,
                'business_profile': website_status.business_profile.dict() if website_status.business_profile else None,
                'business_analysis': website_status.business_analysis.dict() if website_status.business_analysis else None,
                'last_modified': website_status.last_modified,
                'crawl_timestamp': website_status.crawl_timestamp
            }
            
            print(f"Status Code: {website_status.status_code}")
            print(f"Pages Checked: {len(website_status.pages_checked)}")
            if website_status.business_profile:
                print(f"Business Size: {website_status.business_profile.business_size}")
                print(f"Years in Business: {website_status.business_profile.years_in_business}")
                print(f"Main Offerings: {len(website_status.business_profile.main_offerings)}")
            if website_status.business_analysis:
                print(f"Business Maturity: {website_status.business_analysis.business_maturity}")
                print(f"Growth Indicators: {len(website_status.business_analysis.growth_indicators)}")
                print(f"Outreach Opportunities: {len(website_status.business_analysis.outreach_opportunities)}")
            
            results.append(result)
            
            # Random delay between websites
            time.sleep(random.uniform(3, 7))
        
        return pd.DataFrame(results) 