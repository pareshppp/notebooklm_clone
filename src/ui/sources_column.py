import streamlit as st
from pathlib import Path
import mimetypes
from typing import Optional

from src.sources.doc_parser import DocumentParser

def is_supported_file(file_path: str) -> bool:
    """Check if the file type is supported by the parser."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type.startswith('text/') or mime_type in [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
    return False

def handle_file_upload(uploaded_file, upload_dir: Path = Path(".cache/uploaded_docs")) -> Optional[str]:
    """Handle file upload and return the parsed file path if successful."""
    if uploaded_file is None:
        return None
        
    # Save uploaded file to temp location
    upload_dir.mkdir(exist_ok=True)
    file_upload_path = upload_dir / uploaded_file.name
    
    with open(file_upload_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if is_supported_file(str(file_upload_path)):
        # Parse the file
        parsed_path = st.session_state.doc_parser.parse_file(str(file_upload_path))
        return parsed_path
    else:
        st.error(f"Unsupported file type: {uploaded_file.name}")
        return None

def handle_url_source(url: str) -> Optional[str]:
    """Handle URL source addition and return the URL if valid."""
    if not url:
        return None
        
    # Here you could add URL validation if needed
    return url

def render_sources_column():
    """Render the sources column with source management functionality."""
    st.header("Sources")
    
    # Initialize document parser
    if 'doc_parser' not in st.session_state:
        st.session_state.doc_parser = DocumentParser()
    
    # Initialize sources list if not exists
    if 'sources' not in st.session_state:
        st.session_state.sources = []
    
    # Initialize file processing flag
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False

    # Source type selector
    source_type = st.selectbox(
        "Source Type",
        options=["File Upload", "URL"],
        key="source_type"
    )
    
    if source_type == "File Upload":
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=["txt", "pdf", "docx", "md"],
            help="Supported formats: TXT, PDF, DOCX, MD"
        )
        
        if uploaded_file and not st.session_state.file_processed:
            with st.spinner(f"Processing {uploaded_file.name}... This may take a moment."):
                parsed_path = handle_file_upload(uploaded_file)
                if parsed_path and parsed_path not in st.session_state.sources:
                    st.session_state.sources.append(parsed_path)
                    st.success(f"File processed and added: {uploaded_file.name}")
                    st.session_state.file_processed = True
                    st.rerun()
        elif uploaded_file is None:
            st.session_state.file_processed = False
                
    else:  # URL input
        # URL input with its own submit button
        url_input = st.text_input(
            "Enter URL",
            key="url_input",
            placeholder="https://example.com/document"
        )
        
        if st.button("Add URL Source"):
            if url := handle_url_source(url_input):
                if url not in st.session_state.sources:
                    st.session_state.sources.append(url)
                    st.success("URL source added successfully")
                    st.rerun()
                else:
                    st.warning("This URL is already in your sources")
    
    # Display current sources
    if st.session_state.sources:
        st.subheader("Current Sources")
        for i, source in enumerate(st.session_state.sources):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.text(str(source))
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.sources.pop(i)
                    st.rerun()
    else:
        st.info("No sources added yet. Add some sources to get started!")
