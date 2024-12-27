import os
import json
from pathlib import Path
from typing import List
from google.cloud import texttospeech
from pydub import AudioSegment
from datetime import datetime

from src.podcast.podcast_script import generate_podcast_script

class PodcastSpeechSynthesizer:
    def __init__(self, output_dir: str = ".cache/generated_podcasts"):
        """
        Initialize the podcast speech synthesizer.
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.client = texttospeech.TextToSpeechClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for scripts and audio
        self.scripts_dir = self.output_dir / "scripts"
        self.audio_dir = self.output_dir / "audio"
        self.scripts_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        
    def synthesize_speech(self, text: str, voice_name: str, output_file: str) -> str:
        """
        Synthesize speech for a single piece of text.
        
        Args:
            text: Text to synthesize
            voice_name: Name of the voice to use
            output_file: Path to save the audio file
            
        Returns:
            str: Path to the generated audio file
        """
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        # Perform the text-to-speech request
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Write the response to the output file
        output_path = self.audio_dir / output_file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            
        return str(output_path)

    def combine_audio_files(self, audio_files: List[str], output_file: str) -> str:
        """
        Combine multiple audio files into a single podcast.
        
        Args:
            audio_files: List of paths to audio files
            output_file: Name of the output file
            
        Returns:
            str: Path to the combined audio file
        """
        combined = AudioSegment.empty()
        
        # Add small pause between segments
        pause = AudioSegment.silent(duration=500)  # 500ms pause
        
        for audio_file in audio_files:
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment + pause
            
        # Save the combined audio
        output_path = self.audio_dir / output_file
        combined.export(output_path, format="mp3")
        
        return str(output_path)

def create_podcast_audio(
    n_participants: int,
    target_audience: str,
    duration_mins: int = 20,
    output_filename: str = "podcast.mp3"
) -> tuple[str, str]:
    """
    Generate a complete podcast audio file from source documents.
    
    Args:
        n_participants: Number of participants (1-3)
        target_audience: Target audience type
        duration_mins: Duration in minutes
        output_filename: Name of the output audio file
        
    Returns:
        tuple[str, str]: Paths to the generated script file and podcast audio file
    """
    # Generate timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize speech synthesizer
    synthesizer = PodcastSpeechSynthesizer()

    # Generate the podcast script
    script, _ = generate_podcast_script(
        n_participants=n_participants,
        target_audience=target_audience,
        duration_mins=duration_mins,
        timestamp=timestamp,
        scripts_dir=synthesizer.scripts_dir
    )
    
    # Generate audio for each script segment
    audio_files = []
    for i, segment in enumerate(script.script):
        # Generate unique filename for this segment
        segment_filename = f"segment_{timestamp}_{i}_{segment.speaker.speaker_name}.mp3"
        
        # Synthesize speech for this segment
        audio_file = synthesizer.synthesize_speech(
            text=segment.speaker_script,
            voice_name=segment.speaker.speaker_voice,
            output_file=segment_filename
        )
        audio_files.append(audio_file)
    
    # Add timestamp to final output filename
    output_filename = f"podcast_{timestamp}.mp3"
    
    # Combine all audio segments into final podcast
    final_audio = synthesizer.combine_audio_files(
        audio_files=audio_files,
        output_file=output_filename
    )
    
    return final_audio