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
RECORD_SECONDS = 5

# Global variables for language settings
my_language = 'en'  # The language you want translations in (English)

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
        VIRTUAL_CABLE_INDEX = 8  # CABLE Input (VB-Audio Virtual Cable)
        
        # Convert MP3 to AudioSegment
        audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_content))
        
        # Force specific audio properties
        audio_segment = audio_segment.set_channels(2)  # Stereo
        audio_segment = audio_segment.set_frame_rate(44100)
        audio_segment = audio_segment.set_sample_width(2)  # 16-bit
        
        # Create stream with explicit format
        stream = p.open(format=pyaudio.paInt16,
                       channels=2,
                       rate=44100,
                       output=True,
                       output_device_index=VIRTUAL_CABLE_INDEX,
                       frames_per_buffer=1024)
        
        # Convert to raw data and play
        data = audio_segment.raw_data
        
        # Write in chunks to avoid buffer issues
        chunk_size = 1024 * 2  # 2 bytes per sample * 1024
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            stream.write(chunk)
        
        # Clean up
        time.sleep(0.2)  # Small delay to ensure audio completes
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        print(f"Audio playback error: {e}")

def continuous_translation():
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    
    def detect_with_confidence(text):
        try:
            common_langs = ['hi', 'en', 'mr', 'gu', 'pa', 'ta', 'te', 'kn', 'ml']
            detected = detect(text)
            return detected if detected in common_langs else 'hi'
        except:
            return 'en'
    
    translator = GoogleTranslator(source='auto', target=my_language)
    last_language = None
    
    # Create microphone instance for ambient noise adjustment
    print("Adjusting for ambient noise. Please wait...")
    mic = spr.Microphone()
    with mic as source:
        recog1.adjust_for_ambient_noise(source, duration=1)
    print("Ambient noise adjustment complete.")
    
    while True:
        try:
            audio_data = capture_audio()
            speech = recognize_speech(audio_data)

            if speech:
                try:
                    detected_lang = detect_with_confidence(speech)
                    print(f"Recognized speech ({detected_lang}): {speech}")

                    if last_language is None:
                        if detected_lang != 'en':
                            last_language = detected_lang
                        else:
                            print("Waiting for non-English speaker to set target language...")
                            continue

                    # Set up translation direction
                    if detected_lang == 'en':
                        translator = GoogleTranslator(source='en', target=last_language)
                    else:
                        translator = GoogleTranslator(source=detected_lang, target='en')

                    translation = translator.translate(speech)
                    target_language = 'en' if detected_lang != 'en' else last_language
                    print(f"Translated to {target_language}: {translation}")

                    # Synthesize speech in target language
                    input_text = texttospeech.SynthesisInput(text=translation)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code=target_language,
                        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                    )
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3
                    )
                    response = tts_client.synthesize_speech(
                        input=input_text,
                        voice=voice,
                        audio_config=audio_config
                    )

                    # Play the translated audio to Zoom
                    play_audio_to_zoom(response.audio_content)

                except Exception as e:
                    print(f"Translation error: {e}")

            if speech and 'stop translation' in speech:
                print("Stopping translation service.")
                break

        except KeyboardInterrupt:
            print("\nStopping translation service...")
            break

if __name__ == "__main__":
    print("Starting translation service...")
    print("First non-English speaker will set the target language.")
    print("Then translations will go back and forth between English and that language.")
    continuous_translation()