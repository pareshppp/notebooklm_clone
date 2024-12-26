from pathlib import Path
import pypdf
from docx import Document
import datetime
import mimetypes
import logging
from .vectordb_ingestion import VectorDBIngestion

class DocumentParser:
    """Parser for various document formats (txt, md, pdf, docx)."""
    
    def __init__(self):
        self.cache_dir = Path(".cache/.parsed_docs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.vectordb = VectorDBIngestion()
        
    def parse_file(self, file_path: str) -> str:
        """
        Parse a file and return path to the markdown output file.
        Supported formats: txt, md, pdf, docx
        
        Args:
            file_path: Path to the input file
            
        Returns:
            str: Path to the output markdown file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Detect file type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "text/plain" if file_path.suffix in [".txt", ".md"] else None
            
        # Parse based on file type
        try:
            if mime_type == "text/plain" or file_path.suffix in [".txt", ".md"]:
                content = self._parse_text_file(file_path)
            elif mime_type == "application/pdf":
                content = self._parse_pdf(file_path)
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                content = self._parse_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
            # Save to markdown file
            return self._save_to_markdown(content, file_path.name)
            
        except Exception as e:
            logging.error(f"Error parsing file {file_path}: {str(e)}")
            raise
    
    def _parse_text_file(self, file_path: Path) -> str:
        """Parse text or markdown files."""
        return file_path.read_text()
    
    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF files."""
        content = []
        with open(file_path, "rb") as file:
            pdf = pypdf.PdfReader(file)
            for page in pdf.pages:
                content.append(page.extract_text())
        return "\n\n".join(content)
    
    def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX files."""
        doc = Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)
        return "\n\n".join(content)
    
    def _save_to_markdown(self, content: str, original_filename: str) -> str:
        """
        Save content to a markdown file in the cache directory and index it.
        
        Args:
            content: The content to save
            original_filename: Name of the original file
            
        Returns:
            str: Path to the saved markdown file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"parsed_{Path(original_filename).stem}_{timestamp}.md"
        output_path = self.cache_dir / output_filename
        
        # Add metadata header
        header = f"# Parsed Document: {original_filename}\n"
        header += f"Parsed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        header += "---\n\n"
        
        full_content = header + content
        output_path.write_text(full_content)
        
        # Index the document in vector database
        try:
            self.vectordb.process_document(
                str(output_path),
                source_id=original_filename
            )
            logging.info(f"Indexed document in vector database: {original_filename}")
        except Exception as e:
            logging.error(f"Error indexing document {original_filename}: {str(e)}")
        
        return str(output_path)