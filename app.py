import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import create_client, Client
import pandas as pd

# ==========================================
# 1. 頁面與服務初始化
# ==========================================
st.set_page_config(page_title="AI 語言學習分析工具 V2", layout="wide")

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

# ==========================================
# 2. 資料庫核心資料流 (Data Flow)
# ==========================================

# 函式：從 Supabase 載入歷史單字
def load_data_from_supabase():
    try:
        response = supabase.table("vocabulary").select("*").execute()
        data = response.data
        if data:
            st.session_state.review_zone = [item['word'] for item in data if str(item.get('status', '')).strip().lower() == 'review']
            st.session_state.brain_zone = [item['word'] for item in data if str(item.get('status', '')).strip().lower() == 'mastered']
            st.session_state.word_history = [item['word'] for item in data]
        else:
            st.session_state.review_zone = []
            st.session_state.brain_zone = []
            st.session_state.word_history = []
    except Exception as e:
        st.error(f"從雲端載入單字失敗: {e}")

# 函式：儲存新單字至 Supabase
def save_word_to_supabase(data_dict):
    try:
        response = supabase.table("vocabulary").select("word").eq("word", data_dict["word"]).execute()
        if len(response.data) == 0:
            supabase.table("vocabulary").insert(data_dict).execute()
            st.toast(f"✅ {data_dict['word']} 已同步至雲端單字本")
        else:
            st.toast(f"💡 {data_dict['word']} 已在單字本中")
    except Exception as e:
        st.error(f"雲端單字儲存失敗: {e}")

# 函式：更新單字狀態
def update_word_status_in_supabase(word: str, new_status: str):
    try:
        supabase.table("vocabulary").update({"status": new_status}).eq("word", word).execute()
        st.toast(f"雲端同步成功：{word} 移至大腦區 🧠")
    except Exception as e:
        st.error(f"同步狀態失敗: {e}")

# 函式：儲存情境句子到 vocabulary 表格中（將句子當成 word 處理，方便一同納入複習系統）
def save_phrase_to_vocabulary(phrase_dict):
    try:
        # 用句子本身當作唯一值檢查
        response = supabase.table("vocabulary").select("word").eq("word", phrase_dict["word"]).execute()
        if len(response.data) == 0:
            supabase.table("vocabulary").insert(phrase_dict).execute()
            st.toast("📥 句子已成功收藏至【待複習區】！")
            
            # 同步更新本地的暫存狀態，讓側邊欄立刻重新渲染
            if phrase_dict["word"] not in st.session_state.review_zone:
                st.session_state.review_zone.append(phrase_dict["word"])
        else:
            st.toast("💡 這句對話已經在你的收藏庫中囉！")
    except Exception as e:
        st.error(f"收藏句子失敗: {e}")

# --- 初始化 Session State ---
if "word_history" not in st.session_state:
    st.session_state.word_history = []
    st.session_state.review_zone = []
    st.session_state.brain_zone = []
    st.session_state.current_card_index = 0
    load_data_from_supabase()

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

# ==========================================
# 3. 側邊欄 (Sidebar)
# ==========================================
with st.sidebar:
    st.header("📚 知識庫分類")
    
    st.subheader("待複習區 (Review Zone)")
    if not st.session_state.review_zone:
        st.caption("無待複習內容")
    else:
        for word in st.session_state.review_zone:
            # 如果是長句子，縮短顯示避免側邊欄爆掉
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟨 **{display_text}**")
            
    st.markdown("---")
    st.subheader("大腦區 (Mastered)")
    if not st.session_state.brain_zone:
        st.caption("尚未記憶內容")
    else:
        for word in st.session_state.brain_zone:
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟩 **{display_text}**")

# ==========================================
# 4. 主畫面 (Main Content) 三頁籤系統
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔍 單字查詢", "🗂️ 複習卡 (Flashcards)", "🚀 精選情境句型"])

# ---- TAB 1：單字查詢 ----
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

# ---- TAB 2：複習卡 ----
with tab2:
    st.title("🗂️ 複習卡系統")
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！所有單字和句子都已經記住了！")
    else:
        if st.session_state.current_card_index >= len(st.session_state.review_zone):
            st.session_state.current_card_index = 0
            
        current_word = st.session_state.review_zone[st.session_state.current_card_index]
        
        card_data = None
        if "current_data" in st.session_state and st.session_state.current_data['word'] == current_word:
            card_data = st.session_state.current_data
        else:
            try:
                db_res = supabase.table("vocabulary").select("*").eq("word", current_word).execute()
                if db_res.data:
                    card_data = db_res.data[0]
            except Exception:
                pass

        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center; color: #1E3A8A;'>{current_word}</h3>", unsafe_allow_html=True)
            
            if card_data:
                st.markdown(f"<p style='text-align: center;'><strong>/{card_data.get('phonetic', '')}/</strong></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 1.1em;'>{card_data.get('meaning', '')}</p>", unsafe_allow_html=True)
                if card_data.get('example_sentence') and card_data.get('example_sentence') != current_word:
                    st.caption(f"💡 延伸上下文/例句提示：{card_data['example_sentence']}")
            else:
                st.caption("🔍 無法載入詳細釋義，可能為收藏的情境句，可直接滑動複習。")

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
                
                update_word_status_in_supabase(word_to_move, "mastered")
                st.session_state.current_card_index = 0
                st.rerun()

# ---- TAB 3：新開發！精選情境句型區 (核心功能升級) ----
with tab3:
    CATEGORIES = {
        "💼 職場用語": "workplace",
        "☕ 日常生活": "daily",
        "✈️ 機場通關": "airport",
        "🛍️ 購物消費": "shopping",
        "🍽️ 餐廳點菜": "restaurant",
        "🙋 自我介紹": "self_intro",
        "🍻 交友與價值觀": "social"
    }

    # 門檻機制：填寫個人 profile 檔案
    if st.session_state.user_profile is None:
        st.subheader("🚀 建構你的 AI 個人化語言模型")
        st.info("請花 10 秒填寫你的背景，AI 將為你過濾掉僵硬的教科書台詞，直接精選出符合你特質的法文流行語！")
        
        with st.form("profile_form_upgrade"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("如何稱呼您？ (Name)", placeholder="例如: Cary")
                level = st.selectbox("目前法語程度 (Level)", ["入門級 (A1)", "初級實用 (A2)", "中級流利 (B1)", "進階商務 (B2)"])
            with c2:
                goal = st.text_input("核心學習目標 (Goal)", placeholder="例如: 想在法國咖啡廳工作、日常數位遊牧社交")
            
            interests = st.text_area("個人興趣、休閒與獨特價值觀 (Interests)", placeholder="例如: 喜歡爬山、自由潛水、滑板、聽 R&B 音樂，養了一隻五年的貓")
            
            submit_btn = st.form_submit_button("開通高擬真情境大廳 🔓")
            if submit_btn:
                if name and goal:
                    st.session_state.user_profile = {
                        "display_name": name,
                        "current_level": level,
                        "learning_goal": goal,
                        "interests": interests
                    }
                    st.success("建模完成！已解鎖道地句型庫。")
                    st.rerun()
                else:
                    st.error("請填寫姓名與學習目標，讓 AI 能正常對接您的背景。")
    
    # 填寫完成後展現的大廳
    else:
        profile = st.session_state.user_profile
        st.subheader(f"🎯 專屬法語場景大廳 — 正在為 `{profile['display_name']}` 提供客製化流利方案")
        
        if st.button("🔄 重設/修改個人檔案", key="reset_profile_btn"):
            st.session_state.user_profile = None
            st.session_state.selected_category = None
            st.rerun()
            
        st.markdown("---")
        st.write("請選擇您目前希望應對的實戰場景：")
        
        # 建立按鈕網格
        cols = st.columns(4)
        for i, (label, key) in enumerate(CATEGORIES.items()):
            with cols[i % 4]:
                if st.button(label, use_container_width=True, key=f"btn_room_{key}"):
                    st.session_state.selected_category = (label, key)
        
        st.markdown("---")
        
        # 渲染生成的情境句子
        if st.session_state.selected_category:
            cat_label, cat_key = st.session_state.selected_category
            st.markdown(f"### ✨ 當前探索場景：{cat_label}")
            
            # 動態向修改後的 ai_service 撈取客製化句子
            with st.spinner("AI 母語專家正在根據你的背景和特質，篩選巴黎當地的口語密碼..."):
                phrases_list = ai_service.generate_phrases_by_category(cat_key, profile)
            
            if phrases_list:
                for idx, item in enumerate(phrases_list):
                    with st.container(border=True):
                        col_text, col_audio, col_add = st.columns([4, 1, 1])
                        with col_text:
                            st.subheader(item.get("french_sentence", ""))
                            st.caption(f"🎙️ 口音中文擬真：{item.get('phonetic', '')}")
                            st.markdown(f"💡 **中文精準含意：** {item.get('chinese_translation', '')}")
                        
                        with col_audio:
                            # 串接音訊引擎，讓情境句也能直接聽發音
                            try:
                                audio_stream = nlp_engine.generate_audio(item.get("french_sentence", ""), lang="fr")
                                if audio_stream:
                                    st.audio(audio_stream, format='audio/mp3', key=f"audio_phrase_{cat_key}_{idx}")
                            except Exception:
                                st.caption("語音加載中...")
                                
                        with col_add:
                            # 一鍵同步到 Supabase，使其可以被放進複習卡系統
                            if st.button("📥 收藏複習", key=f"save_phrase_btn_{cat_key}_{idx}", use_container_width=True):
                                save_phrase_to_vocabulary({
                                    "word": item.get("french_sentence", ""),
                                    "lang_code": "fr",
                                    "phonetic": item.get("phonetic", ""),
                                    "meaning": item.get("chinese_translation", ""),
                                    "example_sentence": item.get("cultural_tip", ""),
                                    "status": "review"
                                })
                        
                        st.info(f"💬 **現代法文潛規則 (Cultural Tip)：**\n{item.get('cultural_tip', '')}")
            else:
                st.warning("此類別生成失敗，請稍後重試。")
