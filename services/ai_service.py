import os
import json
import re
import google.generativeai as genai


class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "AIService：未偵測到 GOOGLE_API_KEY 環境變數"
            )

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json"
            }
        )

    @staticmethod
    def _parse_json(raw_text):
        """移除可能出現的 Markdown 標記並解析 JSON。"""
        if not raw_text:
            return None

        cleaned_text = raw_text.strip()
        cleaned_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned_text,
            flags=re.IGNORECASE
        )
        cleaned_text = re.sub(
            r"\s*```$",
            "",
            cleaned_text
        )

        return json.loads(cleaned_text)

    @staticmethod
    def _validate_analysis(data):
        """檢查搜尋分析結果格式。"""
        if not isinstance(data, dict):
            return False

        required_keys = [
            "input_type",
            "word",
            "lang_code",
            "phonetic",
            "meaning",
            "example_sentence",
            "sentence_translation",
            "word_breakdown"
        ]

        for key in required_keys:
            if key not in data:
                return False

        if data["input_type"] not in ["word", "sentence"]:
            return False

        if data["lang_code"] not in ["en", "fr"]:
            return False

        for key in [
            "word",
            "phonetic",
            "meaning",
            "example_sentence",
            "sentence_translation"
        ]:
            value = str(data.get(key, "")).strip()

            if not value:
                return False

            if value.lower() in ["ellipsis", "null", "none"]:
                return False

        breakdown = data.get("word_breakdown")

        if not isinstance(breakdown, list) or not breakdown:
            return False

        cleaned_breakdown = []

        for item in breakdown:
            if not isinstance(item, dict):
                continue

            item_word = str(item.get("word", "")).strip()
            item_meaning = str(item.get("meaning", "")).strip()

            if not item_word or not item_meaning:
                continue

            cleaned_breakdown.append({
                "word": item_word,
                "lemma": str(
                    item.get("lemma", item_word)
                ).strip(),
                "phonetic": str(
                    item.get("phonetic", "")
                ).strip(),
                "part_of_speech": str(
                    item.get("part_of_speech", "")
                ).strip(),
                "meaning": item_meaning
            })

        if not cleaned_breakdown:
            return False

        data["word_breakdown"] = cleaned_breakdown
        return True

    def get_word_analysis(self, text):
        """
        分析英文或法文的單字／完整句子。

        保留 get_word_analysis 名稱，
        讓原本 app.py 不需要全面改寫。
        """
        text = str(text).strip()

        if not text:
            return None

        system_prompt = """
你是一位專業的英語與法語教師，專門協助使用繁體中文的台灣學習者。

使用者可能輸入：
1. 一個英文或法文單字
2. 一個英文或法文完整句子

請自動辨識輸入語言與內容類型。

請嚴格回傳以下 JSON 格式。
不要使用 Markdown。
不要加入 JSON 以外的說明文字。

{
  "input_type": "word 或 sentence",
  "word": "修正明顯拼寫或文法後的原文",
  "lang_code": "en 或 fr",
  "phonetic": "完整輸入內容的 IPA 音標",
  "meaning": "完整內容的繁體中文翻譯或核心解釋",
  "example_sentence": "單字請提供自然例句；句子請保留修正後的完整句子",
  "sentence_translation": "example_sentence 的繁體中文翻譯",
  "word_breakdown": [
    {
      "word": "實際出現在原文中的單字",
      "lemma": "單字原形",
      "phonetic": "單字 IPA 音標",
      "part_of_speech": "繁體中文詞性",
      "meaning": "單字在目前語境中的繁體中文意思"
    }
  ]
}

重要規則：
1. 自動判斷輸入是英文或法文。
2. 自動判斷輸入是單字或完整句子。
3. 修正明顯拼寫或文法錯誤，但不可改變原意。
4. word_breakdown 必須按照原句順序列出每一個單字。
5. 重複出現的單字也必須保留。
6. 不要將標點符號獨立列為單字。
7. 法文縮合形式如 j'aime、l'école、c'est，必須保留自然形式。
8. meaning 必須根據目前句子的語境翻譯。
9. 若輸入只有一個單字，word_breakdown 仍須包含該單字。
10. 每個欄位都不可缺少或留空。
11. 不可回傳 Ellipsis、null、None 或無意義資料。
"""

        user_prompt = (
            "請分析以下英文或法文內容：\n"
            f"{text}"
        )

        try:
            response = self.model.generate_content(
                [system_prompt, user_prompt]
            )

            data = self._parse_json(response.text)

            if not self._validate_analysis(data):
                print("get_word_analysis：AI 回傳格式不完整")
                return None

            return data

        except json.JSONDecodeError as error:
            print(f"Gemini JSON 解析錯誤：{error}")
            return None

        except Exception as error:
            print(f"get_word_analysis 錯誤：{error}")
            return None

    def generate_phrases_by_category(
        self,
        category_key: str,
        user_profile: dict
    ) -> list:
        """根據個人資訊與情境生成三個法文句子。"""

        category_mapping = {
            "workplace": (
                "職場用語，例如同事交流、面試、工作匯報、"
                "咖啡廳或麵包店實務交談"
            ),
            "daily": (
                "日常生活，例如市集買菜、咖啡廳點單、"
                "路上問路、與鄰居打招呼"
            ),
            "airport": (
                "機場通關，例如行李托運、海關問答、"
                "尋找登機門"
            ),
            "shopping": (
                "購物消費，例如服飾店挑選、退換貨、"
                "詢問折扣、結帳"
            ),
            "restaurant": (
                "餐廳點菜，例如預約位子、詢問今日特餐、"
                "點餐、結帳與打包"
            ),
            "self_intro": (
                "自我介紹，例如認識新朋友或向社團介紹自己"
            ),
            "social": (
                "交友、興趣與價值觀交流，例如小酒館聊天、"
                "分享休閒活動與個人觀點"
            )
        }

        category_desc = category_mapping.get(
            category_key,
            category_key
        )

        display_name = user_profile.get(
            "display_name",
            "Cary"
        )
        current_level = user_profile.get(
            "current_level",
            "A2"
        )
        learning_goal = user_profile.get(
            "learning_goal",
            "在法國咖啡廳或麵包店工作、文化探索"
        )
        interests = user_profile.get(
            "interests",
            "喜歡爬山、自由潛水、滑板、R&B 音樂和貓"
        )

        prompt = f"""
你是一位精通現代法語的母語教師，熟悉法國日常口語、
巴黎生活、常見慣用語、Slang 與 Verlan。

請為以下使用者生成三個符合指定情境、自然且實用的法文句子。

【指定情境】
{category_desc}

【使用者資料】
稱呼：{display_name}
程度：{current_level}
學習目標：{learning_goal}
興趣與價值觀：{interests}

生成原則：
1. 必須符合指定情境。
2. 使用現代、自然且實用的法語。
3. 避免過時或過度正式的教科書句型。
4. 內容必須符合使用者目前程度。
5. 若為自我介紹或社交情境，自然融入使用者興趣。
6. cultural_tip 必須解釋使用情境、語氣與文化差異。

嚴格回傳以下 JSON 陣列，不要加入其他文字：

[
  {{
    "french_sentence": "法文句子",
    "phonetic": "IPA 或適合台灣學習者的發音提示",
    "chinese_translation": "繁體中文翻譯",
    "cultural_tip": "文化、語氣與口語使用說明"
  }}
]
"""

        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json(response.text)

            if isinstance(result, list):
                return result

            if isinstance(result, dict):
                for value in result.values():
                    if isinstance(value, list):
                        return value

            return []

        except Exception as error:
            print(f"Gemini 情境生成錯誤：{error}")

            mock_data_pool = {
                "restaurant": [
                    {
                        "french_sentence": (
                            "Je pourrais avoir un café allongé "
                            "et un croissant, s'il vous plaît ?"
                        ),
                        "phonetic": (
                            "熱 普黑 阿瓦赫 安 卡菲 阿隆惹 "
                            "欸 安 誇桑，希爾 物 普雷"
                        ),
                        "chinese_translation": (
                            "麻煩給我一杯美式咖啡和一個可頌。"
                        ),
                        "cultural_tip": (
                            "在法國，café allongé 是常見的"
                            "長咖啡說法，比 Americano 更自然。"
                        )
                    }
                ],
                "workplace": [
                    {
                        "french_sentence": (
                            "Désolé, on est un peu sous l'eau "
                            "ce matin avec le coup de feu."
                        ),
                        "phonetic": (
                            "得佐雷，翁 奈 安 波 蘇 洛，"
                            "瑟 馬丹 阿維克 勒 庫 德 佛"
                        ),
                        "chinese_translation": (
                            "抱歉，今天早上的尖峰時段"
                            "我們有點忙不過來。"
                        ),
                        "cultural_tip": (
                            "être sous l'eau 表示工作太多；"
                            "coup de feu 常指餐飲業尖峰時段。"
                        )
                    }
                ],
                "self_intro": [
                    {
                        "french_sentence": (
                            "J'adore la randonnée, ça me permet "
                            "de déconnecter après le travail."
                        ),
                        "phonetic": (
                            "札多赫 拉 夯多內，薩 默 佩赫梅 "
                            "德 德科內克泰 阿普黑 勒 特哈瓦伊"
                        ),
                        "chinese_translation": (
                            "我很喜歡健行，這讓我下班後"
                            "可以放空和休息。"
                        ),
                        "cultural_tip": (
                            "déconnecter 在日常法語中可表示"
                            "暫時離開工作與壓力。"
                        )
                    }
                ]
            }

            return mock_data_pool.get(
                category_key,
                mock_data_pool["self_intro"]
            )
