import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import create_client, Client
import pandas as pd

# ==========================================
# 1. 頁面與服務初始化 (Initialization)
# ==========================================
st.set_page_config(page_title="AI 語言學習分析工具 V2", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    """初始化 Supabase 客戶端"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

@st.cache_resource
def get_services():
    """初始化 AI 與 NLP 引擎"""
    ai_service = AIService()
    nlp_engine = NLPEngine()
    return ai_service, nlp_engine

ai_service, nlp_engine = get_services()

# ==========================================
# 2. 資料庫核心資料流 (Data Flow & Persistence)
# ==========================================

def load_data_from_supabase():
    """從 Supabase 載入歷史單字與複習卡狀態"""
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

def save_word_to_supabase(data_dict):
    """儲存新單字至 Supabase 歷史清單"""
    try:
        response = supabase.table("vocabulary").select("word").eq("word", data_dict["word"]).execute()
        if len(response.data) == 0:
            supabase.table("vocabulary").insert(data_dict).execute()
            st.toast(f"✅ {data_dict['word']} 已同步至雲端單字本")
        else:
            st.toast(f"💡 {data_dict['word']} 已在單字本中")
    except Exception as e:
        st.error(f"雲端單字儲存失敗: {e}")

def update_word_status_in_supabase(word: str, new_status: str):
    """更新單字或句子在複習卡系統中的狀態"""
    try:
        supabase.table("vocabulary").update({"status": new_status}).eq("word", word).execute()
        st.toast(f"雲端同步成功：{word} 狀態已更新 🧠")
    except Exception as e:
        st.error(f"同步狀態失敗: {e}")

def save_profile_to_supabase(profile_dict):
    """
    🎯 核心修正：防禦型寫入機制。
    先強制 insert 確保完全乾淨的資料庫能成功接收首筆資料，
    並在背景清除舊 id 舊設定，徹底打通空表寫入失敗的逻辑卡點。
    """
    try:
        insert_res = supabase.table("user_profile").insert(profile_dict).execute()
        if insert_res.data:
            st.toast("🎯 個人建模設定已永久保存至雲端！")
            # 背景保持單一用戶最新檔案狀態
            new_id = insert_res.data[0].get("id")
            if new_id:
                supabase.table("user_profile").delete().neq("id", new_id).execute()
        else:
            st.error("❌ 寫入成功但未回傳確認資料，請檢查 Supabase 設定。")
    except Exception as e:
        st.error(f"⚠️ 雲端設定儲存失敗 (請確認 RLS 是否關閉): {e}")

def load_profile_from_supabase():
    """開機時自動從雲端撈取個人設定"""
    try:
        response = supabase.table("user_profile").select("*").limit(1).execute()
        if response.data:
            st.session_state.user_profile = response.data[0]
        else:
            st.session_state.user_profile = None
    except Exception as e:
        st.session_state.user_profile = None

def save_phrase_to_vocabulary(phrase_dict):
    """將收藏的情境句子包裝存入 vocabulary 表，完美整合進現有卡片系統"""
    try:
        response = supabase.table("vocabulary").select("word").eq("word", phrase_dict["word"]).execute()
        if len(response.data) == 0:
            supabase.table("vocabulary").insert(phrase_dict).execute()
            st.toast("📥 實戰對話已成功收藏至【待複習區】！")
            
            # 即時渲染：讓側邊欄與暫存區不需要重新整理便同步更新
            if phrase_dict["word"] not in st.session_state.review_zone:
                st.session_state.review_zone.append(phrase_dict["word"])
        else:
            # 如果原本就以範本存在，則更新狀態為 review，直接啟用複習
            supabase.table("vocabulary").update({"status": "review"}).eq("word", phrase_dict["word"]).execute()
            st.toast("📥 實戰對話已同步移入【待複習區】！")
            if phrase_dict["word"] not in st.session_state.review_zone:
                st.session_state.review_zone.append(phrase_dict["word"])
    except Exception as e:
        st.error(f"收藏對話失敗: {e}")

def auto_save_generated_phrases_to_db(phrases_list):
    """
    ⚡ 雲端持久化升級：
    當 Gemini 生成最新精選情境時，自動在背景以 'scenarios' 狀態將句子落庫，
    確保重整網頁不消失，且不污染使用者本人的待複習清單！
    """
    try:
        for item in phrases_list:
            sentence = item.get("french_sentence", "")
            if sentence:
                res = supabase.table("vocabulary").select("word").eq("word", sentence).execute()
                if len(res.data) == 0:
                    supabase.table("vocabulary").insert({
                        "word": sentence,
                        "lang_code": "fr",
                        "phonetic": item.get("phonetic", ""),
                        "meaning": item.get("chinese_translation", ""),
                        "example_sentence": item.get("cultural_tip", ""),
                        "status": "scenarios" 
                    }).execute()
    except Exception as e:
        pass

# --- 核心開機狀態檢查與初始化 ---
if "word_history" not in st.session_state:
    st.session_state.word_history = []
    st.session_state.review_zone = []
    st.session_state.brain_zone = []
    st.session_state.current_card_index = 0
    
    # 執行資料庫數據雙向同步
    load_data_from_supabase()
    load_profile_from_supabase()

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

# ==========================================
# 3. 介面側邊欄 (Sidebar Widget)
# ==========================================
with st.sidebar:
    st.header("📚 知識庫分類看板")
    
    st.subheader("待複習區 (Review Zone)")
    if not st.session_state.review_zone:
        st.caption("無待複習內容")
    else:
        for word in st.session_state.review_zone:
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟨 **{display_text}**")
            
    st.markdown("---")
    st.subheader("大腦記憶區 (Mastered)")
    if not st.session_state.brain_zone:
        st.caption("尚未有記憶完成的單字")
    else:
        for word in st.session_state.brain_zone:
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟩 **{display_text}**")

# ==========================================
# 4. 主畫面 (Main Application Workspace)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔍 單字查詢", "🗂️ 複習卡 (Flashcards)", "🚀 精選情境句型"])

# ---- TAB 1：單字查詢分析 ----
with tab1:
    st.title("單字多維度分析探索")
    word_input = st.text_input("輸入單字（自動辨識英文/法文）", placeholder="例如: l'innovation", key="main_input")
    
    if st.button("開始分析", key="analyze_btn"):
        if word_input:
            with st.spinner("AI 專家正在進行詞彙建模..."):
                data = ai_service.get_word_analysis(word_input)
                
            if data:
                st.session_state.current_data = data
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                if word_input not in st.session_state.review_zone and word_input not in st.session_state.brain_zone:
                    st.session_state.review_zone.append(word_input)
                
                # 同步到 Supabase
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
                st.error("單字分析失敗，請檢查 API 金鑰或網路連線。")

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
                    st.warning("語音生成系統暫時離線")
            
            st.write(f"**核心釋義：** {data['meaning']}")
            st.markdown("---")
            st.write("**語境例句：**")
            st.info(f"{data['example_sentence']}\n\n*{data.get('sentence_translation', '')}*")

# ---- TAB 2：複習卡系統 (字卡輪播) ----
with tab2:
    st.title("🗂️ 高擬真記憶字卡")
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！您目前沒有任何待複習的單字或場景對話！")
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
                    st.caption(f"💡 上下文與潛規則提示：{card_data['example_sentence']}")
            else:
                st.caption("🔍 情境收藏對話，可直接點選滑動按鈕進行分類記憶。")

        col_left, _, col_right = st.columns([1, 2, 1])
        with col_left:
            if st.button("👈 左滑：留著複習", use_container_width=True, key="left_swipe_btn"):
                st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(st.session_state.review_zone)
                st.rerun()
        with col_right:
            if st.button("👉 右滑：完全記住", use_container_width=True, key="right_swipe_btn"):
                word_to_move = st.session_state.review_zone.pop(st.session_state.current_card_index)
                if word_to_move not in st.session_state.brain_zone:
                    st.session_state.brain_zone.append(word_to_move)
                
                # 同步更新 Supabase 資料庫中的狀態為 mastered
                update_word_status_in_supabase(word_to_move, "mastered")
                st.session_state.current_card_index = 0
                st.rerun()

# ---- TAB 3：精選情境句型區 (新功能上線) ----
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

    # 驗證機制：若雲端與本地皆無設定，引導填寫個人化 Profile
    if st.session_state.user_profile is None:
        st.subheader("🚀 客製化您的 AI 個人化法語大腦")
        st.info("請填寫您的基礎實戰背景，AI 專家將自動為您屏蔽死板台詞，生成貼合您特質的巴黎口語！")
        
        with st.form("profile_form_upgrade"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("如何稱呼您？", placeholder="例如: Cary")
                level = st.selectbox("目前法語程度", ["入門級 (A1)", "初級實用 (A2)", "中級流利 (B1)", "進階商務 (B2)"])
            with c2:
                goal = st.text_input("實戰核心目標", placeholder="例如: 想在法國咖啡廳或麵包店工作、數位遊牧")
            
            interests = st.text_area("個人休閒興趣與文化價值觀", placeholder="例如: 喜歡爬山、自由潛水、滑板、聽 R&B 音樂，有一隻養了五年的貓")
            
            submit_btn = st.form_submit_button("開通高流利度場景大廳 🔓")
            if submit_btn:
                if name and goal:
                    profile_data = {
                        "display_name": name,
                        "current_level": level,
                        "learning_goal": goal,
                        "interests": interests
                    }
                    # 同步寫入記憶體與 Supabase 雲端資料庫
                    st.session_state.user_profile = profile_data
                    save_profile_to_supabase(profile_data)
                    st.success("🎉 個人化檔案建模完成！已成功解鎖實戰大廳。")
                    st.rerun()
                else:
                    st.error("請至少提供您的姓名與核心學習目標。")
    
    # 檔案建立完成，顯示分類互動大廳
    else:
        profile = st.session_state.user_profile
        st.subheader(f"🎯 專屬法語實戰大廳 — 正在為 `{profile['display_name']}` 的大腦進行語境適配")
        
        if st.button("🔄 修改個人檔案設定", key="reset_profile_btn"):
            # 刪除暫存，觸發重新填寫
            st.session_state.user_profile = None
            st.session_state.selected_category = None
            st.rerun()
            
        st.markdown("---")
        st.write("請選擇您目前希望重點攻克的法語實戰情境：")
        
        # 打造 4 欄按鈕矩陣佈局 (UI/UX 互動改進)
        cols = st.columns(4)
        for i, (label, key) in enumerate(CATEGORIES.items()):
            with cols[i % 4]:
                if st.button(label, use_container_width=True, key=f"btn_room_{key}"):
                    st.session_state.selected_category = (label, key)
        
        st.markdown("---")
        
        # 動態撈取/生成高度客製化的地道句子
        if st.session_state.selected_category:
            cat_label, cat_key = st.session_state.selected_category
            st.markdown(f"### ✨ 當前探索場景：{cat_label}")
            
            phrases_list = []
            cache_key = f"cache_phrases_{cat_key}"
            
            # ---- 🛡️ 雙軌快取儲存機制：記憶體快取 + 雲端自動落庫 ----
            if cache_key not in st.session_state:
                with st.spinner("AI 專家正串接巴黎當地的口語數據庫，為你篩選核心對話..."):
                    phrases_list = ai_service.generate_phrases_by_category(cat_key, profile)
                    st.session_state[cache_key] = phrases_list
                    
                    # 核心優化：生成完成後，立刻自動儲存在背景 Supabase 數據表，保障重整不蒸發
                    auto_save_generated_phrases_to_db(phrases_list)
            else:
                # 記憶體命中，0.1秒秒出
                phrases_list = st.session_state[cache_key]
            
            if phrases_list:
                for idx, item in enumerate(phrases_list):
                    with st.container(border=True):
                        col_text, col_audio, col_add = st.columns([4, 1, 1])
                        with col_text:
                            st.subheader(item.get("french_sentence", ""))
                            st.caption(f"🎙️ 發音擬真暗示：{item.get('phonetic', '')}")
                            st.markdown(f"💡 **中文精準翻譯：** {item.get('chinese_translation', '')}")
                        
                        with col_audio:
                            # ---- 🎙️ 語音組件重構：防禦型防撞 Key & 降級機制 ----
                            try:
                                sentence_text = item.get("french_sentence", "")
                                if sentence_text:
                                    unique_audio_key = f"audio_phrase_{cat_key}_{idx}_{len(sentence_text)}"
                                    audio_stream = nlp_engine.generate_audio(sentence_text, lang="fr")
                                    
                                    if audio_stream:
                                        st.audio(audio_stream, format='audio/mp3', key=unique_audio_key)
                                    else:
                                        st.caption("🔇 語音流回傳為空")
                                else:
                                    st.caption("📭 找不到法文字串")
                            except Exception:
                                st.caption("🎵 點擊側欄可重新載入語音")
                                
                        with col_add:
                            # 一鍵同步收藏到 vocabulary 表格
                            if st.button("📥 收藏複習", key=f"save_phrase_btn_{cat_key}_{idx}", use_container_width=True):
                                save_phrase_to_vocabulary({
                                    "word": item.get("french_sentence", ""),
                                    "lang_code": "fr",
                                    "phonetic": item.get("phonetic", ""),
                                    "meaning": item.get("chinese_translation", ""),
                                    "example_sentence": item.get("cultural_tip", ""), # 將潛規則細節存入，卡片複習時能看到
                                    "status": "review"
                                })
                        
                        st.info(f"💬 **現代法文潛規則 (Cultural Tip)：**\n{item.get('cultural_tip', '')}")
            else:
                st.warning("此分類目前無法取得即時生成資料，請稍後重試。")
