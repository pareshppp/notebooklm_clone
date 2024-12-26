import streamlit as st
import logging
from src.chat import chat_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_chat_column():
    """Render the chat column with message history and input."""
    st.header("Chat")
    
    # Initialize chat messages if not exists
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Create a container for messages
    messages_container = st.container()
    
    # Chat input at the bottom
    prompt = st.chat_input("Type your message here...")
    
    # Display existing messages
    with messages_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Handle new message
    if prompt:
        try:
            # Display user message immediately
            with messages_container:
                with st.chat_message("user"):
                    st.write(prompt)
            
            # Add to session state
            st.session_state.chat_messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Show typing indicator
            with messages_container:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Get response from RAG agent
                            response = chat_response(prompt, st.session_state.chat_messages[:-1])
                            logger.info("Got response from chat agent")
                        except Exception as e:
                            logger.error(f"Error getting chat response: {str(e)}")
                            raise
            
            # Add AI response to session state
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Display assistant response
            with messages_container:
                with st.chat_message("assistant"):
                    st.write(response)
                    
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            # Remove the user message if we couldn't get a response
            if len(st.session_state.chat_messages) > 0:
                st.session_state.chat_messages.pop()
            return
        
        # Rerun to update UI
        st.rerun()
