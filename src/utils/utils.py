import streamlit as st
from pathlib import Path

def read_source_files() -> str:
    """
    Read and combine content from all markdown files in the sources list.
    
    Returns:
        str: Combined content from all source files
    """
    if 'sources' not in st.session_state:
        return ""
        
    content_parts = []
    
    for source in st.session_state.sources:
        try:
            with open(source, 'r') as f:
                content_parts.append(f.read())
        except Exception as e:
            st.error(f"Error reading source file {source}: {str(e)}")
            continue
            
    return "\n\n".join(content_parts)
