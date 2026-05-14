import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import create_client, Client
import pandas as pd

# 1. 頁面初始化
st.set_page_config(page_title="AI 語言學習分析工具 V2", layout="wide")

# 初始化 Supabase 連線
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

@st.cache_resource
def get_services():
    ai_service = AIService()
    nlp_engine = NLPEngine()
    return ai_service, nlp_engine

ai_service, nlp_engine = get_services()

# 函式：從 Supabase 載入歷史資料 (解決重整消失問題)
def load_data_from_supabase():
    try:
        response = supabase.table("vocabulary").select("*").execute()
        data = response.data
        
        if data:
            # 加上防錯機制：轉換小寫與去空格，確保比對精確
            st.session_state.review_zone = [item['word'] for item in data if str(item.get('status', '')).strip().lower() == 'review']
            st.session_state.brain_zone = [item['word'] for item in data if str(item.get('status', '')).strip().lower() == 'mastered']
            st.session_state.word_history = [item['word'] for item in data]
        else:
            st.session_state.review_zone = []
            st.session_state.brain_zone = []
            st.session_state.word_history = []
    except Exception as e:
        st.error(f"從雲端載入資料失敗: {e}")

# 函式：儲存新單字至 Supabase
def save_word_to_supabase(data_dict):
    try:
        response = supabase.table("vocabulary").select("word").eq("word", data_dict["word"]).execute()
        
        # 使用 len() 判斷更為嚴謹與穩定
        if len(response.data) == 0:
            supabase.table("vocabulary").insert(data_dict).execute()
            st.toast(f"✅ {data_dict['word']} 已同步至雲端資料庫")
        else:
            st.toast(f"💡 {data_dict['word']} 已在資料庫中")
    except Exception as e:
        st.error(f"雲端儲存失敗: {e}")

# 函式：更新 Supabase 中的單字狀態
def update_word_status_in_supabase(word: str, new_status: str):
    try:
        supabase.table("vocabulary").update({"status": new_status}).eq("word", word).execute()
        st.toast(f"雲端同步成功：{word} 移至大腦區 🧠")
    except Exception as e:
        st.error(f"同步狀態至雲端失敗: {e}")

# --- 初始化 Session State (開機自動加載) ---
if "word_history" not in st.session_state:
    st.session_state.word_history = []
    st.session_state.review_zone = []
    st.session_state.brain_zone = []
    st.session_state.current_card_index = 0
    load_data_from_supabase()

# ==========================================
# 3. 側邊欄 (Sidebar) 
# ==========================================
with st.sidebar:
    st.header("📚 知識庫分類")
    
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
    word_input = st.text_input("輸入單字（自動偵測英/法文）", placeholder="例如: innovation", key="main_input")
    
    if st.button("開始分析", key="analyze_btn"):
        if word_input:
            with st.spinner("AI 正在建模中..."):
                data = ai_service.get_word_analysis(word_input)
                
            if data:
                st.session_state.current_data = data
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)
                
                # 正確呼叫 Supabase 儲存函式
                with st.status("正在同步至雲端大腦..."):
                    save_word_to_supabase({
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

    # 顯示查詢結果
    if "current_data" in st.session_state:
        data = st.session_state.current_data
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{data['word']} /{data['phonetic']}/ ({data['lang_code']})")
            with col2:
                try:
                    audio_stream = nlp_engine.generate_audio(data['word'], lang=data['lang_code'])
                    if audio_stream:
                        st.audio(audio_stream, format='audio/mp3')
                except Exception:
                    st.warning("語音生成暫時無法使用")
            
            st.write(f"**意思：** {data['meaning']}")
            st.markdown("---")
            st.write("**例句演示：**")
            st.info(f"{data['example_sentence']}\n\n*{data.get('sentence_translation', '')}*")

# 頁籤 2：複習卡
with tab2:
    st.title("🗂️ 複習卡系統")
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！所有單字都已經記住了！")
    else:
        if st.session_state.current_card_index >= len(st.session_state.review_zone):
            st.session_state.current_card_index = 0
            
        current_word = st.session_state.review_zone[st.session_state.current_card_index]
        
        # --- 核心體驗優化：若本地無資料，動態向 Supabase 撈取 ---
        card_data = None
        if "current_data" in st.session_state and st.session_state.current_data['word'] == current_word:
            card_data = st.session_state.current_data
        else:
            # 從 Supabase 撈取此單字的詳細資料，免去重複查詢的困擾
            try:
                db_res = supabase.table("vocabulary").select("*").eq("word", current_word).execute()
                if db_res.data:
                    card_data = db_res.data[0]
            except Exception:
                pass

        # 顯示卡片內容
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align: center;'>{current_word}</h2>", unsafe_allow_html=True)
            
            if card_data:
                st.markdown(f"<p style='text-align: center;'><strong>/{card_data.get('phonetic', '')}/</strong></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>{card_data.get('meaning', '')}</p>", unsafe_allow_html=True)
                if card_data.get('example_sentence'):
                    st.caption(f"💡 例句提示：{card_data['example_sentence']}")
            else:
                st.caption("🔍 無法載入詳細釋義")

        # 模擬左右滑動按鈕
        col_left, _, col_right = st.columns([1, 2, 1])
        with col_left:
            if st.button("👈 左滑：待複習", use_container_width=True, key="left_swipe_btn"):
                st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(st.session_state.review_zone)
                st.rerun()
        with col_right:
            if st.button("👉 右滑：已記憶", use_container_width=True, key="right_swipe_btn"):
                word_to_move = st.session_state.review_zone.pop(st.session_state.current_card_index)
                
                if word_to_move not in st.session_state.brain_zone:
                    st.session_state.brain_zone.append(word_to_move)
                
                # 異步同步雲端狀態為 'mastered'
                update_word_status_in_supabase(word_to_move, "mastered")
                
                st.session_state.current_card_index = 0
                st.rerun()
