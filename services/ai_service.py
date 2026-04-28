import json
from openai import OpenAI

class AIService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_word_details(self, word):
        prompt = f"""
        請分析單字 '{word}'，回傳 JSON 格式：
        {{
            "word": "單字本身",
            "phonetic": "音標",
            "translation": "中文意思",
            "example": "一句實用的法文例句",
            "example_cn": "例句的中文翻譯"
        }}
        """
        response = self.client.chat.completions.create(
            model="gpt-4o", # 也可以換成 claude-3-5-sonnet
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)

    def correct_memo(self, user_sentence):
        prompt = f"我是法文學習者，請幫我修正這句造句並給予簡短建議：'{user_sentence}'"
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
