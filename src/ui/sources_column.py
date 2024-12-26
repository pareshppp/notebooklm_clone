import streamlit as st
from pathlib import Path
from src.doc_parser import DocumentParser
import mimetypes

def is_supported_file(file_path: str) -> bool:
    """Check if the file type is supported by the parser."""
    mime_type, _ = mimetypes.guess_type(file_path)
    file_path = Path(file_path)
    return (mime_type in ["text/plain", "application/pdf"] or 
            mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or
            file_path.suffix in [".txt", ".md"])

def render_sources_column():
    """Render the sources column with source management functionality."""
    st.header("Sources")
    
    # Initialize document parser
    if 'doc_parser' not in st.session_state:
        st.session_state.doc_parser = DocumentParser()
    
    # Add source input and button
    new_source = st.text_input("Enter source URL or path", key="new_source_input")
    if st.button("Add Source") and new_source:
        try:
            source_path = Path(new_source)
            if source_path.exists() and is_supported_file(new_source):
                # Parse the file and get markdown path
                parsed_path = st.session_state.doc_parser.parse_file(new_source)
                if parsed_path not in st.session_state.sources:
                    st.session_state.sources.append(parsed_path)
                    st.success(f"File parsed and added: {source_path.name}")
                    st.rerun()
            else:
                # Add as regular source if not a supported file
                if new_source not in st.session_state.sources:
                    st.session_state.sources.append(new_source)
                    st.rerun()
        except Exception as e:
            st.error(f"Error adding source: {str(e)}")
    
    # Display sources
    if st.session_state.sources:
        st.subheader("Added Sources:")
        for idx, source in enumerate(st.session_state.sources):
            col1, col2 = st.columns([4, 1])
            with col1:
                source_path = Path(source)
                display_name = source_path.name if source_path.exists() else source
                st.write(f"{idx + 1}. {display_name}")
            with col2:
                if st.button("🗑️", key=f"remove_{idx}"):
                    st.session_state.sources.pop(idx)
                    st.rerun()
    else:
        st.info("No sources added yet")
