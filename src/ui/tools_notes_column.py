import streamlit as st
from datetime import datetime
import os
from pathlib import Path

def render_tools_section():
    """Render the tools section with action buttons."""
    st.header("Tools")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Summary"):
            note = "Generated summary..."
            st.session_state.notes.append({
                "type": "summary",
                "content": note,
                "timestamp": datetime.now()
            })
            st.rerun()
        
        if st.button("FAQs"):
            note = "Generated FAQs..."
            st.session_state.notes.append({
                "type": "faqs",
                "content": note,
                "timestamp": datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("Outline"):
            note = "Generated outline..."
            st.session_state.notes.append({
                "type": "outline",
                "content": note,
                "timestamp": datetime.now()
            })
            st.rerun()
        
        if st.button("Podcast"):
            note = "Generated podcast script..."
            st.session_state.notes.append({
                "type": "podcast",
                "content": note,
                "timestamp": datetime.now()
            })
            st.rerun()

def save_notes_to_markdown():
    """Save all notes to a markdown file and return the file path."""
    if not st.session_state.notes:
        return None
        
    # Create notes directory if it doesn't exist
    notes_dir = Path(".cache/.notes")
    notes_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_notes_{timestamp}.md"
    filepath = notes_dir / filename
    
    # Combine notes with separators
    combined_notes = "\n\n=================================\n\n".join([
        f"[{note['type'].upper()} - {note['timestamp'].strftime('%Y-%m-%d %H:%M')}]\n{note['content']}"
        for note in st.session_state.notes
    ])
    
    # Add header with metadata
    header = f"# Notes Collection - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    full_content = header + combined_notes
    
    # Write to file
    filepath.write_text(full_content)
    return str(filepath)

def render_notes_section():
    """Render the notes section with note management."""
    st.header("Notes")
    
    # Add custom note
    custom_note = st.text_area("Add a custom note", key="custom_note_input")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Add Note") and custom_note:
            st.session_state.notes.append({
                "type": "custom",
                "content": custom_note,
                "timestamp": datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("Add Notes to Source"):
            if st.session_state.notes:
                # Save notes to markdown file
                notes_file = save_notes_to_markdown()
                if notes_file and notes_file not in st.session_state.sources:
                    st.session_state.sources.append(notes_file)
                    st.success(f"Notes saved to {notes_file} and added to sources")
                    st.rerun()
            else:
                st.warning("No notes available to add as source")
    
    # Display all notes
    if st.session_state.notes:
        for idx, note in enumerate(reversed(st.session_state.notes)):
            with st.expander(f"{note['type'].title()} - {note['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(note['content'])
                if st.button("Delete", key=f"delete_note_{idx}"):
                    st.session_state.notes.remove(note)
                    st.rerun()
    else:
        st.info("No notes added yet")

def render_tools_notes_column():
    """Render the complete tools and notes column."""
    render_tools_section()
    render_notes_section()
