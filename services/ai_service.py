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
        
        # 3. 初始化清單中支援的模型 (並強制回傳 JSON)
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
        
        try:
            response = self.model.generate_content([system_prompt, user_prompt])
            return json.loads(response.text)
        except json.JSONDecodeError:
            return None

    def generate_phrases_by_category(self, category_key: str, user_profile: dict) -> list:
        """
        根據使用者的個人資訊與指定情境類別，使用 Gemini 2.5 生成 3 個最道地的法文句子。
        """
        # 定義情境對照（提供給 AI 更好的語境脈絡）
        category_mapping = {
            "workplace": "職場用語（如：同事交流、面試、工作匯報、咖啡廳或麵包店實務交談）",
            "daily": "日常生活（如：市集買菜、咖啡廳點單、路上問路、與鄰居打招呼）",
            "airport": "機場通關（如：行李托運、海關問答、尋找登機門）",
            "shopping": "購物消費（如：服飾店挑選、退換貨、詢問折扣、結帳）",
            "restaurant": "餐廳點菜（如：預約位子、詢問今日特餐、點餐表達、結帳與打包）",
            "self_intro": "自我介紹（如：新朋友見面、向社團介紹自己，須自然融入用戶興趣）",
            "social": "交友、興趣與價值觀交流（如：小酒館聊天、探討休閒活動、分享個人觀點）"
        }
        
        category_desc = category_mapping.get(category_key, category_key)

        prompt = f"""
        你是一位精通現代法語的母語專家，特別擅長觀察法國（尤其是巴黎）年輕一代的日常口語、流行縮寫（Slang/Verlan）與職場實用對話。
        
        請為以下特定背景的使用者，量身打造 3 個在【{category_desc}】情境下「最道地、最常被使用、法國人聽了會心一笑」的精選法文句子。

        【使用者背景檔案】
        - 稱呼/身份: {user_profile.get('display_name', 'Cary')}
        - 目前法語程度: {user_profile.get('current_level', 'A2')}
        - 核心學習目標: {user_profile.get('learning_goal', '在法國咖啡廳或麵包店工作、文化探索')}
        - 個人興趣/休閒/價值觀: {user_profile.get('interests', '喜歡爬山、自由潛水、滑板、聽 R&B 音樂，有一隻養了五年的貓')}

        【生成核心原則】
        1. 拒絕死板、過時的教科書法文（例如別再只用 "Comment allez-vous?" 或 "Je vais bien"）。
        2. 請大量使用當地人天天掛在嘴邊的慣用語（Idioms環境）、流行縮寫（例如：rando 代替 randonnée、kiffer 代替 aimer、boulot 代替 travail）。
        3. 語氣必須符合情境（職場適度禮貌但要實用；自我介紹與交友則要展現高度的流行口語度）。
        4. 如果是「自我介紹」或「交友與價值觀」情境，請務必精巧、自然地把用戶的特質（如：滑板、爬山、貓、R&B）融合進句子中。

        請嚴格遵循以下 JSON 陣列格式回傳，確保根目錄直接是一個 Array：
        [
          {{
            "french_sentence": "法文句子內容",
            "phonetic": "為台灣人設計的中文擬音/發音暗示（例如：惹 踢夫 特羅 拉 朗多）",
            "chinese_translation": "精準且流暢的台灣中文翻譯",
            "cultural_tip": "文化與口語細節點評。詳細解釋為什麼這句在法國人聽來非常道地？使用的潛規則是什麼？"
          }}
        ]
        """

        try:
            # 💡 核心技術修正：統一改用類別中已經初始化好的 Gemini 模型
            response = self.model.generate_content(prompt)
            result_json = json.loads(response.text)
            
            # 規格化檢查：確保最終輸出格式符合預期
            if isinstance(result_json, list):
                return result_json
            elif isinstance(result_json, dict):
                # 防錯：如果 Gemini 自動加上了外層物件鍵，動態抓出內層的 List
                for val in result_json.values():
                    if isinstance(val, list):
                        return val
            return []
            
        except Exception as e:
            print(f"Gemini 情境生成錯誤: {e}")
            # 降級備用資料 (Mock Data)，保障產品可用性防禦
            return [
                {
                    "french_sentence": "Je kiffe trop la rando, ça me permet de déconnecter à fond après le boulot.",
                    "phonetic": "惹 踢夫 特羅 拉 朗多，灑 門 辦每 德 碟口內克帖 阿 逢 阿不黑 勒 布羅",
                    "chinese_translation": "我超愛爬山，這讓我下班後能徹底切斷繁雜思緒、好好放鬆。",
                    "cultural_tip": "法國人極常使用 'kiffer' 代替 aimer（喜歡），'boulot' 則是 travail（工作）的口語說法。'à fond' 代表『徹底地』。這句話完美融合了你喜歡爬山的特質！"
                }
            ]
