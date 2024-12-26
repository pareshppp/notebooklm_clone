import logging
from typing import List
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

from src.utils.utils import read_source_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
llm = ChatVertexAI(
    model="gemini-1.5-flash-002",
    max_output_tokens=1024,
    temperature=0.7,
)

# Create the FAQs prompt
faqs_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at identifying and creating frequently asked questions from documents.
    Generate a comprehensive list of FAQs based on the provided content. The FAQs should:
    - Cover the most important and common questions users might have
    - Include clear and concise answers
    - Be organized by topic
    - Be practical and useful for the target audience
    - Include at least 10 questions and answers
    
    Format each FAQ as:
    Q: [Question]
    A: [Answer]
    """),
    ("user", "Content to analyze: \n\n {source_content}")
])

# Create the FAQs chain
faqs_chain = faqs_prompt | llm | StrOutputParser()

def generate_faqs() -> str:
    """
    Generate FAQs from all source documents.
    
    Returns:
        str: Generated FAQs
    """
    try:
        logger.info("Reading source files")
        content = read_source_files()
        
        if not content:
            return "No source files found to generate FAQs."
        
        logger.info("Generating FAQs")
        # Generate FAQs
        faqs = faqs_chain.invoke({"source_content": content})
        
        logger.info("FAQs generated successfully")
        return faqs
        
    except Exception as e:
        logger.error(f"Error generating FAQs: {str(e)}")
        raise