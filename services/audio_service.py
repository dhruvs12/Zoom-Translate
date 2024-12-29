import pyaudio
import speech_recognition as spr
from pydub import AudioSegment
import io
from config.settings import *
import numpy as np

class AudioService:
    def __init__(self):
        self.recognizer = spr.Recognizer()
        self.recognizer.energy_threshold = ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.chunk_buffer = []
        self.silence_threshold = 10  # Number of silent chunks before processing

    def capture_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)

        # Capture audio until silence is detected
        frames = []
        silent_chunks = 0
        
        while silent_chunks < self.silence_threshold:
            data = stream.read(CHUNK)
            frames.append(data)
            
            # Check for silence
            if self._is_silent(data):
                silent_chunks += 1
            else:
                silent_chunks = 0

        stream.stop_stream()
        stream.close()
        p.terminate()
        return b''.join(frames)

    def _is_silent(self, audio_data):
        # Convert bytes to numpy array
        data = np.frombuffer(audio_data, dtype=np.int16)
        # Calculate RMS of the audio chunk
        rms = np.sqrt(np.mean(np.square(data)))
        return rms < self.recognizer.energy_threshold

    def recognize_speech(self, audio_data):
        try:
            audio = spr.AudioData(audio_data, RATE, 2)
            recognized_text = self.recognizer.recognize_google(audio)
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

    def play_audio(self, audio_content, output_device_index):
        try:
            p = pyaudio.PyAudio()
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_content))
            audio_segment = audio_segment.set_channels(2).set_frame_rate(44100).set_sample_width(2)
            
            stream = p.open(format=pyaudio.paInt16,
                          channels=2,
                          rate=44100,
                          output=True,
                          output_device_index=output_device_index,
                          frames_per_buffer=BUFFER_SIZE)
            
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