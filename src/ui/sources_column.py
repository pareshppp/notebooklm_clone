import streamlit as st

def render_sources_column():
    """Render the sources column with source management functionality."""
    st.header("Sources")
    
    # Add source input and button
    new_source = st.text_input("Enter source URL or path", key="new_source_input")
    if st.button("Add Source") and new_source:
        if new_source not in st.session_state.sources:  # Avoid duplicates
            st.session_state.sources.append(new_source)
            st.rerun()
    
    # Display sources
    if st.session_state.sources:
        st.subheader("Added Sources:")
        for idx, source in enumerate(st.session_state.sources):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{idx + 1}. {source}")
            with col2:
                if st.button("🗑️", key=f"remove_{idx}"):
                    st.session_state.sources.pop(idx)
                    st.rerun()
    else:
        st.info("No sources added yet")
