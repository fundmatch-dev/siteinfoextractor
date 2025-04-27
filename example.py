import pandas as pd
from src.site_info_extractor import SiteInfoExtractor

def main():
    # Create sample DataFrame
    data = {
        'name': ['Example Business 1', 'Example Business 2'],
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
    print("\nResults saved to extraction_results.csv")

if __name__ == "__main__":
    main() 