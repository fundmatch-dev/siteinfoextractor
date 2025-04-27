# SiteInfoExtractor

A comprehensive tool for extracting and analyzing information from business websites. This tool combines web scraping with AI-powered analysis to gather detailed information about businesses, their products, services, and online presence.

## Features

- Email extraction with smart cleaning and validation
- Social media link detection
- Contact information extraction (phone numbers, business hours)
- Product and service detection with AI-enhanced analysis
- Business type classification
- Meta information extraction
- Structured data parsing (JSON-LD, Microdata, etc.)
- Anti-bot detection measures
- Comprehensive error handling

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/SiteInfoExtractor.git
cd SiteInfoExtractor
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenAI API key:

```plaintext
OPENAI_API_KEY=your_api_key_here
```

## Usage

Basic usage with a DataFrame:

```python
import pandas as pd
from src.site_info_extractor import SiteInfoExtractor

# Create DataFrame with business information
data = {
    'name': ['Business 1', 'Business 2'],
    'address': ['123 Main St', '456 Oak Ave'],
    'phone_number': ['555-0123', '555-0456'],
    'website': ['https://example1.com', 'https://example2.com']
}
df = pd.DataFrame(data)

# Initialize extractor
extractor = SiteInfoExtractor()

# Process businesses
results_df = extractor.process_businesses(df)

# Save results
results_df.to_csv('extraction_results.csv', index=False)
```

## Output Structure

The tool extracts and structures the following information:

```python
{
    'name': 'Business Name',
    'address': 'Business Address',
    'phone': 'Phone Number',
    'website': 'Website URL',
    'emails': ['email1@domain.com', 'email2@domain.com'],
    'social_media': {
        'facebook': 'URL',
        'twitter': 'URL',
        'instagram': 'URL',
        'linkedin': 'URL'
    },
    'contact_info': {
        'phone_numbers': ['123-456-7890'],
        'addresses': ['123 Main St'],
        'business_hours': 'Mon-Fri 9-5'
    },
    'meta_info': {
        'title': 'Page Title',
        'description': 'Meta Description',
        'keywords': 'Keywords'
    },
    'products_and_services': {
        'products': [...],
        'services': [...],
        'categories': [...],
        'featured_items': [...]
    },
    'business_analysis': {
        'business_type': 'type',
        'main_offerings': [...],
        'target_audience': 'audience',
        'unique_selling_points': [...],
        'price_range': 'range',
        'business_model': 'model'
    }
}
```

## Anti-Bot Detection Measures

The tool implements several measures to avoid being detected as a bot:

- Random user agent rotation
- Random delays between requests
- Session handling
- Proper headers
- Respect for robots.txt
- Random referrers

## Error Handling

The tool provides comprehensive error handling and reporting:

- Connection errors
- HTTP errors
- Timeout errors
- Invalid data
- API errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
