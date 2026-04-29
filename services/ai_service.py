import anthropic
import json

class AIService:
    def __init__(self, api_key):
        # 初始化 Claude 客戶端
        self.client = anthropic.Anthropic(api_key=api_key)

    def get_word_details(self, word):
        system_prompt = "You are a language teacher. Return ONLY a JSON object."
        user_content = f"""
        請分析單字 '{word}'，回傳 JSON 格式如下：
        {{
            "word": "{word}",
            "phonetic": "音標",
            "translation": "中文意思",
            "example": "一句實用的法文例句",
            "example_cn": "例句的中文翻譯"
        }}
        """
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            # Claude 回傳的是字串，需要解析
            return json.loads(message.content[0].text)
        except Exception as e:
            return {"word": word, "phonetic": "N/A", "translation": f"錯誤: {str(e)}", "example": "", "example_cn": ""}

    def correct_memo(self, user_sentence):
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=500,
                messages=[{"role": "user", "content": f"我是法文學習者，請修正這句並給建議：'{user_sentence}'"}]
            )
            return message.content[0].text
        except Exception as e:
            return f"校正失敗: {str(e)}"
