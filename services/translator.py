from googletrans import Translator as GoogleTranslator
from config.config import Config  

class Translator:
    def __init__(self, target_lang=None):
        self.translator = GoogleTranslator()
        config = Config()
        self.target_lang = target_lang or config.get("translator.target_lang", "en")

    def translate(self, text):
        try:
            translated = self.translator.translate(text, dest=self.target_lang)
            return translated.text
        except Exception as e:
            print(f"[Translator Error] {e}")
            return text
