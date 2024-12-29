from google.cloud import texttospeech
from langdetect import detect, DetectorFactory
from iso639 import languages
from functools import lru_cache
from deep_translator import GoogleTranslator

# Set seed for consistent language detection
DetectorFactory.seed = 0

class LanguageService:
    def __init__(self):
        self.tts_client = texttospeech.TextToSpeechClient()

    @lru_cache(maxsize=100)
    def translate(self, text, source_lang, target_lang):
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)

    def detect_language(self, text):
        try:
            return detect(text)
        except:
            return 'en'

    def get_voice_config(self, language_code):
        try:
            lang_obj = languages.get(part1=language_code)
            if language_code in ['zh', 'yue']:
                bcp47_code = f'{language_code}-CN'
            else:
                bcp47_code = f'{language_code}-{lang_obj.name[:2].upper()}'
            
            return texttospeech.VoiceSelectionParams(
                language_code=bcp47_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
        except Exception as e:
            print(f"Warning: Failed to create voice config for {language_code}. Using English fallback.")
            return texttospeech.VoiceSelectionParams(
                language_code='en-US',
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )

    def synthesize_speech(self, text, voice_config):
        input_text = texttospeech.SynthesisInput(text=text)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.2
        )
        
        return self.tts_client.synthesize_speech(
            input=input_text,
            voice=voice_config,
            audio_config=audio_config
        ) 