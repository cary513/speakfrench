import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 頁面初始化
st.set_page_config(page_title="AI 語言學習分析工具 V2", layout="wide")

@st.cache_resource
def get_services():
    ai_service = AIService()
    nlp_engine = NLPEngine()
    return ai_service, nlp_engine

ai_service, nlp_engine = get_services()

# --- 新增：Google Sheets 連線與儲存函式 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_word_to_sheets(new_data_dict):
    try:
        # 1. 讀取目前的資料，ttl=0 確保不使用快取，直接抓取雲端最新狀態
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        
        # 2. 強制檢查讀取進來的資料結構
        # 有時候讀進來會變成 None 或 全空，這時我們自己建立一個有標題的 DataFrame
        if existing_data is None or existing_data.empty:
            updated_df = pd.DataFrame([new_data_dict])
        else:
            # 3. 確保 'word' 這一欄真的存在於讀取的資料中
            if 'word' in existing_data.columns:
                # 檢查是否重複
                if new_data_dict['word'] in existing_data['word'].astype(str).values:
                    st.toast(f"💡 {new_data_dict['word']} 已在雲端庫中")
                    return 
                # 合併新舊資料
                updated_df = pd.concat([existing_data, pd.DataFrame([new_data_dict])], ignore_index=True)
            else:
                # 如果讀進來沒抓到標題，直接以新資料為主
                updated_df = pd.DataFrame([new_data_dict])
        
        # 4. 存回 Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
        st.toast("✅ 雲端同步成功！")
    except Exception as e:
        st.error(f"雲端同步失敗，請檢查權限或網路: {e}")

# --- 原有初始化 Session State ---
if "word_history" not in st.session_state:
    st.session_state.word_history = []
if "review_zone" not in st.session_state:
    st.session_state.review_zone = []
if "brain_zone" not in st.session_state:
    st.session_state.brain_zone = []
if "current_card_index" not in st.session_state:
    st.session_state.current_card_index = 0

# ==========================================
# 3. 側邊欄 (Sidebar) 
# ==========================================
with st.sidebar:
    st.header("📚 知識庫分類")
    # ... (保持原本側邊欄程式碼不變)
    st.subheader("待複習區 (Review Zone)")
    if not st.session_state.review_zone:
        st.caption("無待複習單字")
    else:
        for word in st.session_state.review_zone:
            st.markdown(f"🟨 **{word}**")
    st.markdown("---")
    st.subheader("大腦區 (Mastered)")
    if not st.session_state.brain_zone:
        st.caption("尚未記憶單字")
    else:
        for word in st.session_state.brain_zone:
            st.markdown(f"🟩 **{word}**")

# ==========================================
# 4. 主畫面 (Main Content)
# ==========================================
tab1, tab2 = st.tabs(["🔍 單字查詢", "🗂️ 複習卡 (Flashcards)"])

with tab1:
    st.title("單字分析與探索")
    word_input = st.text_input("輸入單字（自動偵測英/法文）", placeholder="例如: innovation")
    
    if st.button("開始分析"):
        if word_input:
            with st.spinner("AI 正在建模中..."):
                data = ai_service.get_word_analysis(word_input)
                
            if data:
                st.session_state.current_data = data
                
                # A. 儲存至本地 Session
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)
                
                # B. --- 新增：同步至 Google Sheets ---
                with st.status("正在同步至雲端大腦..."):
                    save_word_to_sheets({
                        "word": data['word'],
                        "lang_code": data['lang_code'],
                        "phonetic": data['phonetic'],
                        "meaning": data['meaning'],
                        "example_sentence": data['example_sentence'],
                        "status": "review"
                    })
                
                st.rerun()
            else:
                st.error("分析失敗")

    # ... (顯示查詢結果的程式碼不變)
    if "current_data" in st.session_state:
        data = st.session_state.current_data
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{data['word']} /{data['phonetic']}/ ({data['lang_code']})")
            with col2:
                try:
                    audio_stream = nlp_engine.generate_audio(data['word'], lang=data['lang_code'])
                    st.audio(audio_stream, format='audio/mp3')
                except Exception:
                    st.warning("語音生成暫時無法使用")
            st.write(f"**意思：** {data['meaning']}")
            st.markdown("---")
            st.write("**例句演示：**")
            st.info(f"{data['example_sentence']}\n\n*{data['sentence_translation']}*")

# 頁籤 2：複習卡
with tab2:
    # ... (保持原本複習卡程式碼不變)
    st.title("🗂️ 複習卡系統")
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！所有單字都已經記住了！")
    else:
        if st.session_state.current_card_index >= len(st.session_state.review_zone):
            st.session_state.current_card_index = 0
        current_word = st.session_state.review_zone[st.session_state.current_card_index]
        card_data = None
        if "current_data" in st.session_state and st.session_state.current_data['word'] == current_word:
            card_data = st.session_state.current_data

        with st.container(border=True):
            st.markdown(f"<h2 style='text-align: center;'>{current_word}</h2>", unsafe_allow_html=True)
            if card_data:
                st.markdown(f"<p style='text-align: center;'><strong>/{card_data['phonetic']}/</strong></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>{card_data['meaning']}</p>", unsafe_allow_html=True)

        col_left, _, col_right = st.columns([1, 2, 1])
        with col_left:
            if st.button("👈 左滑：待複習", use_container_width=True):
                st.session_state.current_card_index += 1
                st.rerun()
        with col_right:
            if st.button("👉 右滑：已記憶", use_container_width=True):
                word_to_move = st.session_state.review_zone.pop(st.session_state.current_card_index)
                st.session_state.brain_zone.append(word_to_move)
                # 這裡你也可以加入一個更新 Google Sheets status 的邏輯
                st.session_state.current_card_index = 0
                st.rerun()
