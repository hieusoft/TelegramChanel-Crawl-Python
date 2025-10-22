
# translator.py
from deep_translator import GoogleTranslator
import logging

Logger = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        from config.config import Config
        config = Config()
        self.target_lang = config.get("translator.target_lang", "en")
        self.lang_map = {
            "vi": "vi",
            "en": "en",
            "zh": "zh-CN",
            "ja": "ja",
            "ko": "ko"
        }
        
        self.enabled = True
        Logger.info(f"✅ Google Translator initialized (target: {self.target_lang})")

    def translate_text(self, text, target_language=None):
   
        if not text or not text.strip():
            return text
        
        target = target_language or self.target_lang
        target_code = self.lang_map.get(target, target)
        
        try:
            
            translator = GoogleTranslator(source='auto', target=target_code)
            
      
            if len(text) > 4500:
             
                chunks = self._split_text(text, 4500)
                translated_chunks = []
                for chunk in chunks:
                    translated_chunks.append(translator.translate(chunk))
                result = " ".join(translated_chunks)
            else:
                result = translator.translate(text)
            
            Logger.debug(f"✅ Translated: {text[:30]}... → {result[:30]}...")
            return result
            
        except Exception as e:
            Logger.warning(f"⚠️ Translation failed: {e}, returning original")
            return text 
    
    def _split_text(self, text, max_length):
 
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
