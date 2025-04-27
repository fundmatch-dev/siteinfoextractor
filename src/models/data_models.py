from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Any
from datetime import datetime

class Product(BaseModel):
    name: str = Field(description="Name of the product")
    description: Optional[str] = Field(description="Description of the product")
    price: Optional[float] = Field(description="Price of the product")
    category: Optional[str] = Field(description="Category of the product")
    features: Optional[List[str]] = Field(description="Key features of the product")
    specifications: Optional[Dict[str, str]] = Field(description="Technical specifications")

class Service(BaseModel):
    name: str = Field(description="Name of the service")
    description: Optional[str] = Field(description="Description of the service")
    price: Optional[float] = Field(description="Price of the service")
    duration: Optional[str] = Field(description="Duration of the service")
    category: Optional[str] = Field(description="Category of the service")
    includes: Optional[List[str]] = Field(description="What's included in the service")

class BusinessAnalysis(BaseModel):
    business_type: str = Field(description="Type of business (e.g., retail, restaurant, service)")
    main_offerings: List[str] = Field(description="Main products or services offered")
    target_audience: Optional[str] = Field(description="Target audience or customer base")
    unique_selling_points: Optional[List[str]] = Field(description="Unique selling points or differentiators")
    price_range: Optional[str] = Field(description="General price range (e.g., budget, mid-range, premium)")
    business_model: Optional[str] = Field(description="Business model (e.g., B2C, B2B, subscription)")

class WebsiteStatus(BaseModel):
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    is_success: bool = False
    emails_found: List[str] = []
    pages_checked: List[Dict[str, str]] = []
    social_media: Dict[str, Optional[str]] = {
        'facebook': None,
        'twitter': None,
        'instagram': None,
        'linkedin': None
    }
    contact_info: Dict[str, Union[List[str], str, None]] = {
        'phone_numbers': [],
        'addresses': [],
        'business_hours': None
    }
    meta_info: Dict[str, Optional[str]] = {
        'title': None,
        'description': None,
        'keywords': None
    }
    products_and_services: Dict[str, List] = {
        'products': [],
        'services': [],
        'categories': [],
        'price_ranges': [],
        'featured_items': []
    }
    business_analysis: Optional[BusinessAnalysis] = None
    business_type: Optional[str] = None
    last_modified: Optional[str] = None
    crawl_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat()) 