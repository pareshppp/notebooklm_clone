import streamlit as st
from src.ui import render_sources_column, render_chat_column, render_tools_notes_column

# Initialize session state variables if they don't exist
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'notes' not in st.session_state:
    st.session_state.notes = []

st.set_page_config(layout="wide", page_title="NotebookLM")

# Main app layout with three columns
left_col, middle_col, right_col = st.columns([1, 2, 1])

# Render each column
with left_col:
    render_sources_column()

with middle_col:
    render_chat_column()

with right_col:
    render_tools_notes_column()