from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
import json
import os
import logging
from datetime import datetime
from typing import Dict, List
from ..models.data_models import Product, Service, BusinessAnalysis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token usage tracking
class TokenUsage:
    def __init__(self):
        self.usage_history: List[Dict] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    def add_usage(self, llm_output: Dict):
        # GPT-3.5 Turbo pricing (as of 2024)
        PRICING = {
            "gpt-3.5-turbo": {
                "input": 0.0005 / 1000,  # $0.0005 per 1K tokens
                "output": 0.0015 / 1000   # $0.0015 per 1K tokens
            }
        }
        
        token_usage = llm_output["token_usage"]
        model = "gpt-3.5-turbo"  # We're using gpt-3.5-turbo-16k which has same pricing
        
        cost = (token_usage["prompt_tokens"] * PRICING[model]["input"]) + \
               (token_usage["completion_tokens"] * PRICING[model]["output"])
        
        usage = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": token_usage["prompt_tokens"],
            "completion_tokens": token_usage["completion_tokens"],
            "total_tokens": token_usage["total_tokens"],
            "cost": cost
        }
        
        self.usage_history.append(usage)
        self.total_tokens += usage["total_tokens"]
        self.total_cost += cost

        # Log the usage
        logger.info(f"API Call - Tokens: {usage['total_tokens']} (Prompt: {usage['prompt_tokens']}, Completion: {usage['completion_tokens']})")
        logger.info(f"Cost: ${usage['cost']:.4f}")
        logger.info(f"Running Total: {self.total_tokens} tokens, ${self.total_cost:.4f}")
        
        return usage

    def get_summary(self) -> Dict:
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "number_of_calls": len(self.usage_history)
        }

# Global token usage tracker
token_usage = TokenUsage()

# Initialize LangChain components
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo-16k",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[lambda x: token_usage.add_usage(x.llm_output)]
)

# LangChain prompts
PRODUCT_ANALYSIS_TEMPLATE = """
Analyze the following product information and structure it into a standardized format.
Include any relevant details about specifications, features, and categorization.

Product Information:
{product_text}

{format_instructions}
"""

SERVICE_ANALYSIS_TEMPLATE = """
Analyze the following service information and structure it into a standardized format.
Include details about what's included, duration, and categorization.

Service Information:
{service_text}

{format_instructions}
"""

BUSINESS_ANALYSIS_TEMPLATE = """
Analyze the following business information and provide insights about the business type,
target audience, and business model.

Business Information:
{business_text}

Website Content:
{website_content}

{format_instructions}
"""

def analyze_product_with_ai(product_info: dict) -> Product:
    """Use LangChain to analyze and structure product information"""
    parser = PydanticOutputParser(pydantic_object=Product)
    prompt = ChatPromptTemplate.from_template(
        template=PRODUCT_ANALYSIS_TEMPLATE
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=parser
    )
    
    result = chain.run(
        product_text=json.dumps(product_info),
        format_instructions=parser.get_format_instructions()
    )
    
    return result

def analyze_service_with_ai(service_info: dict) -> Service:
    """Use LangChain to analyze and structure service information"""
    parser = PydanticOutputParser(pydantic_object=Service)
    prompt = ChatPromptTemplate.from_template(
        template=SERVICE_ANALYSIS_TEMPLATE
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=parser
    )
    
    result = chain.run(
        service_text=json.dumps(service_info),
        format_instructions=parser.get_format_instructions()
    )
    
    return result

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