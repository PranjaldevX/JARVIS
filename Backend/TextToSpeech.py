import pygame  # For handling audio playback
import random  # For selecting random responses
import asyncio  # For asynchronous operations
import edge_tts  # For text-to-speech functionality
import os  # For handling file paths
from dotenv import dotenv_values  # For reading environment variables
import time  # For handling time operations

# Load environment variables from a .env file
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-CA-LiamNeural")  # Default to a voice if not in .env

# Define the path for saving the speech file
file_path = os.path.join("Data", "speech.mp3")

# Asynchronous function to convert text to an audio file
async def TextToAudioFile(text) -> None:
    file_path = r"Data\speech.mp3"

    if os.path.exists(file_path):
        pygame.mixer.quit()  # Stop pygame mixer before removing file
        time.sleep(1)  # Ensure the file is released
        os.remove(file_path)

    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)


# Function to play the generated speech file
def play_audio(func=lambda _: None):
    """Plays the saved speech file and handles interruptions."""
    try:
        pygame.mixer.init()
    except pygame.error as e:
        print(f"Pygame mixer initialization failed: {e}")
        return False

    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        timeout = 100  # Max iterations to prevent infinite loops (~10 sec)
        while pygame.mixer.music.get_busy() and timeout > 0:
            if func(False) is False:
                break
            pygame.time.Clock().tick(10)  # Limit to 10 FPS
            timeout -= 1

        return True
    except Exception as e:
        print(f"Error in play_audio: {e}")
    finally:
        func(False)
        pygame.mixer.music.stop()
        pygame.mixer.quit()

# Function to manage Text-to-Speech (TTS)
def TTS(Text, func=lambda _: None):  # Changed from lambda: None
    """Converts text to speech and plays it."""
    try:
        asyncio.run(TextToAudioFile(Text))  # Ensure proper async execution
        play_audio(func)
    except Exception as e:
        print(f"Error in TTS: {e}")

# Function to manage TTS with additional responses for long text
def TextToSpeech(Text, func=lambda _: None):  # Changed from lambda: None
    """Splits long text and plays only the first part, printing the rest."""
    Data = Text.split(".")  # Split text into sentences

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
    ]

    # If text is long, read part of it and show the rest in the chat
    if len(Data) > 4 and len(Text) > 250:
        short_text = ". ".join(Data[:2]) + ". " + random.choice(responses)
        TTS(short_text, func)
    else:
        TTS(Text, func)

# Main execution loop
if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text: "))