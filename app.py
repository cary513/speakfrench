今天 上午1:03
已貼上文字 (1)(8).txt
文件
請修正語法是否正確

我目前無法讀取這個附件的文字內容。請直接把要檢查的句子貼到聊天室，我會幫你逐句整理成：

原句
修正版
錯誤原因
更自然的表達方式
中文翻譯與發音提示（如果需要）
import calendar
import html
import json
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import Client, create_client

try:
    from streamlit_lottie import st_lottie
except ImportError:
    st_lottie = None


# =========================================================
# 1. App 與既有服務設定
# =========================================================
st.set_page_config(
    page_title="Language Genius",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TAIPEI_TZ = timezone(timedelta(hours=8))
DAILY_GOAL_MINUTES = 12
NAV_ITEMS = ["首頁", "日曆", "複習卡", "A2刷題"]
MOODS = ["很疲累", "有點累", "普通", "不錯", "很棒"]
MOOD_ICONS = ["☹", "🙁", "😐", "🙂", "😄"]
APP_DIR = Path(__file__).resolve().parent
LOTTIE_DIR = APP_DIR / "assets" / "lottie"
LOTTIE_FILES = {
    "idle": "language_genius_cat_under_book_idle.json",
    "learning": "language_genius_cat_plane_learning.json",
    "paused": "language_genius_cat_box_paused.json",
    "completed": "language_genius_cat_celebration_complete.json",
    "results": "language_genius_cat_cup_results.json",
    "loading": "language_genius_cat_stretch_loading.json",
}


@st.cache_resource
def init_supabase() -> Client:
    """沿用原本的 Supabase Secrets 設定。"""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_resource
def get_services():
    """沿用原本的 AI 與 NLP 引擎。"""
    return AIService(), NLPEngine()


supabase = init_supabase()
ai_service, nlp_engine = get_services()


# =========================================================
# 2. 視覺系統
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --lg-bg:#F2F2F4; --lg-surface:#FFFFFF; --lg-text:#171717;
        --lg-muted:#7D818A; --lg-line:#E8E8EA; --lg-orange:#F7A916;
        --lg-orange-soft:#FFF3D7; --lg-shadow:0 12px 34px rgba(24,24,27,.055);
    }
    .stApp { background:var(--lg-bg); color:var(--lg-text); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#FAFAFA; }
    [data-testid="stMainBlockContainer"] {
        max-width:780px; padding-top:2.2rem; padding-bottom:8.5rem;
    }
    h1,h2,h3 { color:var(--lg-text); letter-spacing:-.035em; }
    p,label,[data-testid="stCaptionContainer"] { color:var(--lg-muted); }
    .lg-brand { display:flex; align-items:center; gap:.65rem; margin-bottom:1.8rem; }
    .lg-brand-mark {
        width:34px; height:34px; display:grid; place-items:center;
        border-radius:11px; background:var(--lg-orange); color:#171717; font-size:18px;
    }
    .lg-brand-name { font-weight:750; color:var(--lg-text); }
    .lg-eyebrow { color:#A36A00; font-size:.76rem; font-weight:750; letter-spacing:.12em; }
    .lg-hero-title { font-size:clamp(2rem,6vw,3.2rem); line-height:1.05; margin:.25rem 0 .5rem; }
    .lg-card {
        background:var(--lg-surface); border:1px solid rgba(23,23,23,.035);
        border-radius:22px; padding:24px; margin:18px 0; box-shadow:var(--lg-shadow);
    }
    .lg-stats { display:grid; grid-template-columns:repeat(3,1fr); }
    .lg-stat { text-align:center; padding:8px 14px; }
    .lg-stat + .lg-stat { border-left:1px solid var(--lg-line); }
    .lg-stat-label { color:var(--lg-muted); font-size:.82rem; margin-bottom:.45rem; }
    .lg-stat-value { color:var(--lg-text); font-size:1.65rem; font-weight:780; line-height:1; }
    .lg-stat-unit { color:var(--lg-muted); font-size:.78rem; margin-top:.35rem; }
    .lg-cat-stage { min-height:185px; display:grid; place-items:center; text-align:center; margin:24px 0 12px; }
    .lg-cat { font-size:5.2rem; }
    .lg-book { font-size:5.4rem; margin-top:-3.55rem; position:relative; z-index:2; }
    .lg-celebrate { animation:lg-bounce .9s ease-in-out infinite alternate; }
    @keyframes lg-bounce { from{transform:translateY(8px) rotate(-3deg)} to{transform:translateY(-18px) rotate(3deg)} }
    .lg-log-row {
        display:flex; justify-content:space-between; gap:18px; align-items:flex-start;
        padding:14px 0; border-bottom:1px solid var(--lg-line);
    }
    .lg-log-row:last-child { border-bottom:0; }
    .lg-log-title { color:var(--lg-text); font-weight:680; }
    .lg-log-meta { color:var(--lg-muted); font-size:.84rem; margin-top:.25rem; }
    .lg-pill {
        display:inline-flex; border-radius:999px; background:var(--lg-orange-soft);
        color:#855800; padding:.45rem .8rem; font-size:.78rem; font-weight:680;
    }
    .lg-note { border-left:3px solid var(--lg-orange); padding:.1rem 0 .1rem 1rem; color:var(--lg-muted); }
    .stButton>button,.stFormSubmitButton>button {
        min-height:48px; border-radius:14px; border:1px solid var(--lg-line);
        font-weight:700; box-shadow:none; transition:transform .15s ease;
    }
    .stButton>button:hover,.stFormSubmitButton>button:hover { border-color:var(--lg-orange); transform:translateY(-1px); }
    .stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"] {
        background:var(--lg-orange); color:#171717; border-color:var(--lg-orange);
    }
    [data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div {
        border-radius:15px!important; border-color:var(--lg-line)!important; background:#FFF!important;
    }
    [data-testid="stMetric"] { background:#FFF; border-radius:18px; padding:18px; box-shadow:var(--lg-shadow); }
    div[data-testid="stExpander"] { border:0; border-radius:18px; background:#FFF; box-shadow:var(--lg-shadow); }
    .st-key-bottom_nav {
        position:fixed; z-index:999; left:50%; bottom:18px; transform:translateX(-50%);
        width:min(680px,calc(100vw - 28px)); background:rgba(255,255,255,.94);
        border:1px solid rgba(23,23,23,.06); border-radius:22px; padding:5px 12px;
        box-shadow:0 16px 44px rgba(24,24,27,.16); backdrop-filter:blur(16px);
    }
    .st-key-bottom_nav [data-testid="stRadio"]>label { display:none; }
    .st-key-bottom_nav [data-baseweb="radio"]>div { justify-content:space-around; width:100%; gap:4px; }
    .st-key-bottom_nav label {
        flex:1; justify-content:center; align-items:center; flex-direction:column;
        gap:3px; position:relative; border-radius:0; padding:7px 10px 9px;
        background:transparent!important;
    }
    .st-key-bottom_nav label:has(input:checked) { background:transparent!important; }
    .st-key-bottom_nav label>div:first-child { display:none; }
    .st-key-bottom_nav label::before {
        content:""; display:block; width:25px; height:25px; flex:0 0 25px;
        background:#171717; opacity:.72;
        -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
        -webkit-mask-position:center; mask-position:center;
        -webkit-mask-size:contain; mask-size:contain;
    }
    .st-key-bottom_nav label:nth-of-type(1)::before {
        -webkit-mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+");
        mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+");
    }
    .st-key-bottom_nav label:nth-of-type(2)::before {
        -webkit-mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
        mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
    }
    .st-key-bottom_nav label:nth-of-type(3)::before {
        -webkit-mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg==");
        mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg==");
    }
    .st-key-bottom_nav label:nth-of-type(4)::before {
        -webkit-mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+");
        mask-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+");
    }
    .st-key-bottom_nav label:has(input:checked)::before { opacity:1; }
    .st-key-bottom_nav label:has(input:checked)::after {
        content:""; position:absolute; bottom:2px; width:18px; height:3px;
        border-radius:999px; background:var(--lg-orange);
    }
    .st-key-bottom_nav p { color:#171717; font-size:.72rem; line-height:1; font-weight:650; opacity:.76; }
    .st-key-bottom_nav label:has(input:checked) p { opacity:1; font-weight:750; }
    /* V6: real navigation buttons. No radio input or selection circles. */
    .st-key-bottom_nav [data-testid="stHorizontalBlock"] { gap:0!important; }
    .st-key-bottom_nav [data-testid="column"] { min-width:0!important; }
    .st-key-bottom_nav .stButton { width:100%; }
    .st-key-bottom_nav .stButton>button {
        width:100%; min-width:0; min-height:62px; height:62px;
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        gap:4px; position:relative; padding:5px 2px 8px;
        border:0!important; border-radius:0!important;
        color:#171717!important; background:transparent!important;
        box-shadow:none!important; transform:none!important;
    }
    .st-key-bottom_nav .stButton>button:hover,
    .st-key-bottom_nav .stButton>button:focus,
    .st-key-bottom_nav .stButton>button:active {
        border:0!important; color:#171717!important;
        background:transparent!important; box-shadow:none!important;
        transform:none!important;
    }
    .st-key-bottom_nav .stButton>button::before {
        content:""; display:block; width:25px; height:25px; flex:0 0 25px;
        background:#171717; opacity:.68;
        -webkit-mask-image:var(--nav-icon); mask-image:var(--nav-icon);
        -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
        -webkit-mask-position:center; mask-position:center;
        -webkit-mask-size:contain; mask-size:contain;
    }
    .st-key-bottom_nav .stButton>button p {
        margin:0; color:#171717!important; opacity:.76;
        font-size:.72rem; line-height:1; font-weight:650; white-space:nowrap;
    }
    .st-key-nav_home { --nav-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+"); }
    .st-key-nav_calendar { --nav-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg=="); }
    .st-key-nav_review { --nav-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg=="); }
    .st-key-nav_quiz { --nav-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+"); }
    /* Lottie source images are transparent; keep Streamlit wrappers transparent too. */
    [data-testid="stCustomComponentV1"],
    [data-testid="stCustomComponentV1"]>div,
    iframe[title="streamlit_lottie.st_lottie"] {
        background:transparent!important; border:0!important; box-shadow:none!important;
    }
    @media(max-width:640px) {
        [data-testid="stMainBlockContainer"] { padding:1.25rem 1rem 8rem; }
        .lg-card { padding:20px; } .lg-stat { padding:6px; }
        .lg-stat-value { font-size:1.35rem; } .lg-cat-stage { min-height:155px; }
        .st-key-bottom_nav { bottom:10px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. Session 與資料存取
# =========================================================
def local_today() -> date:
    return datetime.now(TAIPEI_TZ).date()


STATE_DEFAULTS = {
    "active_page":"首頁", "review_zone":[], "brain_zone":[], "word_history":[],
    "current_card_index":0, "user_profile":None, "selected_category":None,
    "timer_status":"idle", "timer_started_at":None, "timer_accumulated_seconds":0.0,
    "daily_logs":{}, "selected_log_date":local_today(), "show_daily_log_form":False,
    "show_monthly_report":False, "quiz_index":0, "quiz_questions":[],
    "quiz_score":0, "quiz_answered":False, "persistence_error":None,
}
for state_key, default_value in STATE_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


def empty_log(target_date: date) -> dict:
    return {
        "study_date":target_date.isoformat(), "study_seconds":0,
        "remembered_cards":0, "quiz_count":0, "mood":"普通", "journal":"",
    }


def get_log(target_date: date | str) -> dict:
    key = target_date if isinstance(target_date, str) else target_date.isoformat()
    if key not in st.session_state.daily_logs:
        st.session_state.daily_logs[key] = empty_log(date.fromisoformat(key))
    return st.session_state.daily_logs[key]


def save_daily_log(log: dict, notify: bool = False) -> bool:
    """同步 Session 與 Supabase，並讀回確認資料真的已寫入。"""
    st.session_state.daily_logs[log["study_date"]] = log.copy()
    payload = {
        "study_date":log["study_date"],
        "study_seconds":int(log.get("study_seconds", 0)),
        "remembered_cards":int(log.get("remembered_cards", 0)),
        "quiz_count":int(log.get("quiz_count", 0)),
        "mood":log.get("mood", "普通"), "journal":log.get("journal", ""),
        "updated_at":datetime.now(TAIPEI_TZ).isoformat(),
    }
    try:
        supabase.table("study_logs").upsert(payload, on_conflict="study_date").execute()
        verified = (
            supabase.table("study_logs")
            .select("study_date,study_seconds,remembered_cards,quiz_count,mood,journal")
            .eq("study_date", payload["study_date"])
            .limit(1)
            .execute()
            .data or []
        )
        if not verified:
            raise RuntimeError("寫入後無法從 study_logs 讀回資料")
        saved = verified[0]
        st.session_state.daily_logs[payload["study_date"]] = {
            **empty_log(date.fromisoformat(payload["study_date"])),
            **saved,
        }
        st.session_state.persistence_error = None
        if notify:
            st.toast("今日學習紀錄已永久儲存至 Supabase")
        return True
    except Exception as exc:
        st.session_state.persistence_error = (
            "學習紀錄尚未寫入 Supabase。請先執行 supabase_learning_persistence.sql。"
            f" 詳細訊息：{exc}"
        )
        if notify:
            st.error(st.session_state.persistence_error)
        return False


def load_initial_data() -> None:
    if st.session_state.get("data_loaded"):
        return
    try:
        rows = supabase.table("vocabulary").select("*").execute().data or []
        st.session_state.review_zone = [r for r in rows if str(r.get("status", "")).lower() == "review"]
        st.session_state.brain_zone = [r for r in rows if str(r.get("status", "")).lower() == "mastered"]
        st.session_state.word_history = [r.get("word", "") for r in rows]
    except Exception as exc:
        st.warning(f"單字資料暫時無法同步：{exc}")
    try:
        profiles = supabase.table("user_profile").select("*").limit(1).execute().data or []
        st.session_state.user_profile = profiles[0] if profiles else None
    except Exception:
        st.session_state.user_profile = None
    try:
        logs = supabase.table("study_logs").select("*").execute().data or []
        st.session_state.daily_logs = {
            row["study_date"]:{**empty_log(date.fromisoformat(row["study_date"])), **row}
            for row in logs if row.get("study_date")
        }
    except Exception as exc:
        st.session_state.persistence_error = f"無法讀取 study_logs：{exc}"
    try:
        timer_rows = (
            supabase.table("study_timer_state")
            .select("*")
            .eq("id", 1)
            .limit(1)
            .execute()
            .data or []
        )
        if timer_rows:
            timer = timer_rows[0]
            saved_status = str(timer.get("timer_status", "idle"))
            if saved_status in {"idle", "running", "paused", "completed", "results"}:
                st.session_state.timer_status = saved_status
            st.session_state.timer_accumulated_seconds = float(
                timer.get("timer_accumulated_seconds", 0) or 0
            )
            started_at = timer.get("timer_started_at")
            st.session_state.timer_started_at = (
                datetime.fromisoformat(str(started_at).replace("Z", "+00:00")).timestamp()
                if started_at else None
            )
    except Exception as exc:
        current_error = st.session_state.get("persistence_error")
        timer_error = f"無法讀取 study_timer_state：{exc}"
        st.session_state.persistence_error = f"{current_error}；{timer_error}" if current_error else timer_error
    st.session_state.data_loaded = True


def save_word_to_supabase(payload: dict) -> None:
    try:
        existing = supabase.table("vocabulary").select("*").eq("word", payload["word"]).execute().data or []
        if existing:
            supabase.table("vocabulary").update({"status":"review"}).eq("word", payload["word"]).execute()
            saved = {**existing[0], "status":"review"}
        else:
            inserted = supabase.table("vocabulary").insert(payload).execute().data or []
            saved = inserted[0] if inserted else payload
        st.session_state.review_zone = [r for r in st.session_state.review_zone if r.get("word") != payload["word"]] + [saved]
        st.toast(f"{payload['word']} 已加入複習卡")
    except Exception as exc:
        st.error(f"單字儲存失敗：{exc}")


def update_word_status_in_supabase(word: str, status: str) -> None:
    try:
        supabase.table("vocabulary").update({"status":status}).eq("word", word).execute()
    except Exception as exc:
        st.warning(f"卡片狀態尚未同步：{exc}")


def save_profile_to_supabase(profile: dict) -> None:
    """更新目前設定，不再刪除資料表內的其他個人檔案。"""
    try:
        current_id = (st.session_state.user_profile or {}).get("id")
        if current_id:
            result = supabase.table("user_profile").update(profile).eq("id", current_id).execute()
        else:
            result = supabase.table("user_profile").insert(profile).execute()
        if result.data:
            st.session_state.user_profile = result.data[0]
            st.toast("個人設定已儲存")
    except Exception as exc:
        st.error(f"個人設定儲存失敗：{exc}")


def auto_save_generated_phrases_to_db(items: list[dict]) -> None:
    for item in items or []:
        sentence = item.get("french_sentence") or item.get("French_sentence") or ""
        if not sentence:
            continue
        payload = {
            "word":sentence.strip(), "lang_code":"fr",
            "phonetic":item.get("phonetic") or item.get("Phonetic") or "",
            "meaning":item.get("chinese_translation") or item.get("meaning") or "",
            "example_sentence":item.get("cultural_tip") or item.get("example_sentence") or "",
            "status":"scenarios",
        }
        try:
            exists = supabase.table("vocabulary").select("word").eq("word", payload["word"]).execute().data or []
            if not exists:
                supabase.table("vocabulary").insert(payload).execute()
        except Exception:
            continue


load_initial_data()

if st.session_state.get("persistence_error"):
    st.error(st.session_state.persistence_error)


# =========================================================
# 3.1 項目 3：發音加入快取
# =========================================================
@st.cache_data(show_spinner=False, ttl=86400)
def get_cached_audio(text, language_code):
    """同一文字一天內只產生一次語音。"""
    if not text:
        return None
    return nlp_engine.generate_audio(
        text,
        lang=language_code
    )


# =========================================================
# 4. 共用 UI 與計時器
# =========================================================
def brand_header() -> None:
    st.markdown(
        '<div class="lg-brand"><div class="lg-brand-mark">▤</div><div class="lg-brand-name">Language Genius</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_lottie(animation_name: str) -> dict | None:
    """從本機 assets 載入動畫，避免每次 Streamlit rerun 重讀大型 JSON。"""
    filename = LOTTIE_FILES.get(animation_name)
    if not filename:
        return None
    path = LOTTIE_DIR / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def render_lottie_state(
    animation_name: str,
    *,
    height: int = 260,
    loop: bool = True,
    key: str | None = None,
) -> None:
    """統一渲染六種貓咪狀態；套件或檔案缺失時保持介面可操作。"""
    animation = load_lottie(animation_name)
    if st_lottie and animation:
        st_lottie(
            animation,
            height=height,
            loop=loop,
            quality="high",
            key=key or f"cat_{animation_name}",
        )
        return
    st.markdown(
        '<div class="lg-cat-stage"><div class="lg-cat">🐈</div></div>',
        unsafe_allow_html=True,
    )
    if not st_lottie:
        st.caption("請在 requirements.txt 加入 streamlit-lottie，動畫即可顯示。")


def render_loading_animation(message: str, key: str):
    """顯示 Loading 貓咪並回傳 placeholder，任務完成後可呼叫 empty()。"""
    placeholder = st.empty()
    with placeholder.container():
        render_lottie_state("loading", height=190, loop=True, key=key)
        st.caption(message)
    return placeholder


def greeting() -> str:
    hour = datetime.now(TAIPEI_TZ).hour
    return "Good morning," if hour < 12 else "Good afternoon," if hour < 18 else "Good evening,"


def timer_elapsed() -> int:
    seconds = float(st.session_state.timer_accumulated_seconds)
    if st.session_state.timer_status == "running" and st.session_state.timer_started_at:
        seconds += time.time() - float(st.session_state.timer_started_at)
    return max(0, int(seconds))


def save_timer_state() -> bool:
    """只在開始、暫停、完成等狀態切換時寫入，不會每秒消耗資料庫請求。"""
    started_at = None
    if st.session_state.timer_started_at:
        started_at = datetime.fromtimestamp(
            float(st.session_state.timer_started_at), timezone.utc
        ).isoformat()
    payload = {
        "id":1,
        "timer_status":st.session_state.timer_status,
        "timer_started_at":started_at,
        "timer_accumulated_seconds":int(st.session_state.timer_accumulated_seconds),
        "updated_at":datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("study_timer_state").upsert(payload, on_conflict="id").execute()
        st.session_state.persistence_error = None
        return True
    except Exception as exc:
        st.session_state.persistence_error = (
            "計時狀態尚未寫入 Supabase。請先執行 supabase_learning_persistence.sql。"
            f" 詳細訊息：{exc}"
        )
        return False


def start_timer() -> None:
    if st.session_state.timer_status == "idle":
        st.session_state.timer_accumulated_seconds = 0.0
    st.session_state.timer_started_at = time.time()
    st.session_state.timer_status = "running"
    save_timer_state()


def pause_timer() -> None:
    if st.session_state.timer_status == "running":
        st.session_state.timer_accumulated_seconds = timer_elapsed()
        st.session_state.timer_started_at = None
        st.session_state.timer_status = "paused"
        save_timer_state()


def finish_timer() -> None:
    total = timer_elapsed()
    log = get_log(local_today()).copy()
    log["study_seconds"] = int(log.get("study_seconds", 0)) + total
    save_daily_log(log)
    st.session_state.timer_accumulated_seconds = 0.0
    st.session_state.timer_started_at = None
    st.session_state.timer_status = "completed"
    st.session_state.show_daily_log_form = True
    save_timer_state()


def reset_timer() -> None:
    st.session_state.timer_status = "idle"
    st.session_state.timer_started_at = None
    st.session_state.timer_accumulated_seconds = 0.0
    save_timer_state()


# =========================================================
# 5. 項目 2：更新 render_word_breakdown (單字可點選展開翻譯)
# =========================================================
def render_word_breakdown(data):
    """句中單字可以個別點選，不會再次呼叫 AI。"""

    breakdown = data.get("word_breakdown", [])

    if not breakdown:
        return

    st.markdown("### 點選句子中的單字")
    st.caption("點開單字即可查看語境翻譯、詞性和原形")

    language_code = data.get("lang_code", "fr")
    columns_per_row = 4

    for row_start in range(0, len(breakdown), columns_per_row):
        row_items = breakdown[row_start:row_start + columns_per_row]
        columns = st.columns(columns_per_row)

        for offset, item in enumerate(row_items):
            index = row_start + offset
            item_word = str(item.get("word", "")).strip()
            meaning = item.get("meaning", "")
            phonetic = item.get("phonetic", "")
            lemma = item.get("lemma", "")
            part_of_speech = item.get("part_of_speech", "")

            if not item_word:
                continue

            with columns[offset]:
                with st.popover(item_word, use_container_width=True):
                    st.markdown(f"### {item_word}")

                    if phonetic:
                        st.caption(f"/{phonetic}/")

                    if meaning:
                        st.markdown(f"**{meaning}**")

                    details = []

                    if part_of_speech:
                        details.append(f"詞性：{part_of_speech}")

                    if lemma and lemma.lower() != item_word.lower():
                        details.append(f"原形：{lemma}")

                    if details:
                        st.caption(" · ".join(details))

                    play_search_audio(
                        item_word,
                        language_code,
                        key=f"search_word_audio_{index}"
                    )


# 假設 play_search_audio 呼叫方式 (運用快取版本)
def play_search_audio(text, language_code, key):
    audio_stream = get_cached_audio(
        text,
        language_code
    )
    if audio_stream:
        st.audio(audio_stream, format="audio/mp3")


# =========================================================
# 6. 項目 1：首頁改用新版搜尋 (修改 render_home)
# =========================================================
def render_home() -> None:
    brand_header()
    
    # 這裡放入你原有的首頁頂部資訊...
    today_log = get_log(local_today())
    
    # 渲染新版搜尋模組
    render_search_module()


def render_search_module():
    """新版完整搜尋模組 (示意或對應你的實作)"""
    st.markdown("### 單字與句子查詢")
    query = st.text_input(
        "單字查詢",
        placeholder="輸入英文或法文單字/句子",
        label_visibility="collapsed"
    )
    if st.button("查詢", type="primary", use_container_width=True):
        if query:
            # 這裡執行查詢與分析邏輯，並會呼叫 render_word_breakdown()
            pass


這段 Python 語法基本正確，在 Python 3.10 以上可以啟動；但目前「查詢」功能不會執行，因為最後仍是 pass。

主要問題：

render_search_module() 沒有呼叫 AI 分析。
render_home() 的 today_log 沒有使用。
date | str、dict | None 需要 Python 3.10+。
st.popover() 需要較新的 Streamlit。
play_search_audio() 的 key 參數沒有實際使用。
html、random、re、calendar、components 等 import 在這段裡尚未使用。
word_breakdown 如果 AI 回傳的不是 list，可能導致錯誤。

建議把搜尋部分修改成：

def render_search_module() -> None:
    """查詢單字或句子，並顯示分析結果。"""
    st.markdown("### 單字與句子查詢")

    query = st.text_input(
        "單字查詢",
        placeholder="輸入英文或法文單字／句子",
        label_visibility="collapsed",
        key="search_query",
    )

    if not st.button(
        "查詢",
        type="primary",
        use_container_width=True,
        key="search_button",
    ):
        return

    query = query.strip()

    if not query:
        st.warning("請先輸入要查詢的單字或句子。")
        return

    loading = render_loading_animation(
        "正在分析內容…",
        key="search_loading",
    )

    try:
        # 請依照 AIService 裡真正的方法名稱調整
        result = ai_service.get_word_analysis(query)

        if isinstance(result, str):
            result = json.loads(result)

        if not isinstance(result, dict):
            raise TypeError("AI 分析結果必須是 dict 或 JSON object")

        st.session_state["search_result"] = result

    except json.JSONDecodeError:
        st.error("AI 回傳的內容不是有效的 JSON 格式。")

    except Exception as exc:
        st.error(f"查詢失敗：{exc}")

    finally:
        loading.empty()

    result = st.session_state.get("search_result")

    if not result:
        return

    sentence = (
        result.get("sentence")
        or result.get("original_text")
        or result.get("word")
        or query
    )
    translation = (
        result.get("translation")
        or result.get("chinese_translation")
        or result.get("meaning")
        or ""
    )
    phonetic = result.get("phonetic", "")
    language_code = result.get("lang_code", "fr")

    st.markdown(f"## {html.escape(str(sentence))}")

    if phonetic:
        st.caption(f"/{phonetic}/")

    if translation:
        st.markdown(f"**整句翻譯：** {html.escape(str(translation))}")

    play_search_audio(
        str(sentence),
        language_code,
        key="search_sentence_audio",
    )

    render_word_breakdown(result)

再強化 render_word_breakdown() 的資料檢查：

def render_word_breakdown(data: dict) -> None:
    """顯示句中每個單字的語境翻譯、詞性、原形及發音。"""
    breakdown = data.get("word_breakdown") or []

    if not isinstance(breakdown, list) or not breakdown:
        st.info("目前沒有可顯示的單字解析。")
        return

    st.markdown("### 點選句子中的單字")
    st.caption("點開單字即可查看語境翻譯、詞性和原形")

    language_code = str(data.get("lang_code") or "fr")
    columns_per_row = 4

    for row_start in range(0, len(breakdown), columns_per_row):
        row_items = breakdown[row_start:row_start + columns_per_row]
        columns = st.columns(len(row_items))

        for offset, item in enumerate(row_items):
            if not isinstance(item, dict):
                continue

            index = row_start + offset
            item_word = str(item.get("word") or "").strip()

            if not item_word:
                continue

            meaning = str(item.get("meaning") or "")
            phonetic = str(item.get("phonetic") or "")
            lemma = str(item.get("lemma") or "")
            part_of_speech = str(item.get("part_of_speech") or "")

            with columns[offset]:
                with st.popover(item_word, use_container_width=True):
                    st.markdown(f"### {html.escape(item_word)}")

                    if phonetic:
                        st.caption(f"/{phonetic}/")

                    if meaning:
                        st.markdown(f"**{html.escape(meaning)}**")

                    details = []

                    if part_of_speech:
                        details.append(
                            f"詞性：{html.escape(part_of_speech)}"
                        )

                    if lemma and lemma.casefold() != item_word.casefold():
                        details.append(
                            f"原形：{html.escape(lemma)}"
                        )

                    if details:
                        st.caption(" · ".join(details))

                    play_search_audio(
                        item_word,
                        language_code,
                        key=f"search_word_audio_{index}",
                    )

你的程式不是「語法錯誤」，而是搜尋區塊尚未完成。最需要確認的是 AIService 裡的方法是否真的叫：

get_word_analysis(query)

以及它實際回傳的 JSON 欄位名稱。現在前端同時使用 translation、chinese_translation、meaning 等不同命名，最好統一資料格式，否則很容易發生「有查詢結果，但畫面沒有翻譯」的情況。

今天 上午9:27
 目前這個版本無法顯示成功

找到原因了：目前程式只有「定義」render_home()，但沒有真正呼叫它；而且查詢按鈕裡仍然是 pass，因此不會顯示任何搜尋結果。

請將程式最下方的 render_search_module() 替換為：

def render_search_module() -> None:
    """搜尋並顯示單字或完整句子的分析結果。"""
    st.markdown("### 單字與句子查詢")

    query = st.text_input(
        "單字查詢",
        placeholder="輸入英文或法文單字／句子",
        label_visibility="collapsed",
        key="search_query",
    )

    if st.button(
        "查詢",
        type="primary",
        use_container_width=True,
        key="search_button",
    ):
        cleaned_query = query.strip()

        if not cleaned_query:
            st.warning("請輸入要查詢的單字或句子。")
        else:
            loading = render_loading_animation(
                "正在分析內容…",
                key="search_loading",
            )

            try:
                result = ai_service.get_word_analysis(cleaned_query)

                # AIService 如果回傳 JSON 字串，先轉成 dict
                if isinstance(result, str):
                    result = json.loads(result)

                if not isinstance(result, dict):
                    raise TypeError(
                        f"AI 回傳格式錯誤：預期 dict，實際為 {type(result).__name__}"
                    )

                st.session_state.search_result = result
                st.session_state.search_error = None

            except json.JSONDecodeError as exc:
                st.session_state.search_result = None
                st.session_state.search_error = (
                    f"AI 回傳的內容不是有效 JSON：{exc}"
                )

            except Exception as exc:
                st.session_state.search_result = None
                st.session_state.search_error = f"查詢失敗：{exc}"

            finally:
                loading.empty()

    error = st.session_state.get("search_error")
    if error:
        st.error(error)
        return

    result = st.session_state.get("search_result")
    if not result:
        return

    original_text = (
        result.get("original_text")
        or result.get("sentence")
        or result.get("word")
        or query
    )

    translation = (
        result.get("chinese_translation")
        or result.get("translation")
        or result.get("meaning")
        or "目前沒有翻譯"
    )

    phonetic = result.get("phonetic") or ""
    language_code = result.get("lang_code") or "fr"

    st.markdown('<div class="lg-card">', unsafe_allow_html=True)
    st.markdown(f"## {html.escape(str(original_text))}")

    if phonetic:
        st.caption(f"/{phonetic}/")

    st.markdown(
        f"**完整翻譯：** {html.escape(str(translation))}"
    )

    play_search_audio(
        str(original_text),
        language_code,
        key="search_sentence_audio",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    render_word_breakdown(result)

然後在 STATE_DEFAULTS 裡加入搜尋狀態：

STATE_DEFAULTS = {
    "active_page": "首頁",
    "review_zone": [],
    "brain_zone": [],
    "word_history": [],
    "current_card_index": 0,
    "user_profile": None,
    "selected_category": None,
    "timer_status": "idle",
    "timer_started_at": None,
    "timer_accumulated_seconds": 0.0,
    "daily_logs": {},
    "selected_log_date": local_today(),
    "show_daily_log_form": False,
    "show_monthly_report": False,
    "quiz_index": 0,
    "quiz_questions": [],
    "quiz_score": 0,
    "quiz_answered": False,
    "persistence_error": None,
    "search_result": None,
    "search_error": None,
}

最重要的是，在整個 Python 檔案最底部加入真正的頁面呼叫：

if __name__ == "__main__":
    render_home()

如果你有底部導覽系統，則改成：

if st.session_state.active_page == "首頁":
    render_home()
elif st.session_state.active_page == "日曆":
    render_calendar()
elif st.session_state.active_page == "複習卡":
    render_review_cards()
elif st.session_state.active_page == "A2刷題":
    render_quiz()

你現在無法顯示成功的兩個直接原因就是：

pass

沒有執行分析，以及：

render_home()

沒有被呼叫。修正後，如果仍出錯，畫面會直接顯示真正的錯誤訊息，下一步就能確認是 AIService 的方法名稱或 JSON 欄位不一致。

import calendar
import html
import json
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from services.ai_service import AIService
from services.nlp_engine import NLPEngine
from supabase import Client, create_client

try:
from streamlit_lottie import st_lottie
except ImportError:
st_lottie = None

=========================================================
1. App 與既有服務設定
=========================================================

st.set_page_config(
page_title="Language Genius",
page_icon="📖",
layout="wide",
initial_sidebar_state="collapsed",
)

TAIPEI_TZ = timezone(timedelta(hours=8))
DAILY_GOAL_MINUTES = 12
NAV_ITEMS = ["首頁", "日曆", "複習卡", "A2刷題"]
MOODS = ["很疲累", "有點累", "普通", "不錯", "很棒"]
MOOD_ICONS = ["☹", "🙁", "😐", "🙂", "😄"]
APP_DIR = Path(file).resolve().parent
LOTTIE_DIR = APP_DIR / "assets" / "lottie"
LOTTIE_FILES = {
"idle": "language_genius_cat_under_book_idle.json",
"learning": "language_genius_cat_plane_learning.json",
"paused": "language_genius_cat_box_paused.json",
"completed": "language_genius_cat_celebration_complete.json",
"results": "language_genius_cat_cup_results.json",
"loading": "language_genius_cat_stretch_loading.json",
}

@st.cache_resource
def init_supabase() -> Client:
"""沿用原本的 Supabase Secrets 設定。"""
return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_services():
"""沿用原本的 AI 與 NLP 引擎。"""
return AIService(), NLPEngine()

supabase = init_supabase()
ai_service, nlp_engine = get_services()

=========================================================
2. 視覺系統
=========================================================

st.markdown(
"""
<style>
{
--lg-bg:#F2F2F4; --lg-surface:#FFFFFF; --lg-text:#171717;
--lg-muted:#7D818A; --lg-line:#E8E8EA; --lg-orange:#F7A916;
--lg-orange-soft:#FFF3D7; --lg-shadow:0 12px 34px rgba(24,24,27,.055);
}
.stApp { background(--lg-bg); color(--lg-text); }
[data-testid="stHeader"] { background; }
[data-testid="stSidebar"] { background:#FAFAFA; }
[data-testid="stMainBlockContainer"] {
max-width:780px; padding-top:2.2rem; padding-bottom:8.5rem;
}
h1,h2,h3 { color(--lg-text); letter-spacing:-.035em; }
p,label,[data-testid="stCaptionContainer"] { color(--lg-muted); }
.lg-brand { display; align-items; gap:.65rem; margin-bottom:1.8rem; }
.lg-brand-mark {
width:34px; height:34px; display; place-items;
border-radius:11px; background(--lg-orange); color:#171717; font-size:18px;
}
.lg-brand-name { font-weight:750; color(--lg-text); }
.lg-eyebrow { color:#A36A00; font-size:.76rem; font-weight:750; letter-spacing:.12em; }
.lg-hero-title { font-size(2rem,6vw,3.2rem); line-height:1.05; margin:.25rem 0 .5rem; }
.lg-card {
background(--lg-surface); border:1px solid rgba(23,23,23,.035);
border-radius:22px; padding:24px; margin:18px 0; box-shadow(--lg-shadow);
}
.lg-stats { display; grid-template-columns(3,1fr); }
.lg-stat { text-align; padding:8px 14px; }
.lg-stat + .lg-stat { border-left:1px solid var(--lg-line); }
.lg-stat-label { color(--lg-muted); font-size:.82rem; margin-bottom:.45rem; }
.lg-stat-value { color(--lg-text); font-size:1.65rem; font-weight:780; line-height:1; }
.lg-stat-unit { color(--lg-muted); font-size:.78rem; margin-top:.35rem; }
.lg-cat-stage { min-height:185px; display; place-items; text-align; margin:24px 0 12px; }
.lg-cat { font-size:5.2rem; }
.lg-book { font-size:5.4rem; margin-top:-3.55rem; position; z-index:2; }
.lg-celebrate { animation .9s ease-in-out infinite alternate; }
@keyframes lg-bounce { from{transform(8px) rotate(-3deg)} to{transform(-18px) rotate(3deg)} }
.lg-log-row {
display; justify-content; gap:18px; align-items;
padding:14px 0; border-bottom:1px solid var(--lg-line);
}
.lg-log-row { border-bottom:0; }
.lg-log-title { color(--lg-text); font-weight:680; }
.lg-log-meta { color(--lg-muted); font-size:.84rem; margin-top:.25rem; }
.lg-pill {
display; border-radius:999px; background(--lg-orange-soft);
color:#855800; padding:.45rem .8rem; font-size:.78rem; font-weight:680;
}
.lg-note { border-left:3px solid var(--lg-orange); padding:.1rem 0 .1rem 1rem; color(--lg-muted); }
.stButton>button,.stFormSubmitButton>button {
min-height:48px; border-radius:14px; border:1px solid var(--lg-line);
font-weight:700; box-shadow; transition .15s ease;
}
.stButton>button,.stFormSubmitButton>button { border-color(--lg-orange); transform(-1px); }
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"] {
background(--lg-orange); color:#171717; border-color(--lg-orange);
}
[data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div {
border-radius:15px!important; border-color(--lg-line)!important; background:#FFF!important;
}
[data-testid="stMetric"] { background:#FFF; border-radius:18px; padding:18px; box-shadow(--lg-shadow); }
div[data-testid="stExpander"] { border:0; border-radius:18px; background:#FFF; box-shadow(--lg-shadow); }
.st-key-bottom_nav {
position; z-index:999; left:50%; bottom:18px; transform(-50%);
width(680px,calc(100vw - 28px)); background(255,255,255,.94);
border:1px solid rgba(23,23,23,.06); border-radius:22px; padding:5px 12px;
box-shadow:0 16px 44px rgba(24,24,27,.16); backdrop-filter(16px);
}
.st-key-bottom_nav [data-testid="stRadio"]>label { display; }
.st-key-bottom_nav [data-baseweb="radio"]>div { justify-content; width:100%; gap:4px; }
.st-key-bottom_nav label {
flex:1; justify-content; align-items; flex-direction;
gap:3px; position; border-radius:0; padding:7px 10px 9px;
background!important;
}
.st-key-bottom_nav label(input) { background!important; }
.st-key-bottom_nav label>div { display; }
.st-key-bottom_nav label::before {
content:""; display; width:25px; height:25px; flex:0 0 25px;
background:#171717; opacity:.72;
-webkit-mask-repeat; mask-repeat;
-webkit-mask-position; mask-position;
-webkit-mask-size; mask-size;
}
.st-key-bottom_nav label(1)::before {
-webkit-mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+");
mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+");
}
.st-key-bottom_nav label(2)::before {
-webkit-mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
}
.st-key-bottom_nav label(3)::before {
-webkit-mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg==");
mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg==");
}
.st-key-bottom_nav label(4)::before {
-webkit-mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+");
mask-image("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+");
}
.st-key-bottom_nav label(input)::before { opacity:1; }
.st-key-bottom_nav label(input)::after {
content:""; position; bottom:2px; width:18px; height:3px;
border-radius:999px; background(--lg-orange);
}
.st-key-bottom_nav p { color:#171717; font-size:.72rem; line-height:1; font-weight:650; opacity:.76; }
.st-key-bottom_nav label(input) p { opacity:1; font-weight:750; }
/* V6: real navigation buttons. No radio input or selection circles. /
.st-key-bottom_nav [data-testid="stHorizontalBlock"] { gap:0!important; }
.st-key-bottom_nav [data-testid="column"] { min-width:0!important; }
.st-key-bottom_nav .stButton { width:100%; }
.st-key-bottom_nav .stButton>button {
width:100%; min-width:0; min-height:62px; height:62px;
display; flex-direction; align-items; justify-content;
gap:4px; position; padding:5px 2px 8px;
border:0!important; border-radius:0!important;
color:#171717!important; background!important;
box-shadow!important; transform!important;
}
.st-key-bottom_nav .stButton>button,
.st-key-bottom_nav .stButton>button,
.st-key-bottom_nav .stButton>button {
border:0!important; color:#171717!important;
background!important; box-shadow!important;
transform!important;
}
.st-key-bottom_nav .stButton>button::before {
content:""; display; width:25px; height:25px; flex:0 0 25px;
background:#171717; opacity:.68;
-webkit-mask-image(--nav-icon); mask-image(--nav-icon);
-webkit-mask-repeat; mask-repeat;
-webkit-mask-position; mask-position;
-webkit-mask-size; mask-size;
}
.st-key-bottom_nav .stButton>button p {
margin:0; color:#171717!important; opacity:.76;
font-size:.72rem; line-height:1; font-weight:650; white-space;
}
.st-key-nav_home { --nav-icon("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTMgMTAuNSAxMiAzbDkgNy41VjIxSDNaIiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEuOSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjguMiIgY3k9IjEzLjEiIHI9IjEuMjUiLz48Y2lyY2xlIGN4PSIxNS44IiBjeT0iMTMuMSIgcj0iMS4yNSIvPjxjaXJjbGUgY3g9IjEwLjUiIGN5PSIxMC44IiByPSIxLjEiLz48Y2lyY2xlIGN4PSIxMy41IiBjeT0iMTAuOCIgcj0iMS4xIi8+PHBhdGggZD0iTTguNyAxNy4yYzAtMiAxLjQ1LTMuMSAzLjMtMy4xczMuMyAxLjEgMy4zIDMuMWMwIDEuMjUtMSAyLTIuMSAxLjQ1YTIuNiAyLjYgMCAwIDAtMi40IDBjLTEuMS41NS0yLjEtLjItMi4xLTEuNDVaIi8+PC9zdmc+"); }
.st-key-nav_calendar { --nav-icon("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE2IiByeD0iMi40IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMyA5aDE4TTcgM3Y0TTE3IDN2NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI5IiBjeT0iMTMiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNSIgY3k9IjEzIiByPSIxIi8+PHBhdGggZD0iTTguNSAxNmMxIDEuMTUgMi4xIDEuNyAzLjUgMS43czIuNS0uNTUgMy41LTEuNyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg=="); }
.st-key-nav_review { --nav-icon("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNCIgeT0iMyIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE4IiByeD0iMi41IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNNCAxNy41aDE0IiBmaWxsPSJub25lIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTUuNSA0LjVsLjY1IDEuOCAxLjg1LjY1LTEuODUuNjUtLjY1IDEuODUtLjY1LTEuODVMMTMgNi45NWwxLjg1LS42NVoiLz48cGF0aCBkPSJtMjAgOSAuNCAxLjEgMS4xLjQtMS4xLjRMMjAgMTJsLS40LTEuMS0xLjEtLjQgMS4xLS40WiIvPjwvc3ZnPg=="); }
.st-key-nav_quiz { --nav-icon("data/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0ibTggMTYgLjctMy4yTDE2LjQgNWwyLjYgMi42LTcuOCA3LjdaIi8+PC9zdmc+"); }
/ Lottie source images are transparent; keep Streamlit wrappers transparent too. */
[data-testid="stCustomComponentV1"],
[data-testid="stCustomComponentV1"]>div,
iframe[title="streamlit_lottie.st_lottie"] {
background!important; border:0!important; box-shadow!important;
}
@media(max-width:640px) {
[data-testid="stMainBlockContainer"] { padding:1.25rem 1rem 8rem; }
.lg-card { padding:20px; } .lg-stat { padding:6px; }
.lg-stat-value { font-size:1.35rem; } .lg-cat-stage { min-height:155px; }
.st-key-bottom_nav { bottom:10px; }
}
</style>
""",
unsafe_allow_html=True,
)

=========================================================
3. Session 與資料存取
=========================================================

def local_today() -> date:
return datetime.now(TAIPEI_TZ).date()

STATE_DEFAULTS = {
"active_page":"首頁", "review_zone":[], "brain_zone":[], "word_history":[],
"current_card_index":0, "user_profile", "selected_category",
"timer_status":"idle", "timer_started_at", "timer_accumulated_seconds":0.0,
"daily_logs":{}, "selected_log_date"(), "show_daily_log_form",
"show_monthly_report", "quiz_index":0, "quiz_questions":[],
"quiz_score":0, "quiz_answered", "persistence_error",
}
for state_key, default_value in STATE_DEFAULTS.items():
if state_key not in st.session_state:
st.session_state[state_key] = default_value

def empty_log(target_date: date) -> dict:
return {
"study_date".isoformat(), "study_seconds":0,
"remembered_cards":0, "quiz_count":0, "mood":"普通", "journal":"",
}

def get_log(target_date: date | str) -> dict:
key = target_date if isinstance(target_date, str) else target_date.isoformat()
if key not in st.session_state.daily_logs:
st.session_state.daily_logs[key] = empty_log(date.fromisoformat(key))
return st.session_state.daily_logs[key]

def save_daily_log(log: dict, notify: bool = False) -> bool:
"""同步 Session 與 Supabase，並讀回確認資料真的已寫入。"""
st.session_state.daily_logs[log["study_date"]] = log.copy()
payload = {
"study_date",
"study_seconds"(log.get("study_seconds", 0)),
"remembered_cards"(log.get("remembered_cards", 0)),
"quiz_count"(log.get("quiz_count", 0)),
"mood".get("mood", "普通"), "journal".get("journal", ""),
"updated_at".now(TAIPEI_TZ).isoformat(),
}
try:
supabase.table("study_logs").upsert(payload, on_conflict="study_date").execute()
verified = (
supabase.table("study_logs")
.select("study_date,study_seconds,remembered_cards,quiz_count,mood,journal")
.eq("study_date", payload["study_date"])
.limit(1)
.execute()
.data or []
)
if not verified:
raise RuntimeError("寫入後無法從 study_logs 讀回資料")
saved = verified[0]
st.session_state.daily_logs[payload["study_date"]] = {
**empty_log(date.fromisoformat(payload["study_date"])),
**saved,
}
st.session_state.persistence_error = None
if notify:
st.toast("今日學習紀錄已永久儲存至 Supabase")
return True
except Exception as exc:
st.session_state.persistence_error = (
"學習紀錄尚未寫入 Supabase。請先執行 supabase_learning_persistence.sql。"
f" 詳細訊息：{exc}"
)
if notify:
st.error(st.session_state.persistence_error)
return False

def load_initial_data() -> None:
if st.session_state.get("data_loaded"):
return
try:
rows = supabase.table("vocabulary").select("").execute().data or []
st.session_state.review_zone = [r for r in rows if str(r.get("status", "")).lower() == "review"]
st.session_state.brain_zone = [r for r in rows if str(r.get("status", "")).lower() == "mastered"]
st.session_state.word_history = [r.get("word", "") for r in rows]
except Exception as exc:
st.warning(f"單字資料暫時無法同步：{exc}")
try:
profiles = supabase.table("user_profile").select("").limit(1).execute().data or []
st.session_state.user_profile = profiles[0] if profiles else None
except Exception:
st.session_state.user_profile = None
try:
logs = supabase.table("study_logs").select("").execute().data or []
st.session_state.daily_logs = {
row["study_date"]:{**empty_log(date.fromisoformat(row["study_date"])), **row}
for row in logs if row.get("study_date")
}
except Exception as exc:
st.session_state.persistence_error = f"無法讀取 study_logs：{exc}"
try:
timer_rows = (
supabase.table("study_timer_state")
.select("")
.eq("id", 1)
.limit(1)
.execute()
.data or []
)
if timer_rows:
timer = timer_rows[0]
saved_status = str(timer.get("timer_status", "idle"))
if saved_status in {"idle", "running", "paused", "completed", "results"}:
st.session_state.timer_status = saved_status
st.session_state.timer_accumulated_seconds = float(
timer.get("timer_accumulated_seconds", 0) or 0
)
started_at = timer.get("timer_started_at")
st.session_state.timer_started_at = (
datetime.fromisoformat(str(started_at).replace("Z", "+00:00")).timestamp()
if started_at else None
)
except Exception as exc:
current_error = st.session_state.get("persistence_error")
timer_error = f"無法讀取 study_timer_state：{exc}"
st.session_state.persistence_error = f"{current_error}；{timer_error}" if current_error else timer_error
st.session_state.data_loaded = True

def save_word_to_supabase(payload: dict) -> None:
try:
existing = supabase.table("vocabulary").select("*").eq("word", payload["word"]).execute().data or []
if existing:
supabase.table("vocabulary").update({"status":"review"}).eq("word", payload["word"]).execute()
saved = {**existing[0], "status":"review"}
else:
inserted = supabase.table("vocabulary").insert(payload).execute().data or []
saved = inserted[0] if inserted else payload
st.session_state.review_zone = [r for r in st.session_state.review_zone if r.get("word") != payload["word"]] + [saved]
st.toast(f"{payload['word']} 已加入複習卡")
except Exception as exc:
st.error(f"單字儲存失敗：{exc}")

def update_word_status_in_supabase(word: str, status: str) -> None:
try:
supabase.table("vocabulary").update({"status"}).eq("word", word).execute()
except Exception as exc:
st.warning(f"卡片狀態尚未同步：{exc}")

def save_profile_to_supabase(profile: dict) -> None:
"""更新目前設定，不再刪除資料表內的其他個人檔案。"""
try:
current_id = (st.session_state.user_profile or {}).get("id")
if current_id:
result = supabase.table("user_profile").update(profile).eq("id", current_id).execute()
else:
result = supabase.table("user_profile").insert(profile).execute()
if result.data:
st.session_state.user_profile = result.data[0]
st.toast("個人設定已儲存")
except Exception as exc:
st.error(f"個人設定儲存失敗：{exc}")

def auto_save_generated_phrases_to_db(items: list[dict]) -> None:
for item in items or []:
sentence = item.get("french_sentence") or item.get("French_sentence") or ""
if not sentence:
continue
payload = {
"word".strip(), "lang_code":"fr",
"phonetic".get("phonetic") or item.get("Phonetic") or "",
"meaning".get("chinese_translation") or item.get("meaning") or "",
"example_sentence".get("cultural_tip") or item.get("example_sentence") or "",
"status":"scenarios",
}
try:
exists = supabase.table("vocabulary").select("word").eq("word", payload["word"]).execute().data or []
if not exists:
supabase.table("vocabulary").insert(payload).execute()
except Exception:
continue

load_initial_data()

if st.session_state.get("persistence_error"):
st.error(st.session_state.persistence_error)

=========================================================
3.1 項目 3：發音加入快取
=========================================================

@st.cache_data(show_spinner=False, ttl=86400)
def get_cached_audio(text, language_code):
"""同一文字一天內只產生一次語音。"""
if not text:
return None
return nlp_engine.generate_audio(
text,
lang=language_code
)

=========================================================
4. 共用 UI 與計時器
=========================================================

def brand_header() -> None:
st.markdown(
'<div class="lg-brand"><div class="lg-brand-mark">▤</div><div class="lg-brand-name">Language Genius</div></div>',
unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_lottie(animation_name: str) -> dict | None:
"""從本機 assets 載入動畫，避免每次 Streamlit rerun 重讀大型 JSON。"""
filename = LOTTIE_FILES.get(animation_name)
if not filename:
return None
path = LOTTIE_DIR / filename
try:
return json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
return None

def render_lottie_state(
animation_name: str,
*,
height: int = 260,
loop: bool = True,
key: str | None = None,
) -> None:
"""統一渲染六種貓咪狀態；套件或檔案缺失時保持介面可操作。"""
animation = load_lottie(animation_name)
if st_lottie and animation:
st_lottie(
animation,
height=height,
loop=loop,
quality="high",
key=key or f"cat_{animation_name}",
)
return
st.markdown(
'<div class="lg-cat-stage"><div class="lg-cat">🐈</div></div>',
unsafe_allow_html=True,
)
if not st_lottie:
st.caption("請在 requirements.txt 加入 streamlit-lottie，動畫即可顯示。")

def render_loading_animation(message: str, key: str):
"""顯示 Loading 貓咪並回傳 placeholder，任務完成後可呼叫 empty()。"""
placeholder = st.empty()
with placeholder.container():
render_lottie_state("loading", height=190, loop=True, key=key)
st.caption(message)
return placeholder

def greeting() -> str:
hour = datetime.now(TAIPEI_TZ).hour
return "Good morning," if hour < 12 else "Good afternoon," if hour < 18 else "Good evening,"

def timer_elapsed() -> int:
seconds = float(st.session_state.timer_accumulated_seconds)
if st.session_state.timer_status == "running" and st.session_state.timer_started_at:
seconds += time.time() - float(st.session_state.timer_started_at)
return max(0, int(seconds))

def save_timer_state() -> bool:
"""只在開始、暫停、完成等狀態切換時寫入，不會每秒消耗資料庫請求。"""
started_at = None
if st.session_state.timer_started_at:
started_at = datetime.fromtimestamp(
float(st.session_state.timer_started_at), timezone.utc
).isoformat()
payload = {
"id":1,
"timer_status".session_state.timer_status,
"timer_started_at",
"timer_accumulated_seconds"(st.session_state.timer_accumulated_seconds),
"updated_at".now(timezone.utc).isoformat(),
}
try:
supabase.table("study_timer_state").upsert(payload, on_conflict="id").execute()
st.session_state.persistence_error = None
return True
except Exception as exc:
st.session_state.persistence_error = (
"計時狀態尚未寫入 Supabase。請先執行 supabase_learning_persistence.sql。"
f" 詳細訊息：{exc}"
)
return False

def start_timer() -> None:
if st.session_state.timer_status == "idle":
st.session_state.timer_accumulated_seconds = 0.0
st.session_state.timer_started_at = time.time()
st.session_state.timer_status = "running"
save_timer_state()

def pause_timer() -> None:
if st.session_state.timer_status == "running":
st.session_state.timer_accumulated_seconds = timer_elapsed()
st.session_state.timer_started_at = None
st.session_state.timer_status = "paused"
save_timer_state()

def finish_timer() -> None:
total = timer_elapsed()
log = get_log(local_today()).copy()
log["study_seconds"] = int(log.get("study_seconds", 0)) + total
save_daily_log(log)
st.session_state.timer_accumulated_seconds = 0.0
st.session_state.timer_started_at = None
st.session_state.timer_status = "completed"
st.session_state.show_daily_log_form = True
save_timer_state()

def reset_timer() -> None:
st.session_state.timer_status = "idle"
st.session_state.timer_started_at = None
st.session_state.timer_accumulated_seconds = 0.0
save_timer_state()

=========================================================
5. 項目 2：更新 render_word_breakdown (單字可點選展開翻譯)
=========================================================
def render_word_breakdown(data: dict) -> None:
    """顯示句中每個單字的語境翻譯、詞性、原形及發音。"""
    breakdown = data.get("word_breakdown") or []

    if not isinstance(breakdown, list) or not breakdown:
        st.info("目前沒有可顯示的單字解析。")
        return

    st.markdown("### 點選句子中的單字")
    st.caption("點開單字即可查看語境翻譯、詞性和原形")

    language_code = str(data.get("lang_code") or "fr")
    columns_per_row = 4

    for row_start in range(0, len(breakdown), columns_per_row):
        row_items = breakdown[row_start:row_start + columns_per_row]
        columns = st.columns(len(row_items))

        for offset, item in enumerate(row_items):
            if not isinstance(item, dict):
                continue

            index = row_start + offset
            item_word = str(item.get("word") or "").strip()

            if not item_word:
                continue

            meaning = str(item.get("meaning") or "")
            phonetic = str(item.get("phonetic") or "")
            lemma = str(item.get("lemma") or "")
            part_of_speech = str(item.get("part_of_speech") or "")

            with columns[offset]:
                with st.popover(item_word, use_container_width=True):
                    st.markdown(f"### {html.escape(item_word)}")

                    if phonetic:
                        st.caption(f"/{phonetic}/")

                    if meaning:
                        st.markdown(f"**{html.escape(meaning)}**")

                    details = []

                    if part_of_speech:
                        details.append(
                            f"詞性：{html.escape(part_of_speech)}"
                        )

                    if lemma and lemma.casefold() != item_word.casefold():
                        details.append(
                            f"原形：{html.escape(lemma)}"
                        )

                    if details:
                        st.caption(" · ".join(details))

                    play_search_audio(
                        item_word,
                        language_code,
                        key=f"search_word_audio_{index}",
                    )

def play_search_audio(text, language_code, key):
audio_stream = get_cached_audio(
text,
language_code
)
if audio_stream:
st.audio(audio_stream, format="audio/mp3")

=========================================================
6. 項目 1：首頁改用新版搜尋 (修改 render_home)
=========================================================

def render_home() -> None:
brand_header()

# 這裡放入你原有的首頁頂部資訊...
today_log = get_log(local_today())

# 渲染新版搜尋模組
render_search_module()

def render_search_module() -> None:
    """查詢單字或句子，並顯示分析結果。"""
    st.markdown("### 單字與句子查詢")

    query = st.text_input(
        "單字查詢",
        placeholder="輸入英文或法文單字／句子",
        label_visibility="collapsed",
        key="search_query",
    )

    if not st.button(
        "查詢",
        type="primary",
        use_container_width=True,
        key="search_button",
    ):
        return

    query = query.strip()

    if not query:
        st.warning("請先輸入要查詢的單字或句子。")
        return

    loading = render_loading_animation(
        "正在分析內容…",
        key="search_loading",
    )

    try:
        # 請依照 AIService 裡真正的方法名稱調整
        result = ai_service.get_word_analysis(query)

        if isinstance(result, str):
            result = json.loads(result)

        if not isinstance(result, dict):
            raise TypeError("AI 分析結果必須是 dict 或 JSON object")

        st.session_state["search_result"] = result

    except json.JSONDecodeError:
        st.error("AI 回傳的內容不是有效的 JSON 格式。")

    except Exception as exc:
        st.error(f"查詢失敗：{exc}")

    finally:
        loading.empty()

    result = st.session_state.get("search_result")

    if not result:
        return

    sentence = (
        result.get("sentence")
        or result.get("original_text")
        or result.get("word")
        or query
    )
    translation = (
        result.get("translation")
        or result.get("chinese_translation")
        or result.get("meaning")
        or ""
    )
    phonetic = result.get("phonetic", "")
    language_code = result.get("lang_code", "fr")

    st.markdown(f"## {html.escape(str(sentence))}")

    if phonetic:
        st.caption(f"/{phonetic}/")

    if translation:
        st.markdown(f"**整句翻譯：** {html.escape(str(translation))}")

    play_search_audio(
        str(sentence),
        language_code,
        key="search_sentence_audio",
    )

    render_word_breakdown(result)
