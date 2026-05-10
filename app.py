import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine

# 1. 頁面初始化
st.set_page_config(page_title="AI 語言學習分析工具 V2", layout="wide")

@st.cache_resource
def get_services():
    ai_service = AIService()
    nlp_engine = NLPEngine()
    return ai_service, nlp_engine

ai_service, nlp_engine = get_services()

# 2. 初始化 Session State 狀態管理
if "word_history" not in st.session_state:
    st.session_state.word_history = []
if "review_zone" not in st.session_state:
    st.session_state.review_zone = []
if "brain_zone" not in st.session_state:
    st.session_state.brain_zone = []
if "current_card_index" not in st.session_state:
    st.session_state.current_card_index = 0

# ==========================================
# 3. 側邊欄 (Sidebar) - 知識庫管理
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
# 4. 主畫面 (Main Content) - Tabs 切換
# ==========================================
tab1, tab2 = st.tabs(["🔍 單字查詢", "🗂️ 複習卡 (Flashcards)"])

# 頁籤 1：單字查詢
with tab1:
    st.title("單字分析與探索")
    word_input = st.text_input("輸入單字（自動偵測英/法文）", placeholder="例如: innovation 或 bonjour")
    
    if st.button("開始分析"):
        if word_input:
            with st.spinner("AI 正在建模中..."):
                data = ai_service.get_word_analysis(word_input)
                
            if data:
                st.session_state.current_data = data
                
                # 儲存至歷史紀錄與待複習區
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)
                    
                st.rerun()
            else:
                st.error("分析失敗，請檢查網路或 API 配置。")

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
                    st.audio(audio_stream, format='audio/mp3')
                except Exception as e:
                    st.warning("語音生成暫時無法使用")

            st.write(f"**意思：** {data['meaning']}")
            st.markdown("---")
            st.write("**例句演示：**")
            st.info(f"{data['example_sentence']}\n\n*{data['sentence_translation']}*")

# 頁籤 2：複習卡
with tab2:
    st.title("🗂️ 複習卡系統")
    
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！所有單字都已經記住了！")
    else:
        # 確保 index 在合理範圍
        if st.session_state.current_card_index >= len(st.session_state.review_zone):
            st.session_state.current_card_index = 0
            
        current_word = st.session_state.review_zone[st.session_state.current_card_index]
        
        # 取得單字的快取資料（若有）
        card_data = None
        if "current_data" in st.session_state and st.session_state.current_data['word'] == current_word:
            card_data = st.session_state.current_data
        
        # 繪製卡片 UI
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align: center;'>{current_word}</h2>", unsafe_allow_html=True)
            if card_data:
                st.markdown(f"<p style='text-align: center;'><strong>/{card_data['phonetic']}/</strong></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>{card_data['meaning']}</p>", unsafe_allow_html=True)
            else:
                st.caption("請先查詢該單字以載入詳細釋義")
                
        # 模擬左右滑動按鈕
        col_left, _, col_right = st.columns([1, 2, 1])
        with col_left:
            if st.button("👈 左滑：待複習", use_container_width=True):
                # 留在 Review Zone，跳到下一個
                st.session_state.current_card_index += 1
                if st.session_state.current_card_index >= len(st.session_state.review_zone):
                    st.session_state.current_card_index = 0
                st.rerun()
                
        with col_right:
            if st.button("👉 右滑：已記憶", use_container_width=True):
                # 移動至大腦區 (Brain Zone)
                word_to_move = st.session_state.review_zone.pop(st.session_state.current_card_index)
                if word_to_move not in st.session_state.brain_zone:
                    st.session_state.brain_zone.append(word_to_move)
                
                # 重置 Index
                st.session_state.current_card_index = 0
                st.rerun()
