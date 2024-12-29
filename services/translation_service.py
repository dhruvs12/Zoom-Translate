import asyncio
import queue
from threading import Thread
import speech_recognition as spr
from utils.audio_device import VirtualAudioDevice
from services.audio_service import AudioService
from services.language_service import LanguageService
from utils.audio_controller import AudioController

class TranslationService:
    def __init__(self):
        self.audio_service = AudioService()
        self.language_service = LanguageService()
        self.virtual_device = VirtualAudioDevice()
        self.output_device_index = self.virtual_device.get_default_virtual_device()
        self.audio_controller = AudioController()
        
        # Initialize queues
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        self.playback_queue = queue.Queue()
        
        self.is_running = False
        
        if self.output_device_index is None:
            raise ValueError("No virtual audio device found. Please install a virtual audio cable.")

    def start_workers(self):
        self.is_running = True
        
        # Start worker threads
        Thread(target=self._audio_capture_worker, daemon=True).start()
        Thread(target=self._speech_recognition_worker, daemon=True).start()
        Thread(target=self._translation_worker, daemon=True).start()
        Thread(target=self._audio_playback_worker, daemon=True).start()

    def stop_workers(self):
        self.is_running = False

    def _audio_capture_worker(self):
        while self.is_running:
            try:
                audio_data = self.audio_service.capture_audio()
                self.audio_queue.put(audio_data)
            except Exception as e:
                print(f"Error capturing audio: {e}")

    def _speech_recognition_worker(self):
        while self.is_running:
            try:
                audio_data = self.audio_queue.get(timeout=1)
                text = self.audio_service.recognize_speech(audio_data)
                if text:
                    self.text_queue.put(text)
                self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error recognizing speech: {e}")

    def _translation_worker(self):
        last_language = None
        
        while self.is_running:
            try:
                text = self.text_queue.get(timeout=1)
                
                if 'stop translation' in text.lower():
                    self.stop_workers()
                    continue

                detected_lang = self.language_service.detect_language(text)
                print(f"Recognized ({detected_lang}): {text}")

                if last_language is None and detected_lang != 'en':
                    last_language = detected_lang
                elif last_language is None:
                    self.text_queue.task_done()
                    continue

                source_lang = 'en' if detected_lang == 'en' else detected_lang
                target_lang = last_language if detected_lang == 'en' else 'en'
                
                translation = self.language_service.translate(text, source_lang, target_lang)
                voice_config = self.language_service.get_voice_config(target_lang)
                
                self.translation_queue.put((translation, voice_config))
                self.text_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in translation: {e}")

    def _audio_playback_worker(self):
        while self.is_running:
            try:
                translation, voice_config = self.translation_queue.get(timeout=1)
                
                # Mute the microphone before playing translation
                self.audio_controller.mute_mic()
                
                # Synthesize and play the translation
                response = self.language_service.synthesize_speech(translation, voice_config)
                self.audio_service.play_audio(response.audio_content, self.output_device_index)
                
                # Unmute the microphone after playing translation
                self.audio_controller.unmute_mic()
                
                self.translation_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio playback: {e}")
                self.audio_controller.unmute_mic()  # Ensure mic is unmuted in case of error

    async def run(self):
        print("Adjusting for ambient noise. Please wait...")
        mic = spr.Microphone()
        with mic as source:
            self.audio_service.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Ambient noise adjustment complete.")
        
        self.start_workers()
        
        try:
            # Keep the main thread alive
            while self.is_running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping translation service...")
        finally:
            self.stop_workers() 