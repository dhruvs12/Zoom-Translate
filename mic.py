import os
import speech_recognition as spr
from deep_translator import GoogleTranslator
from google.cloud import texttospeech
import pyaudio
import wave
import numpy as np
from pydub import AudioSegment
import io
import time
import asyncio
from functools import lru_cache

# Set up Google Cloud Text-to-Speech client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Dhruv\Desktop\translator\sa_translator.json"
tts_client = texttospeech.TextToSpeechClient()

# Create Recogniser() class object
recog1 = spr.Recognizer()
recog1.energy_threshold = 300  # Adjust this value between 100-4000
recog1.dynamic_energy_threshold = True
recog1.pause_threshold = 0.8

# Audio stream settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100
RECORD_SECONDS = 1  # Reduced from 5 to 1 second

# Global variables for language settings
my_language = 'en'  # The language you want translations in (English)

# Cache for translations
@lru_cache(maxsize=100)
def cached_translate(text, source_lang, target_lang):
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    return translator.translate(text)

# Preload voice configurations
VOICE_CONFIGS = {
    'en': texttospeech.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    ),
    'hi': texttospeech.VoiceSelectionParams(
        language_code='hi-IN',
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    # Add more languages as needed
}

def capture_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("Capturing audio...")
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Audio capture complete.")
    stream.stop_stream()
    stream.close() 
    p.terminate()
    return b''.join(frames)

def recognize_speech(audio_data):
    try:
        audio = spr.AudioData(audio_data, RATE, 2)  # 2 bytes per sample for int16
        recognized_text = recog1.recognize_google(audio)
        return recognized_text.lower()
    except spr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
        return None
    except spr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def play_audio_to_zoom(audio_content):
    try:
        p = pyaudio.PyAudio()
        VIRTUAL_CABLE_INDEX = 8
        
        audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_content))
        audio_segment = audio_segment.set_channels(2).set_frame_rate(44100).set_sample_width(2)
        
        # Increased buffer size for smoother playback
        BUFFER_SIZE = 2048
        
        stream = p.open(format=pyaudio.paInt16,
                       channels=2,
                       rate=44100,
                       output=True,
                       output_device_index=VIRTUAL_CABLE_INDEX,
                       frames_per_buffer=BUFFER_SIZE)
        
        # Process in larger chunks for efficiency
        chunk_size = BUFFER_SIZE * 4
        data = audio_segment.raw_data
        
        for i in range(0, len(data), chunk_size):
            if not stream.is_active():
                break
            chunk = data[i:i + chunk_size]
            stream.write(chunk)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        print(f"Audio playback error: {e}")

async def async_translation_pipeline():
    last_language = None
    
    print("Adjusting for ambient noise. Please wait...")
    mic = spr.Microphone()
    with mic as source:
        recog1.adjust_for_ambient_noise(source, duration=1)
    print("Ambient noise adjustment complete.")
    
    while True:
        try:
            audio_data = await asyncio.to_thread(capture_audio)
            speech = await asyncio.to_thread(recognize_speech, audio_data)

            if speech:
                if 'stop translation' in speech:
                    print("Stopping translation service.")
                    break
                    
                detected_lang = await asyncio.to_thread(detect_with_confidence, speech)
                print(f"Recognized: {speech}")

                if last_language is None and detected_lang != 'en':
                    last_language = detected_lang
                elif last_language is None:
                    continue

                source_lang = 'en' if detected_lang == 'en' else detected_lang
                target_lang = last_language if detected_lang == 'en' else 'en'
                
                # Use cached translation
                translation = await asyncio.to_thread(
                    cached_translate, speech, source_lang, target_lang
                )

                # Use preloaded voice config
                input_text = texttospeech.SynthesisInput(text=translation)
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.2
                )
                
                response = await asyncio.to_thread(
                    tts_client.synthesize_speech,
                    input=input_text,
                    voice=VOICE_CONFIGS[target_lang],
                    audio_config=audio_config
                )

                await asyncio.to_thread(play_audio_to_zoom, response.audio_content)

        except KeyboardInterrupt:
            print("\nStopping translation service...")
            break
        except Exception as e:
            print(f"Error in translation pipeline: {e}")
            continue

# Update main execution
if __name__ == "__main__":
    print("Starting translation service...")
    print("First non-English speaker will set the target language.")
    print("Then translations will go back and forth between English and that language.")
    asyncio.run(async_translation_pipeline())