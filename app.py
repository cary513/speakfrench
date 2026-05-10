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
        # 讀取目前的資料（如果試算表是空的，會回傳空 DataFrame）
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        
        # 將新單字轉為 DataFrame
        new_entry = pd.DataFrame([new_data_dict])
        
        # 合併舊資料與新資料
        if existing_data.empty:
            updated_df = new_entry
        else:
            # 檢查是否重複，若重複則不重複加入
            if new_data_dict['word'] in existing_data['word'].values:
                return 
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        
        # 存回 Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
    except Exception as e:
        st.error(f"雲端同步失敗: {e}")

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

# 頁籤 1：單字查詢
with tab1:
    st.title("單字分析與探索")
    word_input = st.text_input("輸入單字（自動偵測英/法文）", placeholder="例如: innovation", key="main_word_input")
    
    if st.button("開始分析", key="analyze_btn"):
        if word_input:
            # 1. 介面視覺回饋
            with st.spinner("AI 正在分析中..."):
                data = ai_service.get_word_analysis(word_input)
            
            if data:
                # 2. 更新 Session 狀態（確保 UI 即時呈現）
                st.session_state.current_data = data
                
                # 3. 更新本地歷史紀錄
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)

                # 4. 執行雲端同步（使用 status 讓使用者看到進度）
                with st.status("正在同步至雲端大腦...", expanded=False) as status:
                    save_word_to_sheets({
                        "word": data['word'],
                        "lang_code": data['lang_code'],
                        "phonetic": data['phonetic'],
                        "meaning": data['meaning'],
                        "example_sentence": data['example_sentence'],
                        "status": "review"
                    })
                    status.update(label="✅ 同步完成！", state="complete", expanded=False)
                
                # 5. 強制刷新畫面
                st.rerun()
            else:
                st.error("AI 分析失敗，請檢查 API Key 或網路。")

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
