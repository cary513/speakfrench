import streamlit as st
import openai
import csv
import os
import io
from datetime import datetime
from gtts import gTTS
import base64

# ── Page config ────────────────────────────────────────────────
st.set_page_config(page_title="法文單字學習卡", page_icon="🇫🇷", layout="centered")

st.markdown("""
<style>
    .card { background:#f9f9fb; border:1px solid #e0e0e8; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
    .word-title { font-size:2rem; font-weight:700; color:#1a1a2e; }
    .phonetic  { font-size:1rem; color:#888; margin-bottom:.5rem; }
    .section-label { font-size:.75rem; font-weight:600; letter-spacing:.08em; color:#aaa; text-transform:uppercase; margin-bottom:.25rem; }
    .review-btn  button { background:#fff3cd !important; border:1px solid #ffc107 !important; color:#856404 !important; }
    .learned-btn button { background:#d1e7dd !important; border:1px solid #198754 !important; color:#155724 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar – API Key ───────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.caption("Key 僅存於本次 session，不會被儲存。")
    st.divider()
    st.markdown("**CSV 記錄檔**")
    csv_path = st.text_input("路徑", value="vocab_log.csv")
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button("⬇️ 下載 CSV", f, file_name=csv_path, mime="text/csv")
    st.divider()
    st.markdown("**使用說明**\n1. 輸入 API Key\n2. 輸入單字查詢\n3. 點 🔊 播放發音\n4. 標記複習／學會\n5. Memo 區校正造句")

# ── CSV helpers ────────────────────────────────────────────────
CSV_FIELDS = ["timestamp", "word", "language", "translation", "example_sentence", "status"]

def append_csv(row: dict, path: str):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)

# ── gTTS audio helper ──────────────────────────────────────────
def text_to_audio_b64(text: str, lang: str) -> str:
    lang_map = {"法文": "fr", "英文": "en"}
    tts = gTTS(text=text, lang=lang_map.get(lang, "fr"))
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def audio_html(b64: str) -> str:
    return f'<audio autoplay controls src="data:audio/mp3;base64,{b64}" style="width:100%;margin-top:.5rem"></audio>'

# ── OpenAI helpers ─────────────────────────────────────────────
def get_word_info(word: str, lang: str, client) -> dict:
    prompt = f"""
你是一位法文／英文語言教師。使用者輸入了一個單字，請以 JSON 格式回傳以下欄位（全部用繁體中文說明）：
- "translation": 繁體中文翻譯（簡潔）
- "phonetic": 發音標記（法文用 IPA，英文用 KK 音標）
- "part_of_speech": 詞性（名詞/動詞/形容詞等）
- "example_fr": 一個{"法文" if lang=="法文" else "英文"}例句
- "example_zh": 上述例句的繁體中文翻譯
- "tips": 一句學習小提示（記憶法或常見錯誤）

單字：{word}（{lang}）
只回傳 JSON，不要多餘文字。
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    import json
    return json.loads(resp.choices[0].message.content)

def correct_sentence(word: str, lang: str, user_sentence: str, client) -> str:
    prompt = f"""
使用者嘗試用「{word}」（{lang}）造句如下：
「{user_sentence}」

請：
1. 指出語法或用詞錯誤（若無錯誤也請說明）
2. 提供修正後的句子
3. 簡短解釋修改原因
請用繁體中文回答，排版清楚。
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

# ── Session state init ─────────────────────────────────────────
for key in ["word_info", "current_word", "current_lang", "audio_b64", "correction"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Main UI ────────────────────────────────────────────────────
st.title("🇫🇷 法文單字學習卡")
st.caption("輸入英文或法文單字，即時翻譯、發音、造句練習")

# Input row
col1, col2, col3 = st.columns([3, 1.2, 1])
with col1:
    word_input = st.text_input("輸入單字", placeholder="ex: bonjour / freedom", label_visibility="collapsed")
with col2:
    lang_select = st.selectbox("語言", ["法文", "英文"], label_visibility="collapsed")
with col3:
    search_btn = st.button("🔍 查詢", use_container_width=True)

# ── Query ──────────────────────────────────────────────────────
if search_btn and word_input.strip():
    if not api_key:
        st.error("請先在左側欄填入 OpenAI API Key")
    else:
        with st.spinner("AI 分析中…"):
            try:
                client = openai.OpenAI(api_key=api_key)
                info = get_word_info(word_input.strip(), lang_select, client)
                st.session_state.word_info    = info
                st.session_state.current_word = word_input.strip()
                st.session_state.current_lang = lang_select
                st.session_state.correction   = None
                # Generate audio for example sentence
                example = info.get("example_fr", word_input.strip())
                st.session_state.audio_b64 = text_to_audio_b64(example, lang_select)
            except Exception as e:
                st.error(f"API 錯誤：{e}")

# ── Word Card ──────────────────────────────────────────────────
if st.session_state.word_info:
    info = st.session_state.word_info
    word = st.session_state.current_word
    lang = st.session_state.current_lang

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Header
        st.markdown(f'<div class="word-title">{word}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="phonetic">{info.get("phonetic","")} &nbsp;·&nbsp; {info.get("part_of_speech","")}</div>', unsafe_allow_html=True)

        # Translation
        st.markdown('<div class="section-label">翻譯</div>', unsafe_allow_html=True)
        st.markdown(f"**{info.get('translation','')}**")

        # Audio button
        word_audio = text_to_audio_b64(word, lang)
        if st.button("🔊 播放單字發音"):
            st.markdown(audio_html(word_audio), unsafe_allow_html=True)

        st.divider()

        # Example
        st.markdown('<div class="section-label">例句</div>', unsafe_allow_html=True)
        st.markdown(f"_{info.get('example_fr','')}_")
        st.caption(info.get("example_zh", ""))

        if st.button("🔊 播放例句發音"):
            st.markdown(audio_html(st.session_state.audio_b64), unsafe_allow_html=True)

        st.divider()

        # Tips
        st.markdown('<div class="section-label">學習小提示</div>', unsafe_allow_html=True)
        st.info(info.get("tips", ""))

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Review / Learned buttons ───────────────────────────────
    st.markdown("#### 這個單字你…")
    c1, c2 = st.columns(2)

    def save_word(status):
        append_csv({
            "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "word":             word,
            "language":         lang,
            "translation":      info.get("translation", ""),
            "example_sentence": info.get("example_fr", ""),
            "status":           status,
        }, csv_path)
        st.toast(f"已記錄為「{status}」✅")

    with c1:
        st.markdown('<div class="review-btn">', unsafe_allow_html=True)
        if st.button("🔄 需要複習", use_container_width=True):
            save_word("複習")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="learned-btn">', unsafe_allow_html=True)
        if st.button("✅ 我學會了", use_container_width=True):
            save_word("學會")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Memo / Sentence Correction ─────────────────────────────
    st.divider()
    st.markdown("#### ✏️ 造句練習（AI 校正）")
    st.caption(f"試著用「{word}」造一個句子，AI 會幫你找出錯誤並修正。")

    user_sentence = st.text_area("你的造句", placeholder=f"ex: Je {word} beaucoup...", height=80)

    if st.button("🤖 請 AI 校正"):
        if not user_sentence.strip():
            st.warning("請先輸入造句")
        elif not api_key:
            st.error("請填入 API Key")
        else:
            with st.spinner("AI 校正中…"):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    st.session_state.correction = correct_sentence(word, lang, user_sentence.strip(), client)
                except Exception as e:
                    st.error(f"API 錯誤：{e}")

    if st.session_state.correction:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**AI 校正結果**")
        st.markdown(st.session_state.correction)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:3rem 0;color:#aaa">
        <div style="font-size:3rem">🇫🇷</div>
        <div style="margin-top:.5rem">輸入單字開始學習</div>
    </div>
    """, unsafe_allow_html=True)
