import io
from gtts import gTTS

class NLPEngine:
    def __init__(self):
        # 初始化設定
        pass
        
    def generate_audio(self, text, lang):
        """
        根據輸入的文字與語言代碼生成語音串流
        :param text: 要轉換為語音的文字
        :param lang: 語言代碼（如 'en', 'fr'）
        :return: BytesIO 語音資料流
        """
        # 將應用程式的語言代碼對應至 gTTS 支援的格式
        lang_mapping = {"en": "en", "fr": "fr"}
        tts_lang = lang_mapping.get(lang, "en")
        
        # 產生語音物件
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        
        # 將語音寫入記憶體串流，供 Streamlit st.audio 播放
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return fp
