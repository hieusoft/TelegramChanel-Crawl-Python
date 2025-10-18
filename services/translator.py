from googletrans import Translator as GoogleTranslator
from config.config import Config  

class Translator:
    def __init__(self, target_lang=None):
        self.translator = GoogleTranslator()
        config = Config()
        self.target_lang = target_lang or config.get("translator.target_lang", "en")

    def translate(self, text):
        try:
            if not text:
                return ""

            lines = text.split('\n')
            translated_lines = []

            for line in lines:
                if not line.strip():
                    translated_lines.append("")  # Giữ dòng trống
                    continue

                try:
                    translated_text = self.translator.translate(line, dest=self.target_lang).text
                    translated_lines.append(str(translated_text or ""))  # Ép chuỗi, tránh None
                except Exception as inner_e:
                    print(f"[Translator Error - line skipped] {inner_e}")
                    translated_lines.append(line)  # Giữ nguyên dòng nếu dịch lỗi

            return "\n".join(translated_lines)

        except Exception as e:
            print(f"[Translator Error] {e}")
            return text
