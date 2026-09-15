import json
import os
import re
from typing import Any

import google.generativeai as genai

try:
    import streamlit as st
except ImportError:
    st = None


class AIService:
    """英文與法文學習內容生成服務。"""

    def __init__(self) -> None:
        api_key = self._get_api_key()

        if not api_key:
            raise ValueError(
                "AIService：未偵測到 GOOGLE_API_KEY。"
                "請在環境變數或 .streamlit/secrets.toml 中設定。"
            )

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
            },
        )

    @staticmethod
    def _get_api_key() -> str | None:
        """先讀取環境變數，再讀取 Streamlit Secrets。"""
        api_key = os.getenv("GOOGLE_API_KEY")

        if api_key:
            return api_key.strip()

        if st is not None:
            try:
                secret_key = st.secrets.get("GOOGLE_API_KEY")

                if secret_key:
                    return str(secret_key).strip()

            except Exception:
                pass

        return None

    @staticmethod
    def _parse_json(raw_text: str | None) -> Any:
        """移除 Markdown 程式碼標記並解析 JSON。"""
        if not raw_text:
            return None

        cleaned_text = str(raw_text).strip()

        cleaned_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned_text,
            flags=re.IGNORECASE,
        )

        cleaned_text = re.sub(
            r"\s*```$",
            "",
            cleaned_text,
        )

        return json.loads(cleaned_text)

    @staticmethod
    def _clean_string(value: Any) -> str:
        """將欄位安全轉換成乾淨字串。"""
        if value is None:
            return ""

        cleaned_value = str(value).strip()

        if cleaned_value.casefold() in {
            "ellipsis",
            "null",
            "none",
            "n/a",
        }:
            return ""

        return cleaned_value

    @classmethod
    def _validate_analysis(
        cls,
        data: Any,
    ) -> dict[str, Any] | None:
        """驗證並標準化單字／句子分析結果。"""
        if not isinstance(data, dict):
            return None

        input_type = cls._clean_string(
            data.get("input_type")
        ).lower()

        lang_code = cls._clean_string(
            data.get("lang_code")
        ).lower()

        if input_type not in {"word", "sentence"}:
            return None

        if lang_code not in {"en", "fr"}:
            return None

        word = cls._clean_string(data.get("word"))
        phonetic = cls._clean_string(data.get("phonetic"))
        meaning = cls._clean_string(data.get("meaning"))

        example_sentence = cls._clean_string(
            data.get("example_sentence")
        )

        sentence_translation = cls._clean_string(
            data.get("sentence_translation")
        )

        if not word or not meaning:
            return None

        # IPA 偶爾可能產生失敗，不應因此捨棄整份結果。
        if not phonetic:
            phonetic = "暫無發音資料"

        if not example_sentence:
            example_sentence = word

        if not sentence_translation:
            sentence_translation = meaning

        raw_breakdown = data.get("word_breakdown", [])
        cleaned_breakdown: list[dict[str, str]] = []

        if isinstance(raw_breakdown, list):
            for item in raw_breakdown:
                if not isinstance(item, dict):
                    continue

                item_word = cls._clean_string(
                    item.get("word")
                )

                item_meaning = cls._clean_string(
                    item.get("meaning")
                )

                if not item_word or not item_meaning:
                    continue

                lemma = cls._clean_string(
                    item.get("lemma")
                )

                item_phonetic = cls._clean_string(
                    item.get("phonetic")
                )

                part_of_speech = cls._clean_string(
                    item.get("part_of_speech")
                )

                cleaned_breakdown.append(
                    {
                        "word": item_word,
                        "lemma": lemma or item_word,
                        "phonetic": item_phonetic,
                        "part_of_speech": part_of_speech,
                        "meaning": item_meaning,
                    }
                )

        # 如果 Gemini 沒有回傳逐字解析，建立基本資料，
        # 避免前端完全沒有內容。
        if not cleaned_breakdown:
            cleaned_breakdown = [
                {
                    "word": word,
                    "lemma": word,
                    "phonetic": phonetic,
                    "part_of_speech": "",
                    "meaning": meaning,
                }
            ]

        return {
            "input_type": input_type,
            "word": word,
            "original_text": word,
            "lang_code": lang_code,
            "phonetic": phonetic,
            "meaning": meaning,
            "translation": meaning,
            "chinese_translation": meaning,
            "example_sentence": example_sentence,
            "sentence_translation": sentence_translation,
            "word_breakdown": cleaned_breakdown,
        }

    def get_word_analysis(
        self,
        text: str,
    ) -> dict[str, Any] | None:
        """
        分析英文或法文的單字／完整句子。

        回傳欄位可直接提供 app.py 顯示：
        - word
        - original_text
        - meaning
        - translation
        - chinese_translation
        - phonetic
        - example_sentence
        - sentence_translation
        - word_breakdown
        """
        cleaned_input = self._clean_string(text)

        if not cleaned_input:
            return None

        system_prompt = """
你是一位專業的英語與法語教師，專門協助使用繁體中文的台灣學習者。

使用者可能輸入：
1. 一個英文單字
2. 一個法文單字
3. 一個英文完整句子
4. 一個法文完整句子

請自動辨識輸入語言和內容類型，並修正明顯的拼寫或文法錯誤。

請只回傳合法 JSON，不要使用 Markdown，也不要加入說明文字。

JSON 格式：

{
  "input_type": "word 或 sentence",
  "word": "修正後的完整原文",
  "lang_code": "en 或 fr",
  "phonetic": "完整內容的 IPA 音標",
  "meaning": "完整內容的繁體中文翻譯",
  "example_sentence": "自然且實用的完整例句",
  "sentence_translation": "example_sentence 的繁體中文翻譯",
  "word_breakdown": [
    {
      "word": "實際出現在原文中的單字",
      "lemma": "單字原形",
      "phonetic": "單字 IPA 音標",
      "part_of_speech": "繁體中文詞性",
      "meaning": "這個單字在目前語境中的繁體中文意思"
    }
  ]
}

規則：
1. input_type 只能是 word 或 sentence。
2. lang_code 只能是 en 或 fr。
3. 修正文法時不可改變使用者原意。
4. meaning 必須是完整原文的繁體中文翻譯。
5. word_breakdown 必須按照原句順序列出每一個單字。
6. 重複出現的單字也必須保留。
7. 不要把標點符號獨立列為單字。
8. 法文縮合形式如 j'aime、l'école、c'est 必須保留。
9. 單字翻譯必須符合目前句子的語境。
10. 如果輸入只有一個單字，word_breakdown 仍須包含該單字。
11. 所有欄位都必須存在。
12. 不可回傳 null、None、Ellipsis 或空白內容。
"""

        user_prompt = (
            "請分析以下英文或法文內容：\n"
            f"{cleaned_input}"
        )

        try:
            response = self.model.generate_content(
                [system_prompt, user_prompt]
            )

            raw_response = getattr(response, "text", None)

            if not raw_response:
                raise RuntimeError(
                    "Gemini 沒有回傳文字內容"
                )

            parsed_data = self._parse_json(raw_response)
            validated_data = self._validate_analysis(parsed_data)

            if not validated_data:
                raise ValueError(
                    "Gemini 回傳的 JSON 格式不完整"
                )

            return validated_data

        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Gemini JSON 解析失敗：{error}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Gemini 分析失敗：{error}"
            ) from error

    def generate_phrases_by_category(
        self,
        category_key: str,
        user_profile: dict[str, Any] | None,
    ) -> list[dict[str, str]]:
        """根據個人資訊與指定情境生成三個法文句子。"""
        if not isinstance(user_profile, dict):
            user_profile = {}

        category_mapping = {
            "workplace": (
                "職場用語，例如同事交流、面試、工作匯報、"
                "咖啡廳或麵包店實務交談"
            ),
            "daily": (
                "日常生活，例如市集買菜、咖啡廳點單、"
                "路上問路及與鄰居打招呼"
            ),
            "airport": (
                "機場通關，例如行李托運、海關問答及"
                "尋找登機門"
            ),
            "shopping": (
                "購物消費，例如服飾店挑選、退換貨、"
                "詢問折扣及結帳"
            ),
            "restaurant": (
                "餐廳點菜，例如預約位子、詢問今日特餐、"
                "點餐、結帳及打包"
            ),
            "self_intro": (
                "自我介紹，例如認識新朋友或向社團介紹自己"
            ),
            "social": (
                "交友、興趣與價值觀交流，例如聊天、"
                "分享休閒活動與個人觀點"
            ),
        }

        category_desc = category_mapping.get(
            category_key,
            category_key or "日常生活",
        )

        display_name = self._clean_string(
            user_profile.get("display_name")
        ) or "Cary"

        current_level = self._clean_string(
            user_profile.get("current_level")
        ) or "A2"

        learning_goal = self._clean_string(
            user_profile.get("learning_goal")
        ) or "使用自然法語完成日常交流"

        interests = self._clean_string(
            user_profile.get("interests")
        ) or "旅行、設計、音樂和貓"

        prompt = f"""
你是一位精通現代法語的母語教師，熟悉法國日常口語和文化。

請為以下使用者生成剛好三個符合指定情境、自然且實用的法文句子。

指定情境：
{category_desc}

使用者資料：
稱呼：{display_name}
程度：{current_level}
學習目標：{learning_goal}
興趣：{interests}

生成規則：
1. 必須生成剛好三個不同的句子。
2. 每個句子都必須符合指定情境。
3. 使用現代、自然且實用的法語。
4. 避免過時或過度正式的教科書句型。
5. 難度必須符合使用者程度。
6. cultural_tip 必須使用繁體中文。
7. phonetic 請優先提供 IPA。
8. 每個欄位都不可留空。

請只回傳合法 JSON 陣列：

[
  {{
    "french_sentence": "法文句子",
    "phonetic": "IPA 發音",
    "chinese_translation": "繁體中文翻譯",
    "cultural_tip": "使用情境、語氣和文化說明"
  }},
  {{
    "french_sentence": "法文句子",
    "phonetic": "IPA 發音",
    "chinese_translation": "繁體中文翻譯",
    "cultural_tip": "使用情境、語氣和文化說明"
  }},
  {{
    "french_sentence": "法文句子",
    "phonetic": "IPA 發音",
    "chinese_translation": "繁體中文翻譯",
    "cultural_tip": "使用情境、語氣和文化說明"
  }}
]
"""

        try:
            response = self.model.generate_content(prompt)
            raw_response = getattr(response, "text", None)

            if not raw_response:
                raise RuntimeError(
                    "Gemini 沒有回傳情境句子"
                )

            parsed_result = self._parse_json(raw_response)

            if isinstance(parsed_result, dict):
                possible_lists = [
                    value
                    for value in parsed_result.values()
                    if isinstance(value, list)
                ]

                parsed_result = (
                    possible_lists[0]
                    if possible_lists
                    else []
                )

            if not isinstance(parsed_result, list):
                raise ValueError(
                    "情境句子的回傳格式不是陣列"
                )

            cleaned_results: list[dict[str, str]] = []

            for item in parsed_result:
                if not isinstance(item, dict):
                    continue

                french_sentence = self._clean_string(
                    item.get("french_sentence")
                )

                phonetic = self._clean_string(
                    item.get("phonetic")
                )

                chinese_translation = self._clean_string(
                    item.get("chinese_translation")
                )

                cultural_tip = self._clean_string(
                    item.get("cultural_tip")
                )

                if not french_sentence or not chinese_translation:
                    continue

                cleaned_results.append(
                    {
                        "french_sentence": french_sentence,
                        "phonetic": phonetic,
                        "chinese_translation": chinese_translation,
                        "cultural_tip": cultural_tip,
                    }
                )

            if not cleaned_results:
                raise ValueError(
                    "Gemini 沒有產生有效的情境句子"
                )

            return cleaned_results[:3]

        except Exception as error:
            print(f"Gemini 情境生成錯誤：{error}")
            return self._fallback_phrases(category_key)

    @staticmethod
    def _fallback_phrases(
        category_key: str,
    ) -> list[dict[str, str]]:
        """Gemini 暫時無法使用時顯示的備用句子。"""
        fallback_data = {
            "restaurant": [
                {
                    "french_sentence": (
                        "Je voudrais un café, s'il vous plaît."
                    ),
                    "phonetic": (
                        "/ʒə vu.dʁɛ œ̃ ka.fe sil vu plɛ/"
                    ),
                    "chinese_translation": (
                        "我想要一杯咖啡，謝謝。"
                    ),
                    "cultural_tip": (
                        "使用 Je voudrais 比直接說 Je veux 更有禮貌。"
                    ),
                },
                {
                    "french_sentence": (
                        "Qu'est-ce que vous recommandez ?"
                    ),
                    "phonetic": (
                        "/kɛs kə vu ʁə.kɔ.mɑ̃.de/"
                    ),
                    "chinese_translation": (
                        "您推薦什麼？"
                    ),
                    "cultural_tip": (
                        "適合詢問服務人員推薦的餐點。"
                    ),
                },
                {
                    "french_sentence": (
                        "L'addition, s'il vous plaît."
                    ),
                    "phonetic": (
                        "/la.di.sjɔ̃ sil vu plɛ/"
                    ),
                    "chinese_translation": (
                        "麻煩結帳。"
                    ),
                    "cultural_tip": (
                        "這是在法國餐廳請服務人員結帳的自然說法。"
                    ),
                },
            ],
            "workplace": [
                {
                    "french_sentence": (
                        "Je vais terminer cette tâche cet après-midi."
                    ),
                    "phonetic": (
                        "/ʒə vɛ tɛʁ.mi.ne sɛt taʃ sɛ.ta.pʁɛ.mi.di/"
                    ),
                    "chinese_translation": (
                        "我今天下午會完成這項工作。"
                    ),
                    "cultural_tip": (
                        "適合用來向同事說明工作進度。"
                    ),
                },
                {
                    "french_sentence": (
                        "Est-ce que tu peux m'aider ?"
                    ),
                    "phonetic": (
                        "/ɛs kə ty pø mɛ.de/"
                    ),
                    "chinese_translation": (
                        "你可以幫我嗎？"
                    ),
                    "cultural_tip": (
                        "對熟悉的同事可使用 tu；正式場合改用 vous。"
                    ),
                },
                {
                    "french_sentence": (
                        "On peut en discuter demain."
                    ),
                    "phonetic": (
                        "/ɔ̃ pø ɑ̃ dis.ky.te də.mɛ̃/"
                    ),
                    "chinese_translation": (
                        "我們明天可以討論這件事。"
                    ),
                    "cultural_tip": (
                        "On 在日常職場口語中常用來表示「我們」。"
                    ),
                },
            ],
            "default": [
                {
                    "french_sentence": (
                        "Bonjour, comment allez-vous ?"
                    ),
                    "phonetic": (
                        "/bɔ̃.ʒuʁ kɔ.mɑ̃ ta.le vu/"
                    ),
                    "chinese_translation": (
                        "您好，您最近好嗎？"
                    ),
                    "cultural_tip": (
                        "適合第一次見面或較正式的場合。"
                    ),
                },
                {
                    "french_sentence": (
                        "J'apprends le français en ce moment."
                    ),
                    "phonetic": (
                        "/ʒa.pʁɑ̃ lə fʁɑ̃.sɛ ɑ̃ sə mɔ.mɑ̃/"
                    ),
                    "chinese_translation": (
                        "我目前正在學法文。"
                    ),
                    "cultural_tip": (
                        "適合在自我介紹時說明自己的學習狀態。"
                    ),
                },
                {
                    "french_sentence": (
                        "J'aime découvrir de nouvelles choses."
                    ),
                    "phonetic": (
                        "/ʒɛm de.ku.vʁiʁ də nu.vɛl ʃoz/"
                    ),
                    "chinese_translation": (
                        "我喜歡探索新事物。"
                    ),
                    "cultural_tip": (
                        "適合用來分享自己的個性或興趣。"
                    ),
                },
            ],
        }

        return fallback_data.get(
            category_key,
            fallback_data["default"],
        )
