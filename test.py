import speech_recognition as sr
from googletrans import Translator
from google.cloud import texttospeech
import pyaudio
import wave
import numpy as np
import threading
import queue
import os

# Set up Google Cloud Text-to-Speech client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Dhruv\Desktop\translator\sa_translator.json"
tts_client = texttospeech.TextToSpeechClient()

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono audio
RATE = 44100
RECORD_SECONDS = 5

# Global variables
translator = Translator()
recognizer = sr.Recognizer()

def capture_audio():
    p = pyaudio.PyAudio()
    
    # List available input devices
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

    # Let user choose input device
    device_id = int(input("Enter the number of the input device you want to use: "))
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_id,
                    frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    return b''.join(frames)

def process_audio(audio_data):
    try:
        audio = sr.AudioData(audio_data, RATE, 2)  # 2 bytes per sample for int16
        text = recognizer.recognize_google(audio)
        print(f"Recognized: {text}")
        
        # Detect language and translate if necessary
        detected_lang = translator.detect(text).lang
        if detected_lang != 'en':  # Assuming English is your language
            translation = translator.translate(text, dest='en')
            print(f"Translated: {translation.text}")
            
            # Text-to-speech
            input_text = texttospeech.SynthesisInput(text=translation.text)
            voice = texttospeech.VoiceSelectionParams(
                language_code='en-US',
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )
            response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
            
            # Play synthesized speech (you need to implement this part)
            play_audio(response.audio_content)
    except sr.UnknownValueError:
        print("Could not understand audio")
    except Exception as e:
        print(f"Error: {e}")

def play_audio(audio_data):
    # Implement this function to play audio through your virtual audio device
    print("Playing translated audio")
    # This is where you'd send the audio to a virtual audio device that Zoom can use as input

if __name__ == "__main__":
    print("Starting translation service...")
    while True:
        audio_data = capture_audio()
        process_audio(audio_data)
        
        if input("Continue? (y/n): ").lower() != 'y':
            break

    print("Translation service stopped.")