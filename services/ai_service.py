import google.generativeai as genai
import os
import json
import re

class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("❌ GOOGLE_API_KEY 沒設定")

        genai.configure(api_key=api_key)

        try:
            self.model = genai.GenerativeModel("gemini-1.5-flash-latest")
        except:
            self.model = genai.GenerativeModel("gemini-1.5-pro-latest")

    def clean_json(self, text):
        text = re.sub(r"```json|```", "", text)
        return text.strip()

    def get_word_info(self, word):
        prompt = f"""
        請分析單字：{word}

        並用 JSON 回傳：
        {{
            "word": "",
            "phonetic": "",
            "meaning": "",
            "example_sentence": "",
            "sentence_translation": ""
        }}

        規則：
        - 僅回傳 JSON
        - 不要 markdown
        - 用繁體中文
        """

        response = self.model.generate_content(prompt)
        text = response.text

        try:
            clean_text = self.clean_json(text)
            data = json.loads(clean_text)

            data.setdefault("word", word)
            data.setdefault("phonetic", "")
            data.setdefault("meaning", "")
            data.setdefault("example_sentence", "")
            data.setdefault("sentence_translation", "")

            return data

        except:
            return {
                "word": word,
                "phonetic": "",
                "meaning": text,
                "example_sentence": "",
                "sentence_translation": ""
            }
