import streamlit as st
from gtts import gTTS
from io import BytesIO

class NLPEngine:
    def __init__(self):
        # 僅在真的需要 NLP 分析時才加載 spacy
        self.nlp = None

    @st.cache_data # 使用 cache 避免同一個單字重複向 Google 請求
    def get_speech(self, text, lang='fr'):
        """
        將文字轉語音，並回傳 BytesIO 流
        """
        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=text, lang=lang)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp
        except Exception as e:
            st.error(f"語音生成失敗: {e}")
            return None

# 實例化供外部調用
nlp_engine = NLPEngine()
