from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
import json
import os
from ..models.data_models import Product, Service, BusinessAnalysis

# Initialize LangChain components
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo-16k",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
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