import os
import json
import google.generativeai as genai

class AIService:
    def __init__(self):
        # 1. 確保環境變數存在
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("AIService: 未偵測到 GOOGLE_API_KEY 環境變數")
        
        # 2. 顯式配置 Google GenAI SDK
        genai.configure(api_key=api_key)
        
        # 3. 初始化清單中支援的模型
        self.model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
    def get_word_analysis(self, word):
        system_prompt = """
        你是一位專業語言學教授。分析單字並回傳 JSON 格式：
        {
            "word": "string",
            "lang_code": "en/fr",
            "phonetic": "IPA",
            "meaning": "繁體中文解釋",
            "example_sentence": "例句",
            "sentence_translation": "例句翻譯"
        }
        """
        user_prompt = f"請分析單字：{word}"
        
        response = self.model.generate_content([system_prompt, user_prompt])
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return None
