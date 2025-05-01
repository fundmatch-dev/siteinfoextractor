from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.callbacks.base import BaseCallbackHandler
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from ..models.data_models import BusinessAnalysis, BusinessProfile, ProductService

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create a log file with timestamp
log_filename = os.path.join(log_dir, f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Token usage tracking
class TokenUsage:
    def __init__(self):
        self.usage_history: List[Dict] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    def add_usage(self, llm_output: Dict):
        # OpenAI GPT-4 pricing (as of April 2024)
        # PRICING = {
        #     "gpt-4.1": {
        #         "input": 0.01 / 1000,    # $0.01 per 1K tokens
        #         "output": 0.03 / 1000     # $0.03 per 1K tokens
        #     },
        #     "gpt-4": {
        #         "input": 0.03 / 1000,    # $0.03 per 1K tokens
        #         "output": 0.06 / 1000     # $0.06 per 1K tokens
        #     },
        #     "gpt-4-turbo": {
        #         "input": 0.01 / 1000,    # $0.01 per 1K tokens
        #         "output": 0.03 / 1000     # $0.03 per 1K tokens
        #     },
        #     "gpt-3.5-turbo": {
        #         "input": 0.0005 / 1000,  # $0.0005 per 1K tokens
        #         "output": 0.0015 / 1000   # $0.0015 per 1K tokens
        #     }
        # }

        PRICING = {
            "gpt-4.1": {
                "input": 0.002 / 1000,    # $0.002 per 1K tokens
                "output": 0.008 / 1000    # $0.008 per 1K tokens
            },
            "gpt-4.1-mini": {
                "input": 0.0004 / 1000,   # $0.0004 per 1K tokens
                "output": 0.0016 / 1000   # $0.0016 per 1K tokens
            },
            "gpt-4.1-nano": {
                "input": 0.0001 / 1000,   # $0.0001 per 1K tokens
                "output": 0.0004 / 1000   # $0.0004 per 1K tokens
            }
        }

        
        token_usage = llm_output["token_usage"]
        model = llm_output.get("model", "gpt-4.1")  # Default to gpt-4.1 if model not specified
        
        # Calculate cost based on input and output tokens
        input_cost = token_usage["prompt_tokens"] * PRICING[model]["input"]
        output_cost = token_usage["completion_tokens"] * PRICING[model]["output"]
        total_cost = input_cost + output_cost
        
        usage = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": token_usage["prompt_tokens"],
            "completion_tokens": token_usage["completion_tokens"],
            "total_tokens": token_usage["total_tokens"],
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
        
        self.usage_history.append(usage)
        self.total_tokens += usage["total_tokens"]
        self.total_cost += total_cost

        # Log the usage with more detailed cost breakdown
        logger.info(f"API Call - Model: {model}")
        logger.info(f"Tokens: {usage['total_tokens']} (Input: {usage['prompt_tokens']}, Output: {usage['completion_tokens']})")
        logger.info(f"Cost Breakdown:")
        logger.info(f"  Input: ${usage['input_cost']:.4f}")
        logger.info(f"  Output: ${usage['output_cost']:.4f}")
        logger.info(f"  Total: ${usage['total_cost']:.4f}")
        logger.info(f"Running Total: {self.total_tokens} tokens, ${self.total_cost:.4f}")
        
        return usage

    def get_summary(self) -> Dict:
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "number_of_calls": len(self.usage_history),
            "average_cost_per_call": self.total_cost / len(self.usage_history) if self.usage_history else 0,
            "average_tokens_per_call": self.total_tokens / len(self.usage_history) if self.usage_history else 0
        }

# Global token usage tracker
token_usage = TokenUsage()

# Custom callback handler for token tracking
class TokenTrackingCallback(BaseCallbackHandler):
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes running."""
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage.add_usage(response.llm_output)

# Initialize LangChain components
llm = ChatOpenAI(
    model_name="gpt-4.1",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[TokenTrackingCallback()]
)

# LangChain prompts
BUSINESS_ANALYSIS_TEMPLATE = """
Analyze the following business information and provide insights about the business type,
target audience, and business model.

Business Information:
{business_text}

Website Content:
{website_content}

{format_instructions}
"""

BUSINESS_PROFILE_ANALYSIS_TEMPLATE = """
Analyze the following business profile information and enhance it with additional insights.
Focus on identifying business characteristics that would be valuable for outreach.

Business Profile:
{profile_text}

Website Content:
{website_content}

{format_instructions}
"""

PRODUCT_SERVICE_ANALYSIS_TEMPLATE = """
Analyze the following product or service information and structure it into a standardized format.
Focus on identifying the type, category, and price range.

Product/Service Information:
{product_service_text}

{format_instructions}
"""

def analyze_business_with_ai(website_content: str, structured_data: dict) -> BusinessAnalysis:
    """Use LangChain to analyze and provide business insights"""
    parser = PydanticOutputParser(pydantic_object=BusinessAnalysis)
    prompt = ChatPromptTemplate.from_template(
        template=BUSINESS_ANALYSIS_TEMPLATE
    )
    
    # Split text if it's too long
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200
    )
    
    if len(website_content) > 4000:
        chunks = text_splitter.split_text(website_content)
        website_content = chunks[0]  # Use first chunk for analysis
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=parser
    )
    
    result = chain.run(
        business_text=json.dumps(structured_data),
        website_content=website_content,
        format_instructions=parser.get_format_instructions()
    )
    
    return result

def analyze_business_profile_with_ai(profile: dict, website_content: str) -> dict:
    """Use LangChain to analyze and enhance business profile information"""
    parser = PydanticOutputParser(pydantic_object=BusinessProfile)
    prompt = ChatPromptTemplate.from_template(
        template=BUSINESS_PROFILE_ANALYSIS_TEMPLATE
    )
    
    # Split text if it's too long
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200
    )
    
    if len(website_content) > 4000:
        chunks = text_splitter.split_text(website_content)
        website_content = chunks[0]  # Use first chunk for analysis
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=parser
    )
    
    result = chain.run(
        profile_text=json.dumps(profile),
        website_content=website_content,
        format_instructions=parser.get_format_instructions()
    )
    
    return result

def analyze_product_service_with_ai(product_service_info: dict) -> ProductService:
    """Use LangChain to analyze and structure product/service information"""
    parser = PydanticOutputParser(pydantic_object=ProductService)
    prompt = ChatPromptTemplate.from_template(
        template=PRODUCT_SERVICE_ANALYSIS_TEMPLATE
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=parser
    )
    
    result = chain.run(
        product_service_text=json.dumps(product_service_info),
        format_instructions=parser.get_format_instructions()
    )
    
    return result

def get_token_usage_summary() -> Dict:
    """Get a summary of token usage and costs"""
    summary = token_usage.get_summary()
    logger.info("\nToken Usage Summary:")
    logger.info(f"Total API Calls: {summary['number_of_calls']}")
    logger.info(f"Total Tokens Used: {summary['total_tokens']}")
    logger.info(f"Total Cost: ${summary['total_cost']:.4f}")
    return summary

def get_token_usage_history() -> List[Dict]:
    """Get the complete history of token usage"""
    return token_usage.usage_history 