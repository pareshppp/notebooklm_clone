import logging
from typing import List
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
import vertexai
import os
import dotenv
dotenv.load_dotenv()

from src.utils.utils import read_source_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Initialize components
llm = ChatVertexAI(
    model="gemini-1.5-flash-002",
    max_output_tokens=8096,
    temperature=0.2,
)

# Create the summary prompt
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a skilled summarizer who can create concise, informative summaries of documents.
    Create a comprehensive summary of the provided content that captures the main ideas, key points, and important details.
    The summary should be well-structured and easy to understand.
    """),
    ("user", """Summarize the following content: \n\n {source_content}""")
])

# Create the summary chain
summary_chain = summary_prompt | llm | StrOutputParser()

def generate_summary() -> str:
    """
    Generate a summary of all source documents.
    
    Returns:
        str: Generated summary
    """
    try:
        logger.info("Reading source files")
        content = read_source_files()
        logger.debug(f"Content: {content}")
        
        if not content:
            return "No source files found to summarize."
        
        logger.info("Generating summary")
        # Generate summary
        summary = summary_chain.invoke({"source_content": content})
        
        logger.info("Summary generated successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise