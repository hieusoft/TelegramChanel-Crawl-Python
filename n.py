from config.config import Config  
from openai import OpenAI


class Translator:
    def __init__(self):
        config = Config()
        self.target_lang = config.get("translator.target_lang", "en")
        api_key = config.get("openai.api_key")
        base_url = config.get("openai.base_url", "https://openrouter.ai/api/v1")

        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def translate_text(self, text, target_language=None):
        target_language = target_language or self.target_lang

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional translator. "
                        f"Translate everything into {target_language}. "
                        "Keep emojis, punctuation, newlines, and spacing exactly as in the original text. "
                        "Do NOT modify or remove any symbols, markdown, or formatting."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )

        result = response.choices[0].message.content.strip()

        bad_tokens = [
            "<｜begin▁of▁sentence｜>",
            "<｜end▁of▁sentence｜>",
            "<|begin_of_sentence|>",
            "<|end_of_sentence|>",
        ]
        for token in bad_tokens:
            result = result.replace(token, "")

        return result.strip()


if __name__ == "__main__":
    translator = Translator()
    text = "Hellooooo"
    translated = translator.translate_text(text)
    print("✅ Bản dịch:", translated)
