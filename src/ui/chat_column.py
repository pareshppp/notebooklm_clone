import streamlit as st

def render_chat_column():
    """Render the chat column with message history and input."""
    st.header("Chat")
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Add AI response
        response = f"AI response to: {prompt}"
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        # Rerun to show messages immediately
        st.rerun()
