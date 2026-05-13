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
    # 這裡會自動讀取 Secrets 裡的 SUPABASE_URL 和 SUPABASE_KEY
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

# 儲存單字至 Supabase
def save_word_to_supabase(data_dict):
    try:
        # PM 邏輯：檢查單字是否重複 (確保資料庫唯一性)
        response = supabase.table("vocabulary").select("word").eq("word", data_dict["word"]).execute()
        
        if not response.data:
            # 如果不存在，則插入新資料
            supabase.table("vocabulary").insert(data_dict).execute()
            st.toast(f"✅ {data_dict['word']} 已同步至雲端資料庫")
        else:
            st.toast(f"💡 {data_dict['word']} 已在資料庫中")
    except Exception as e:
        st.error(f"雲端儲存失敗: {e}")

# --- 初始化 Session State ---
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
                # 儲存到本地
                st.session_state.current_data = data
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)
                
                # 同步到 Supabase (呼叫修正後的函式名稱)
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
                    # 每次渲染時生成音訊，解決 rerun 消失問題
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
        
        # 顯示卡片內容
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align: center;'>{current_word}</h2>", unsafe_allow_html=True)
            # 若當前緩存資料剛好是這個單字，就顯示詳細內容
            if "current_data" in st.session_state and st.session_state.current_data['word'] == current_word:
                card_data = st.session_state
