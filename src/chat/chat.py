from typing import TypedDict, Annotated, Sequence, Dict, Any
from typing_extensions import TypedDict
import operator
from datetime import datetime
import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langchain_chroma import Chroma
import vertexai
import os
from langchain_google_vertexai import VertexAIEmbeddings
from pathlib import Path

import dotenv
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define state schema
class AgentState(TypedDict):
    messages: Sequence[HumanMessage | AIMessage]
    context: list[str]
    current_time: str

# Initialize components
llm = ChatVertexAI(
    model="gemini-1.5-flash-002",
    max_output_tokens=1024,
    temperature=0,
)

embeddings = VertexAIEmbeddings(model_name="text-embedding-005")

vectordb = Chroma(
    persist_directory=str(Path(".cache/vectordb")),
    collection_name=f"document_chunks",
    embedding_function=embeddings
)
retriever = vectordb.as_retriever(search_kwargs={"k": 4})


# Create the chat prompt
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant with access to a knowledge base of documents. 
    Use the provided context to answer questions accurately. If you don't find relevant information 
    in the context, say so and answer based on your general knowledge.
    
    Current time: {current_time}
    
    Context from documents:
    {context}
    """),
    MessagesPlaceholder(variable_name="messages"),
])

# Define RAG functions
def retrieve_context(state: AgentState) -> AgentState:
    """Retrieve relevant context from vector store."""
    try:
        # Get the last message
        last_message = state["messages"][-1]
        logger.info(f"Retrieving context for message: {last_message.content}")
        if not isinstance(last_message, HumanMessage):
            return state
        
        # Search vectordb
        results = retriever.invoke(last_message.content)
        context = [doc.page_content for doc in results]
        
        # Update state
        state["context"] = context
        logger.info(f"Retrieved {len(context)} context chunks")
        return state
    except Exception as e:
        logger.error(f"Error in retrieve_context: {str(e)}")
        raise

def generate_response(state: AgentState) -> AgentState:
    """Generate response using context and chat history."""
    try:
        # Format context
        context_str = "\n\n".join(state["context"]) if state["context"] else "No relevant context found."
        
        # Generate response
        chain = chat_prompt | llm | StrOutputParser()
        response = chain.invoke({
            "messages": state["messages"],
            "context": context_str,
            "current_time": state["current_time"]
        })
        
        # Add response to messages
        state["messages"].append(AIMessage(content=response))
        logger.info("Generated response successfully")
        return state
    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}")
        raise

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("generate_response", generate_response)

# Add edges
workflow.add_edge("retrieve_context", "generate_response")
workflow.add_edge("generate_response", END)

# Set entry point
workflow.set_entry_point("retrieve_context")

# Compile the graph
chain = workflow.compile()

def chat_response(message: str, history: list[dict]) -> str:
    """
    Process a chat message and return the response.
    
    Args:
        message: The user's message
        history: List of previous messages in the format [{"role": "user"|"assistant", "content": str}]
        
    Returns:
        str: The assistant's response
    """
    try:
        # Convert history to LangChain message format
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        # Prepare initial state
        state = {
            "messages": messages,
            "context": [],
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Run the chain
        result = chain.invoke(state)
        logger.info("Chain execution completed successfully")
        
        # Return the last message
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Error in chat_response: {str(e)}")
        raise