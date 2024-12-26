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

# Create the outline prompt
outline_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at creating structured outlines of complex documents.
    Create a detailed hierarchical outline of the provided content that shows the organization and flow of ideas.
    The outline should:
    - Use proper hierarchical structure (I, A, 1, a, etc.)
    - Include main topics and subtopics
    - Capture the logical flow of information
    - Be easy to follow and understand
    """),
    ("human", "Content to outline: \n\n {source_content}"),
    
])

# Create the outline chain
outline_chain = outline_prompt | llm | StrOutputParser()

def generate_outline() -> str:
    """
    Generate a hierarchical outline of all source documents.
    
    Returns:
        str: Generated outline
    """
    try:
        logger.info("Reading source files")
        content = read_source_files()
        
        if not content:
            return "No source files found to create outline."
        
        logger.info("Generating outline")
        # Generate outline
        outline = outline_chain.invoke({"source_content": content})
        
        logger.info("Outline generated successfully")
        return outline
        
    except Exception as e:
        logger.error(f"Error generating outline: {str(e)}")
        raise