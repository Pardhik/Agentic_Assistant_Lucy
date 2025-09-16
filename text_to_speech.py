import os
import elevenlabs
from elevenlabs.client import ElevenLabs
import subprocess
import platform
from pydub import AudioSegment
from gtts import gTTS


ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def play_audio(filepath):
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', filepath])
        elif os_name == "Windows":  # Windows
            # Convert MP3 to WAV for SoundPlayer
            if filepath.endswith(".mp3"):
                wav_file = filepath.replace(".mp3", ".wav")
                AudioSegment.from_mp3(filepath).export(wav_file, format="wav")
                filepath = wav_file
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{filepath}").PlaySync();'])
        elif os_name == "Linux":  # Linux
            if filepath.endswith(".mp3"):
                subprocess.run(['mpg123', filepath])  # Requires mpg123 installed
            else:
                subprocess.run(['aplay', filepath])
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")


def text_to_speech_with_elevenlabs(input_text, output_filepath):
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio = client.text_to_speech.convert(
        text=input_text,
        voice_id="ZF6FPAbjXT4488VcRRnw",  # Your voice ID
        model_id="eleven_multilingual_v2",
        output_format="mp3_22050_32"
    )
    elevenlabs.save(audio, output_filepath)
    play_audio(output_filepath)


def text_to_speech_with_gtts(input_text, output_filepath):
    tts = gTTS(text=input_text, lang="en", slow=False)
    tts.save(output_filepath)
    play_audio(output_filepath)

if __name__ == "__main__":
    input_text = "Hi, I am doing fine, how are you? This is a test for AI with Pardhik"
    output_filepath = "test_text_to_speech.mp3"

    #Use ElevenLabs
    text_to_speech_with_elevenlabs(input_text, output_filepath)

    #Use gTTS (uncomment to test)
    text_to_speech_with_gtts(input_text, output_filepath)

