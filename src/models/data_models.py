from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Any
from datetime import datetime
from enum import Enum

class BusinessSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    UNKNOWN = "unknown"

class PriceRange(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    PREMIUM = "premium"
    UNKNOWN = "unknown"

class SalesModel(str, Enum):
    DIRECT = "direct"
    SUBSCRIPTION = "subscription"
    MARKETPLACE = "marketplace"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"

class DistributionChannel(str, Enum):
    ONLINE = "online"
    PHYSICAL = "physical"
    BOTH = "both"
    MOBILE_APP = "mobile_app"
    UNKNOWN = "unknown"

class BusinessProfile(BaseModel):
    """Core business information for outreach"""
    name: Optional[str] = Field(default="unknown", description="Business name")
    primary_category: Optional[str] = Field(default="unknown", description="Main business category")
    industry: Optional[str] = Field(default="unknown", description="Primary industry")
    business_size: Optional[BusinessSize] = Field(default=BusinessSize.UNKNOWN)
    years_in_business: Optional[int] = Field(default=None, description="Years in operation")
    
    # Core offerings
    main_offerings: Optional[List[str]] = Field(default_factory=list, description="Main products/services")
    price_range: Optional[PriceRange] = Field(default=PriceRange.UNKNOWN)
    target_segments: Optional[List[str]] = Field(default_factory=list, description="Target customer segments")
    
    # Business model
    sales_model: Optional[SalesModel] = Field(default=SalesModel.UNKNOWN)
    distribution_channels: Optional[List[DistributionChannel]] = Field(
        default_factory=lambda: [DistributionChannel.UNKNOWN]
    )
    service_delivery: Optional[List[str]] = Field(default_factory=list, description="Service delivery methods")
    
    # Contact information
    locations: Optional[List[str]] = Field(default_factory=list, description="Business locations")
    service_areas: Optional[List[str]] = Field(default_factory=list, description="Service coverage areas")
    contact_methods: Optional[Dict[str, List[str]]] = Field(
        default_factory=lambda: {
            "phone": [],
            "email": [],
            "contact_form": []
        }
    )
    social_media: Optional[Dict[str, Optional[str]]] = Field(
        default_factory=lambda: {
            "facebook": None,
            "twitter": None,
            "instagram": None,
            "linkedin": None
        }
    )

class BusinessAnalysis(BaseModel):
    """AI-generated insights for outreach"""
    business_maturity: Optional[str] = Field(default="unknown", description="Assessment of business maturity")
    growth_indicators: Optional[List[str]] = Field(default_factory=list, description="Signs of business growth")
    potential_pain_points: Optional[List[str]] = Field(default_factory=list, description="Potential business challenges")
    outreach_opportunities: Optional[List[str]] = Field(default_factory=list, description="Identified outreach opportunities")
    personalization_points: Optional[Dict[str, List[str]]] = Field(
        default_factory=lambda: {
            "industry": [],
            "size": [],
            "offerings": [],
            "challenges": []
        },
        description="Key points for personalizing outreach"
    )

class WebsiteStatus(BaseModel):
    """Status of website crawling and extraction"""
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    is_success: bool = False
    pages_checked: List[Dict[str, str]] = []
    business_profile: Optional[BusinessProfile] = None
    business_analysis: Optional[BusinessAnalysis] = None
    last_modified: Optional[str] = None
    crawl_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ProductService(BaseModel):
    """Simple model for products and services"""
    name: Optional[str] = Field(default="unknown", description="Name of the product or service")
    type: Optional[str] = Field(default="unknown", description="Type: 'product' or 'service'")
    category: Optional[str] = Field(default="unknown", description="Category of the product/service")
    price_range: Optional[str] = Field(default="unknown", description="Price range: budget/mid-range/premium")
    description: Optional[str] = Field(default="", description="Brief description") 