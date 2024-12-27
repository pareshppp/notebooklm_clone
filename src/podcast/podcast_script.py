from typing import List
from pathlib import Path
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime
import json
import random
from src.utils.utils import read_source_files

SYSTEM_PROMPT_PODCAST_SCRIPT = """
You are an expert podcast scriptwriter specializing in turning complex information into engaging audio content. Your task is to generate a compelling podcast script based on the provided documents, tailored to the specified audience, number of participants, and duration.

**Input Information:**

*   **Documents:**  [Insert the actual document content here, either as a plain text block or a reference to the location of the documents].
*   **Number of Participants:** [Number between 1-3]
*   **Target Audience:** [lay person, college students, or experts]
*   **Duration:** [Number in minutes, e.g., 15] minutes

**Instructions:**

1.  **Analyze the Documents:** Carefully read and understand the core concepts, arguments, and information presented in the documents.
2.  **Define the Podcast Structure:** Design a clear podcast structure, including an introduction, a main discussion body, and a conclusion. Ensure a smooth flow of conversation and natural transitions. Consider incorporating elements like:
    *   An engaging opening to hook the listener.
    *   Clear explanations of key terms and concepts (especially for lay person and college student audiences).
    *   Questions that guide the discussion and probe deeper into the topic.
    *   Real-world examples and relevant anecdotes to make the information relatable.
    *   A summary or takeaway at the end.
3.  **Assign Roles:**  Create speaking roles for each participant and determine a role for the Host.
4.  **Speaker voice assignment**: Assign a google tts voice for each participant in the script. Try to have distinct voices for each participant, with gender and voice tone appropriate for the role.
5.  **Write the Script:** Generate a detailed script for each speaker using a conversational tone. Consider how the different speakers can play off each other to create a dynamic discussion.
6.  **Adhere to the Duration:** Ensure the final script is suitable for a podcast of approximately the specified duration.  
7.  **JSON Output:** Generate the final output as a JSON list of speaker scripts, following the exact format below:

```json
{{
    "script":
    [
        {{
            "speaker": {{
                "speaker_name": "Host",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
            "speaker_script": "The podcast script for the host"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant1",
                "speaker_gender": "female",
                "speaker_voice": "en-US-Journey-F"
            }},
            "speaker_script": "The podcast script for Participant1"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant2",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
            "speaker_script": "The podcast script for Participant2"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant3",
                "speaker_gender": "female",
                "speaker_voice": "en-US-Journey-O"
            }},
            "speaker_script": "The podcast script for Participant3"
        }}
   ]
}}
```

**Example:**

If you are given the following input:

*   **Documents:** [Assume the document content is about the history of the internet]
*   **Number of Participants:** 3
*   **Target Audience:** Lay person
*   **Duration:** 15 minutes

The output should look something like this:

```json
{{
    "script": [
        {{
            "speaker": {{
                "speaker_name": "Host",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
        "speaker_script": "Welcome to 'Tech Time'! Today, we're diving into the fascinating history of the internet. With me are two experts, [Participant 1 name] and [Participant 2 name]. Thanks for joining me!"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant1",
                "speaker_gender": "female",
                "speaker_voice": "en-US-Journey-F"
            }},
            "speaker_script": "It's great to be here, thanks for having me!"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant2",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
            "speaker_script": "Absolutely, excited to share some insights."
        }},
        {{
            "speaker": {{
                "speaker_name": "Host",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
            "speaker_script": "Great! So, to start, when did this 'internet' thing really get going? Many people assume it's just a few decades old, but that's not really true, is it?"
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant1",
                "speaker_gender": "female",
                "speaker_voice": "en-US-Journey-O"
            }},
            "speaker_script": "That's right. While the World Wide Web as we know it is relatively recent, the roots go back much further, to the 1960s with projects like ARPANET, sponsored by the U.S. Department of Defense..."
        }},
        {{
            "speaker": {{
                "speaker_name": "Participant2",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
            "speaker_script": "And a critical point is that it wasn't designed for the mass consumer initially. It was primarily focused on connecting research institutions and government agencies...."
        }},
        {{
        "speaker": {{
                "speaker_name": "Host",
                "speaker_gender": "male",
                "speaker_voice": "en-US-Journey-D"
            }},
        "speaker_script": "That's fascinating, I always wondered how it all started. ... [The script continues with further discussion points, questions, and conclusions following the same format]"
        }}
    ]
}}
```
"""


class SpeakerInfo(BaseModel):
    speaker_name: str = Field(description="The name of the speaker. Can be one of Host, Participant1, Participant2, Participant3, or a name from the source documents.")
    speaker_gender: Literal["male", "female"] = Field(description="The gender of the speaker.")
    speaker_voice: str = Field(description="The google tts voice to use for this speaker. Use one of the journey voices.")

class SpeakerScript(BaseModel):
    speaker: SpeakerInfo = Field(description="Information about the speaker.")
    speaker_script: str = Field(description="The podcast script for this speaker.")

class PodcastScript(BaseModel):
    script: List[SpeakerScript] = Field(description="A list of speaker scripts forming the complete podcast script.")


def create_podcast_script_chain():
    """Create a LangChain LCEL chain for generating podcast scripts."""
    
    # Initialize the Gemini model
    llm = ChatVertexAI(
        model_name="gemini-1.5-flash-002",
        max_output_tokens=8096,
        temperature=0.7,
    )
    
    # Create the podcast script generation prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_PODCAST_SCRIPT),
        ("human", """
            Document Content: {source_content} \n\n\n
            Number of Participants: {number_of_participants} \n\n
            Target Audience: {target_audience} \n\n
            Duration: {duration} \n\n
        """),
    ])
    
    # Build the LCEL chain
    chain = prompt | llm | PydanticOutputParser(pydantic_object=PodcastScript)
    
    return chain

def fix_google_tts_voices_journey(script: PodcastScript) -> PodcastScript:
    gender_voice_map = {
        "male": ["en-US-Journey-D", "en-GB-Journey-D"],
        "female": ["en-US-Journey-F", "en-US-Journey-O", "en-GB-Journey-F", "en-GB-Journey-O"]
    }

    # replace voices for males with any of the male voices randomly and same for females
    for speaker in script.script:
        if speaker.speaker.speaker_gender in gender_voice_map:
            speaker.speaker.speaker_voice = gender_voice_map[speaker.speaker.speaker_gender][0]

    return script

def generate_podcast_script(
    n_participants: int, 
    target_audience: str, 
    duration_mins: int = 20, 
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S"), 
    scripts_dir: Path = Path(".cache/generated_podcasts/scripts")
) -> str:
    """
    Generate a podcast script from the source documents.
    
    Returns:
        str: Generated podcast script
    """
    if n_participants < 1 or n_participants > 3:
        raise ValueError("Number of participants must be between 1 and 3.")

    # Read source documents
    source_content = read_source_files()
    if not source_content:
        return "No source documents found. Please add some documents first."
        
    # Create and run the chain
    chain = create_podcast_script_chain()
    script = chain.invoke({
        "source_content": source_content,
        "number_of_participants": n_participants,
        "target_audience": target_audience,
        "duration": duration_mins
    })

    script_file = scripts_dir / f"podcast_script_{timestamp}.json"
    with open(script_file, "w") as f:
        json.dump(script.dict(), f, indent=2)
    
    return script, str(script_file)
