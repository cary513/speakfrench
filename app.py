import streamlit as st
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import create_client, Client

# ==========================================
# 1. 頁面與服務初始化 (Initialization)
# ==========================================
st.set_page_config(page_title="AI語言天才V2", layout="wide")

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
    """
    從 Supabase 載入歷史單字與複習卡狀態
    🎯 核心重構：改為直接存儲完整字典物件，確保單字與句子能完美混編複習
    """
    try:
        response = supabase.table("vocabulary").select("*").execute()
        data = response.data
        if data:
            # 將完整 dict 物件直接分流存入記憶體快取
            st.session_state.review_zone = [item for item in data if str(item.get('status', '')).strip().lower() == 'review']
            st.session_state.brain_zone = [item for item in data if str(item.get('status', '')).strip().lower() == 'mastered']
            st.session_state.word_history = [item['word'] for item in data]
        else:
            st.session_state.review_zone = []
            st.session_state.brain_zone = []
            st.session_state.word_history = []
    except Exception as e:
        st.error(f"從雲端載入單字失敗: {e}")

def save_word_to_supabase(data_dict):
    """儲存新單字至 Supabase 歷史清單，並同步更新記憶體內部的物件格式"""
    try:
        response = supabase.table("vocabulary").select("*").eq("word", data_dict["word"]).execute()
        if len(response.data) == 0:
            insert_res = supabase.table("vocabulary").insert(data_dict).execute()
            st.toast(f"✅ {data_dict['word']} 已同步至雲端單字本")
            if insert_res.data and (data_dict["word"] not in [r.get("word") for r in st.session_state.review_zone]):
                st.session_state.review_zone.append(insert_res.data[0])
        else:
            st.toast(f"💡 {data_dict['word']} 已在單字本中")
            # 確保狀態正確
            supabase.table("vocabulary").update({"status": "review"}).eq("word", data_dict["word"]).execute()
            if data_dict["word"] not in [r.get("word") for r in st.session_state.review_zone]:
                st.session_state.review_zone.append(response.data[0])
    except Exception as e:
        st.error(f"雲端單字儲存失敗: {e}")

def update_word_status_in_supabase(word: str, new_status: str):
    """更新單字或句子在複習卡系統中的狀態"""
    try:
        supabase.table("vocabulary").update({"status": new_status}).eq("word", word).execute()
        st.toast(f"雲端同步成功：狀態已更新 🧠")
    except Exception as e:
        st.error(f"同步狀態失敗: {e}")

def save_profile_to_supabase(profile_dict):
    """防禦型個人設定寫入機制：打通空表寫入失敗的邏輯卡點"""
    try:
        insert_res = supabase.table("user_profile").insert(profile_dict).execute()
        if insert_res.data:
            st.toast("🎯 個人建模設定已永久保存至雲端！")
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
    """
    🎯 核心重構：收藏對話時，完整將資料庫產出的最新物件塞進複習區，
    徹底解決單字與句子長短不一導致的卡片空白問題。
    """
    try:
        response = supabase.table("vocabulary").select("*").eq("word", phrase_dict["word"]).execute()
        if len(response.data) == 0:
            insert_res = supabase.table("vocabulary").insert(phrase_dict).execute()
            st.toast("📥 實戰對話已成功收藏至【待複習區】！")
            if insert_res.data:
                st.session_state.review_zone.append(insert_res.data[0])
        else:
            supabase.table("vocabulary").update({"status": "review"}).eq("word", phrase_dict["word"]).execute()
            st.toast("📥 實戰對話已同步移入【待複習區】！")
            # 避免重複添加，先篩選掉舊的再加新的
            st.session_state.review_zone = [item for item in st.session_state.review_zone if item['word'] != phrase_dict["word"]]
            st.session_state.review_zone.append(response.data[0])
    except Exception as e:
        st.error(f"收藏對話失敗 (請確認 vocabulary 表的 RLS 是否已關閉): {e}")

def auto_save_generated_phrases_to_db(phrases_list):
    """
    ⚡ 雲端持久化升級：加上強制去重與 AI 隨機大小寫欄位自動模糊相容適配機制，
    徹底從源頭擊碎「生成句子全部卡在同一句」的系統 bug。
    """
    try:
        if not phrases_list:
            return
        for item in phrases_list:
            # 模糊相容大小寫，防止 AI 隨機調整 JSON 鍵值導致抓到空字串
            sentence = item.get("french_sentence") or item.get("French_sentence") or ""
            phonetic = item.get("phonetic") or item.get("Phonetic") or ""
            meaning = item.get("chinese_translation") or item.get("meaning") or ""
            tip = item.get("cultural_tip") or item.get("example_sentence") or ""
            
            if sentence:
                res = supabase.table("vocabulary").select("word").eq("word", sentence.strip()).execute()
                if len(res.data) == 0:
                    supabase.table("vocabulary").insert({
                        "word": sentence.strip(),
                        "lang_code": "fr",
                        "phonetic": phonetic,
                        "meaning": meaning,
                        "example_sentence": tip,
                        "status": "scenarios" 
                    }).execute()
    except Exception:
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
        for item in st.session_state.review_zone:
            word = item.get("word", "")
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟨 **{display_text}**")
            
    st.markdown("---")
    st.subheader("大腦記憶區 (Mastered)")
    if not st.session_state.brain_zone:
        st.caption("尚未有記憶完成的單字")
    else:
        for item in st.session_state.brain_zone:
            word = item.get("word", "")
            display_text = word if len(word) < 15 else f"{word[:15]}..."
            st.markdown(f"🟩 **{display_text}**")

# ==========================================
# 4. 主畫面 (Main Application Workspace)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 單字查詢", 
    "🗂️ 複習卡 (Flashcards)", 
    "🚀 精選情境句型",
    "📝 A2 刷題"
])

# ---- TAB 1：單字查詢分析 ----
with tab1:
    st.title("語言小天才")
    word_input = st.text_input("輸入單字（自動辨識英文/法文）", placeholder="例如: l'innovation", key="main_input")
    
    if st.button("開始分析", key="analyze_btn"):
        if word_input:
            # ---- 🚀 PM 額度防禦：如果以前查過這個字，直接從快取或資料庫拿，不扣 Gemini API 額度 ----
            word_cache_key = f"word_cache_{word_input.strip().lower()}"
            
            with st.spinner("AI 專家正在進行詞彙建模..."):
                data = None
                # 1. 優先檢查本地 Session 快取
                if word_cache_key in st.session_state:
                    data = st.session_state[word_cache_key]
                else:
                    # 2. 次要檢查 Supabase 雲端歷史紀錄
                    try:
                        db_res = supabase.table("vocabulary").select("*").eq("word", word_input.strip()).execute()
                        if db_res.data:
                            db_item = db_res.data[0]
                            data = {
                                "word": db_item["word"],
                                "lang_code": db_item["lang_code"],
                                "phonetic": db_item["phonetic"],
                                "meaning": db_item["meaning"],
                                "example_sentence": db_item["example_sentence"],
                                "sentence_translation": "" 
                            }
                            st.session_state[word_cache_key] = data
                    except Exception:
                        pass

                # 3. 雙軌快取皆未命中，最後才請求 Gemini (極大化節省免費額度)
                # 🔥 防禦型新寫法：若 API 爆量，優雅提示用戶，中斷線程不讓網頁大崩潰
                if not data:
                    try:
                        data = ai_service.get_word_analysis(word_input)
                        if data:
                            st.session_state[word_cache_key] = data
                    except Exception as gemini_err:
                        st.error("⚠️ Google AI 目前非常忙碌（免費額度已達每分鐘上限）。請稍候 1 分鐘，或者切換到「精選情境句型」點擊已有場景進行複習！")
                        st.stop()

            # ---- 4. 確保資料取得後，執行雲端落庫與前端狀態更新 ----
            if data:
                st.session_state.current_data = data
                if word_input not in st.session_state.word_history:
                    st.session_state.word_history.append(word_input)
                
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
                st.error("單字分析失敗，可能是 Google AI 額度已達上限，請稍候 1 分鐘再試。")

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
            
            # ========== 語境例句 + 點擊單字顯示註解 ==========
            st.write("**語境例句：**（點擊下方單字可查看詳細註解）")
            st.info(f"{data['example_sentence']}\n\n*{data.get('sentence_translation', '')}*")

            # 🔊 整句發音
            if data.get('example_sentence'):
                if st.button("🔊 播放整句發音", key="example_sentence_audio"):
                    with st.spinner("🎵 調音中..."):
                        try:
                            audio_stream = nlp_engine.generate_audio(
                                data['example_sentence'],
                                lang=data.get('lang_code', 'fr')
                            )
                            if audio_stream:
                                st.audio(audio_stream, format='audio/mp3')
                            else:
                                st.caption("🔇 語音流為空")
                        except Exception:
                            st.warning("語音生成系統暫時離線")

            # 把例句拆成單字做成可點擊按鈕
            import re
            sentence = data.get('example_sentence', '')
            words = re.findall(r"\b[\w'-]+\b", sentence)
            
            if words:
                st.caption("點擊單字查看解釋：")
                cols = st.columns(min(len(words), 6))
                for i, w in enumerate(words):
                    with cols[i % 6]:
                        if st.button(w, key=f"click_word_{data['word']}_{i}_{w}"):
                            st.session_state.clicked_explain_word = w
                            st.session_state.clicked_explain_lang = data.get('lang_code', 'fr')

            # 顯示被點擊單字的藍色註解框
            if "clicked_explain_word" in st.session_state:
                explain_word = st.session_state.clicked_explain_word
                explain_lang = st.session_state.get('clicked_explain_lang', 'fr')
                
                cache_key = f"word_cache_{explain_word.strip().lower()}"
                explain_data = st.session_state.get(cache_key)
                
                # 1. Session 沒有 → 先查 Supabase
                if not explain_data:
                    try:
                        db_res = supabase.table("vocabulary").select("*").eq("word", explain_word.strip()).execute()
                        if db_res.data:
                            db_item = db_res.data[0]
                            explain_data = {
                                "word": db_item["word"],
                                "lang_code": db_item.get("lang_code", "fr"),
                                "phonetic": db_item.get("phonetic", ""),
                                "meaning": db_item.get("meaning", ""),
                                "example_sentence": db_item.get("example_sentence", ""),
                                "sentence_translation": ""
                            }
                            st.session_state[cache_key] = explain_data
                    except Exception:
                        pass
                
                # 2. 還是沒有 → 才呼叫 Gemini
                if not explain_data:
                    with st.spinner(f"正在分析「{explain_word}」..."):
                        try:
                            explain_data = ai_service.get_word_analysis(explain_word)
                            if explain_data:
                                st.session_state[cache_key] = explain_data
                                # 同步存進 Supabase
                                save_word_to_supabase({
                                    "word": explain_data['word'],
                                    "lang_code": explain_data['lang_code'],
                                    "phonetic": explain_data['phonetic'],
                                    "meaning": explain_data['meaning'],
                                    "example_sentence": explain_data['example_sentence'],
                                    "status": "review"
                                })
                        except Exception:
                            explain_data = None
                
                # 顯示藍色註解框
                if explain_data:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #3B82F6;
                            color: white;
                            padding: 14px 18px;
                            border-radius: 12px;
                            margin-top: 12px;
                            line-height: 1.6;
                            font-size: 15px;
                        ">
                            <strong style="font-size:17px;">{explain_data['word']}</strong><br>
                            {explain_data['meaning']}<br><br>
                            <span style="opacity:0.9;">例句用法參考：{explain_data.get('example_sentence', '')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    if st.button(f"🔊 播放「{explain_word}」發音", key=f"audio_explain_{explain_word}"):
                        try:
                            audio_stream = nlp_engine.generate_audio(explain_word, lang=explain_lang)
                            if audio_stream:
                                st.audio(audio_stream, format='audio/mp3')
                        except Exception:
                            st.warning("語音暫時無法播放")
                else:
                    st.warning(f"無法取得「{explain_word}」的解釋，請稍後再試。")     
# ---- TAB 2：複婚卡系統 (字卡輪播 - 單字與句子大混編) ----
with tab2:
    st.title("🗂️ 高擬真記憶字卡 (單字/情境混合複習大腦)")
    
    if not st.session_state.review_zone:
        st.success("🎉 太棒了！您目前沒有任何待複習的單字或場景對話！")
    else:
        if st.session_state.current_card_index >= len(st.session_state.review_zone):
            st.session_state.current_card_index = 0
            
        current_card = st.session_state.review_zone[st.session_state.current_card_index]
        current_word = current_card.get("word", "")

        with st.container(border=True):
            font_size = "22px" if len(current_word) > 20 else "34px"
            st.markdown(f"<h3 style='text-align: center; color: #1E3A8A; font-size: {font_size};'>{current_word}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'><strong>/{current_card.get('phonetic', '')}/</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: #374151;'>{current_card.get('meaning', '')}</p>", unsafe_allow_html=True)
            
            if current_card.get('example_sentence'):
                st.info(f"💡 上下文與潛規則提示：\n{current_card['example_sentence']}")

            c_audio, _ = st.columns([1, 4])
            with c_audio:
                if st.button("🔊 播放發音", key=f"audio_card_{st.session_state.current_card_index}"):
                    with st.spinner("🎵 調音中..."):
                        try:
                            audio_stream = nlp_engine.generate_audio(current_word, lang=current_card.get('lang_code', 'fr'))
                            if audio_stream:
                                st.audio(audio_stream, format='audio/mp3')
                        except Exception:
                            st.error("語音生成失敗")

        col_left, _, col_right = st.columns([1, 2, 1])
        with col_left:
            if st.button("👈 左滑：留著複習", use_container_width=True, key="left_swipe_btn"):
                st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(st.session_state.review_zone)
                st.rerun()
        with col_right:
            if st.button("👉 右滑：完全記住", use_container_width=True, key="right_swipe_btn"):
                card_to_move = st.session_state.review_zone.pop(st.session_state.current_card_index)
                if card_to_move['word'] not in [b.get('word') for b in st.session_state.brain_zone]:
                    st.session_state.brain_zone.append(card_to_move)
                
                update_word_status_in_supabase(card_to_move['word'], "mastered")
                st.session_state.current_card_index = 0
                st.rerun()

# ---- TAB 3：精選情境句型區 ----
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
                    st.session_state.user_profile = profile_data
                    save_profile_to_supabase(profile_data)
                    st.success("🎉 個人化檔案建模完成！已成功解鎖實戰大廳。")
                    st.rerun()
                else:
                    st.error("請至少提供您的姓名與核心學習目標。")
    
    else:
        profile = st.session_state.user_profile
        st.subheader(f"🎯 專屬法語實戰大廳 — 正在為 `{profile['display_name']}` 的大腦進行語境適配")
        
        if st.button("🔄 修改個人檔案設定", key="reset_profile_btn"):
            st.session_state.user_profile = None
            st.session_state.selected_category = None
            st.rerun()
            
        st.markdown("---")
        st.write("請選擇您目前希望重點攻克的法語實戰情境：")
        
        cols = st.columns(4)
        for i, (label, key) in enumerate(CATEGORIES.items()):
            with cols[i % 4]:
                if st.button(label, use_container_width=True, key=f"btn_room_{key}"):
                    st.session_state.selected_category = (label, key)
        
        st.markdown("---")
        
        if st.session_state.selected_category:
            cat_label, cat_key = st.session_state.selected_category
            st.markdown(f"### ✨ 當前探索場景：{cat_label}")
            
            phrases_list = []
            cache_key = f"cache_phrases_{cat_key}"
            
            if cache_key not in st.session_state:
                with st.spinner("AI 專家正串接巴黎當地的口語數據庫，為你篩選核心對話..."):
                    phrases_list = ai_service.generate_phrases_by_category(cat_key, profile)
                    st.session_state[cache_key] = phrases_list
                    auto_save_generated_phrases_to_db(phrases_list)
            else:
                phrases_list = st.session_state[cache_key]
            
            if phrases_list:
                for idx, item in enumerate(phrases_list):
                    # 💡 精準動態相容欄位提取，杜絕 AI 隨機 Key 回傳造成的多排句子完全重疊
                    sentence_text = item.get("french_sentence") or item.get("French_sentence") or f"實戰句型 {idx+1}"
                    phonetic_text = item.get("phonetic") or item.get("Phonetic") or ""
                    translation_text = item.get("chinese_translation") or item.get("meaning") or ""
                    tip_text = item.get("cultural_tip") or item.get("example_sentence") or ""
                    
                    with st.container(border=True):
                        col_text, col_audio, col_add = st.columns([4, 1, 1])
                        with col_text:
                            st.subheader(sentence_text)
                            st.caption(f"🎙️ 發音擬真暗示：{phonetic_text}")
                            st.markdown(f"💡 **中文精準翻譯：** {translation_text}")
                        
                        with col_audio:
                            # 💡 按需動態加載發音按鈕，加上特製 hash 盾牌，確保音訊獨立運作不混淆
                            if st.button("🔊 發音", key=f"speak_btn_{cat_key}_{idx}_{hash(sentence_text)}"):
                                with st.spinner(""):
                                    try:
                                        if sentence_text:
                                            audio_stream = nlp_engine.generate_audio(sentence_text, lang="fr")
                                            if audio_stream:
                                                st.audio(audio_stream, format='audio/mp3')
                                            else:
                                                st.caption("🔇 語音流為空")
                                    except Exception:
                                        st.caption("🎵 語音暫時離線")
                                
                        with col_add:
                            if st.button("📥 收藏複習", key=f"save_phrase_btn_{cat_key}_{idx}_{hash(sentence_text)}", use_container_width=True):
                                save_phrase_to_vocabulary({
                                    "word": sentence_text,
                                    "lang_code": "fr",
                                    "phonetic": phonetic_text,
                                    "meaning": translation_text,
                                    "example_sentence": tip_text, 
                                    "status": "review"
                                })
                        
                        st.info(f"💬 **現代法文潛規則 (Cultural Tip)：**\n{tip_text}")
            else:
                st.warning("此分類目前無法取得即時生成資料，請稍候再試。")

# ---- TAB 4：A2 刷題 ----
with tab4:
    st.title("📝 DELF A2 刷題練習")
    st.caption("目前題庫來自 AI 生成 + 官方風格練習題，可持續擴充")

    # 初始化狀態
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_answered" not in st.session_state:
        st.session_state.quiz_answered = False
    if "quiz_selected_skill" not in st.session_state:
        st.session_state.quiz_selected_skill = "全部"

    # 選擇技能
    skill_options = {
        "全部": None,
        "閱讀 Reading": "reading",
        "聽力 Listening": "listening",
        "寫作 Writing": "writing",
        "口說 Speaking": "speaking"
    }
    
    selected_label = st.selectbox(
        "選擇練習技能",
        options=list(skill_options.keys()),
        key="skill_selector"
    )
    selected_skill = skill_options[selected_label]

    # 載入題目按鈕
    if st.button("開始刷題 / 換一批題目", type="primary"):
        try:
            query = supabase.table("quiz_questions").select("*").eq("is_active", True)
            if selected_skill:
                query = query.eq("skill", selected_skill)
            
            res = query.execute()
            questions = res.data or []
            
            if not questions:
                st.warning("目前這個分類還沒有題目，請先新增題目。")
            else:
                # 簡單隨機抽最多 10 題
                import random
                random.shuffle(questions)
                st.session_state.quiz_questions = questions[:10]
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answered = False
                st.rerun()
        except Exception as e:
            st.error(f"載入題目失敗：{e}")

    # 顯示目前題目
    questions = st.session_state.quiz_questions
    
    if not questions:
        st.info("請先選擇技能並點擊「開始刷題」")
    else:
        current_idx = st.session_state.quiz_index
        
        if current_idx >= len(questions):
            st.success(f"🎉 本輪練習結束！你答對了 {st.session_state.quiz_score} / {len(questions)} 題")
            if st.button("再練一次"):
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answered = False
                st.rerun()
        else:
            q = questions[current_idx]
            
            st.markdown(f"**題目 {current_idx + 1} / {len(questions)}**")
            st.markdown(f"**技能：** {q.get('skill', '')}　|　**主題：** {q.get('topic', '')}")
            st.markdown("---")
            st.write(q.get("question_text", ""))

            # 根據題型顯示作答區
            user_answer = None
            
            if q.get("question_type") == "mcq":
                options = q.get("options") or []
                if isinstance(options, str):
                    import json
                    try:
                        options = json.loads(options)
                    except:
                        options = []
                
                user_answer = st.radio(
                    "請選擇答案：",
                    options=options,
                    key=f"answer_{current_idx}"
                )
            else:
                # 開放題
                user_answer = st.text_area(
                    "請輸入你的回答（寫作/口說可先打字練習）：",
                    key=f"answer_{current_idx}",
                    height=100
                )

            # 提交答案
            if not st.session_state.quiz_answered:
                if st.button("提交答案", key=f"submit_{current_idx}"):
                    st.session_state.quiz_answered = True
                    
                    correct = q.get("correct_answer", "")
                    
                    # 簡單判斷（選擇題較準，開放題只顯示範例）
                    if q.get("question_type") == "mcq":
                        if user_answer == correct:
                            st.session_state.quiz_score += 1
                            st.success("✅ 答對了！")
                        else:
                            st.error(f"❌ 答錯了。正確答案是：{correct}")
                    else:
                        st.info("開放題沒有標準對錯，請參考下方範例與解析。")
                    
                    st.markdown("### 解析")
                    st.write(q.get("explanation", "暫無解析"))
                    
                    if q.get("question_type") != "mcq":
                        st.markdown("**參考答案：**")
                        st.write(correct)
            else:
                # 已經回答過，顯示下一題按鈕
                st.markdown("### 解析")
                st.write(q.get("explanation", "暫無解析"))
                
                if st.button("下一題 →", key=f"next_{current_idx}"):
                    st.session_state.quiz_index += 1
                    st.session_state.quiz_answered = False
                    st.rerun()
