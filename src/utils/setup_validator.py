import os
import sys
from dotenv import load_dotenv

def verify_openai_setup():
    """Verify OpenAI API key format and environment setup without making API calls"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please ensure you have created a .env file with your OpenAI API key")
        print("Example .env file content:")
        print("OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Check if API key starts with expected prefix
    if not api_key.startswith(('sk-', 'sk_')):
        print("\n❌ Error: Invalid OpenAI API key format")
        print("API key should start with 'sk-' or 'sk_'")
        print("Please check your .env file and ensure the API key is correct")
        sys.exit(1)
    
    # Check minimum length for API key (typical length is around 51 characters)
    if len(api_key) < 40:
        print("\n❌ Warning: API key seems too short")
        print("A typical OpenAI API key is about 51 characters long")
        print("Please verify your API key is complete")
        sys.exit(1)
    
    print("\n✅ OpenAI API key format verification successful!")
    print(f"API Key found: sk-...{api_key[-4:]}")
    return True

def load_environment():
    """Load environment variables and verify required settings"""
    load_dotenv()
    verify_openai_setup()
    
    # Add any additional environment verifications here
    return True 