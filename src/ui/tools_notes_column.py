import streamlit as st
from datetime import datetime
import os
from pathlib import Path

from src.tools.summary import generate_summary
from src.tools.faqs import generate_faqs
from src.tools.outline import generate_outline
from src.podcast.synthesize_speech import create_podcast_audio
from src.sources.vectordb_ingestion import VectorDBIngestion

def render_tools_section():
    """Render the tools section with action buttons."""
    st.header("Tools")
    
    # Initialize session state for podcast settings if not exists
    if 'podcast_settings' not in st.session_state:
        st.session_state.podcast_settings = {
            'n_participants': 2,
            'target_audience': 'college students',
            'duration_mins': 15,
            'last_podcast': None
        }
    
    col1, col2, col3= st.columns(3)
    
    with col1:
        if st.button("Summary"):
            with st.spinner("Generating summary..."):
                note = generate_summary()
                st.session_state.notes.append({
                    "type": "summary",
                    "content": note,
                    "timestamp": datetime.now()
                })
                st.rerun()
    
    with col2:
        if st.button("FAQs"):
            with st.spinner("Generating FAQs..."):
                note = generate_faqs()
                st.session_state.notes.append({
                    "type": "faqs",
                    "content": note,
                    "timestamp": datetime.now()
                })
                st.rerun()

    with col3:
        if st.button("Outline"):
            with st.spinner("Generating outline..."):
                note = generate_outline()
                st.session_state.notes.append({
                    "type": "outline",
                    "content": note,
                    "timestamp": datetime.now()
                })
                st.rerun()

    # Add Podcast button with settings expander
    with st.expander("Podcast Settings"):
        st.session_state.podcast_settings['n_participants'] = st.slider(
            "Number of Participants (excluding host)",
            min_value=1,
            max_value=3,
            value=st.session_state.podcast_settings['n_participants']
        )
        
        st.session_state.podcast_settings['target_audience'] = st.selectbox(
            "Target Audience",
            options=['lay person', 'college students', 'experts'],
            index=['lay person', 'college students', 'experts'].index(
                st.session_state.podcast_settings['target_audience']
            )
        )
        
        st.session_state.podcast_settings['duration_mins'] = st.slider(
            "Duration (minutes)",
            min_value=5,
            max_value=30,
            value=st.session_state.podcast_settings['duration_mins'],
            step=5
        )
    
    if st.button("Generate Podcast"):
        with st.spinner("Generating podcast... This may take a few minutes."):
            try:
                # Generate the podcast
                podcast_path = create_podcast_audio(
                    n_participants=st.session_state.podcast_settings['n_participants'],
                    target_audience=st.session_state.podcast_settings['target_audience'],
                    duration_mins=st.session_state.podcast_settings['duration_mins']
                )
                
                # Store the path in session state
                st.session_state.podcast_settings['last_podcast'] = podcast_path
                st.success("Podcast generated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error generating podcast: {str(e)}")
    
    # Display audio player if podcast exists
    if st.session_state.podcast_settings['last_podcast']:
        podcast_path = st.session_state.podcast_settings['last_podcast']
        if os.path.exists(podcast_path):
            st.subheader("Generated Podcast")
            with open(podcast_path, 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/mp3')

def save_notes_to_markdown():
    """Save all notes to a markdown file and return the file path."""
    if not st.session_state.notes:
        return None
        
    # Create notes directory if it doesn't exist
    notes_dir = Path(".cache/notes")
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
                with st.spinner("Saving notes and indexing into vector database..."):
                    # Save notes to markdown file
                    notes_file = save_notes_to_markdown()
                    if notes_file and notes_file not in st.session_state.sources:
                        # Index the notes in vector database
                        vectordb = VectorDBIngestion()
                        vectordb.process_document(notes_file, source_id=Path(notes_file).name)
                        
                        # Add to sources
                        st.session_state.sources.append(notes_file)
                        st.success(f"Notes saved and indexed successfully")
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
