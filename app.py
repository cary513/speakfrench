import streamlit as st
from ai_service import AIService
from nlp_engine import NLPEngine

# 初始化服務（建議使用 cache 避免重複初始化）
@st.cache_resource
def init_services():
    return AIService(), NLPEngine()

ai_service, nlp_engine = init_services()

st.set_page_config(page_title="AI 語言卡片 V2", layout="centered")

st.title("🧩 AI 語言學習分析工具")
st.caption("基於 Gemini 1.5 Flash 技術的自動化學習原型")

word_input = st.text_input("輸入單字（自動偵測英/法文）", placeholder="例如: innovation 或 bonjour")

if word_input:
    with st.spinner("AI 正在建模中..."):
        data = ai_service.get_word_analysis(word_input)
        
    if data:
        # UI 配置優化：使用 Container 區分功能區塊
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{data['word']} /{data['phonetic']}/")
            with col2:
                # 語音生成
                audio_stream = nlp_engine.generate_audio(data['word'], lang=data['lang_code'])
                st.audio(audio_stream, format='audio/mp3')

            st.write(f"**意思：** {data['meaning']}")
            
            st.markdown("---")
            st.write("**例句演示：**")
            st.info(f"{data['example_sentence']}\n\n*{data['sentence_translation']}*")
    else:
        st.error("分析失敗，請檢查網路或 API 配置。")
