from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings

import dotenv
dotenv.load_dotenv()

class VectorDBIngestion:
    """Handle document chunking and ingestion into Chroma vector database."""
    
    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize the ingestion handler.
        
        Args:
            persist_dir: Directory to persist the vector database. 
                       If None, uses .cache/.vectordb
        """
        self.persist_dir = Path(persist_dir) if persist_dir else Path(".cache/.vectordb")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize text splitter with default parameters
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize embeddings and vector store
        self.embeddings = VertexAIEmbeddings(model_name="text-embedding-005")
        

        
        # Initialize Chroma collection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.vectordb = Chroma(
            persist_directory=str(self.persist_dir),
            collection_name=f"document_chunks_{timestamp}",
            embedding_function=self.embeddings
        )
    
    def process_document(self, file_path: str, source_id: Optional[str] = None) -> List[str]:
        """
        Process a document: chunk it and add to vector database.
        
        Args:
            file_path: Path to the markdown file to process
            source_id: Optional unique identifier for the source
            
        Returns:
            List[str]: List of chunk IDs added to the database
        """
        try:
            # Read the markdown file
            content = Path(file_path).read_text()
            
            # Create metadata
            metadata = {
                "source": file_path,
                "source_id": source_id or file_path,
            }
            
            # Create Langchain document
            doc = Document(page_content=content, metadata=metadata)
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add to vector store
            ids = self.vectordb.add_documents(chunks)
            
            logging.info(f"Added {len(ids)} chunks from {file_path} to vector database")
            return ids
            
        except Exception as e:
            logging.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search the vector database for relevant chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List[Document]: List of relevant document chunks
        """
        return self.vectordb.similarity_search(query, k=k)
    
    def get_stats(self) -> dict:
        """Get statistics about the vector database."""
        try:
            collection = self.client.get_collection("document_chunks")
            count = collection.count()
            return {
                "total_chunks": count,
                "total_sources": len(set(m.get("source_id") for m in collection.get()["metadatas"] if m))
            }
        except Exception as e:
            logging.error(f"Error getting stats: {str(e)}")
            return {"total_chunks": 0, "total_sources": 0}