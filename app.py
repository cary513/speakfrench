import streamlit as st
from services.ai_service import AIService
from gtts import gTTS
import os

# 介面設定
st.set_page_config(page_title="AI Language Swiper", layout="centered")
st.title("🇫🇷 AI 語言學習卡片")

# 初始化 Service (請在此輸入你的 API Key)
# 產品建議：正式環境應使用 st.secrets 隱藏 Key
ai_handler = AIService(api_key="你的_OPENAI_API_KEY")

# 使用 Session State 存儲當前單字狀態
if "current_word_data" not in st.session_state:
    st.session_state.current_word_data = None

# --- UI 輸入區 ---
word_input = st.text_input("輸入你想查詢的單字：", placeholder="例如：Bonjour")

if st.button("查詢"):
    if word_input:
        with st.spinner('AI 正在分析中...'):
            data = ai_handler.get_word_details(word_input)
            st.session_state.current_word_data = data
            
            # 產生音檔
            tts = gTTS(text=word_input, lang='fr')
            tts.save("speech.mp3")

# --- 顯示結果區 ---
if st.session_state.current_word_data:
    data = st.session_state.current_word_data
    
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"{data['word']} /{data['phonetic']}/")
    with col2:
        if os.path.exists("speech.mp3"):
            st.audio("speech.mp3")

    st.write(f"💡 **意思：** {data['translation']}")
    st.info(f"📝 **例句：** {data['example']}\n\n({data['example_cn']})")

    # --- Memo 與 AI 校正 ---
    st.subheader("我的造句筆記 (Memo)")
    user_memo = st.text_area("試著用這個單字造句...")
    if st.button("AI 幫我改造句"):
        if user_memo:
            correction = ai_handler.correct_memo(user_memo)
            st.success(f"**AI 建議：**\n{correction}")

    # --- 左右滑動邏輯 (MVP 暫以按鈕取代) ---
    st.divider()
    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("⬅️ 我已經學會了 (移至已學資料夾)"):
            st.toast("已移動到已學資料夾！")
            # 這裡之後會補上存入資料庫的邏輯
    with right_col:
        if st.button("➡️ 之後再複習 (移至複習資料夾)"):
            st.toast("已加入複習清單！")
