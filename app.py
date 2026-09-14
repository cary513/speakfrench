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


def render_stats(log: dict, eyebrow: str = "今日學習數據") -> None:
    study_seconds = int(log.get("study_seconds", 0))
    study_minutes = "<1" if 0 < study_seconds < 60 else str(study_seconds // 60)
    st.markdown(
        f"""
        <div class="lg-card"><div class="lg-eyebrow">{eyebrow}</div>
          <div class="lg-stats">
            <div class="lg-stat"><div class="lg-stat-label">學習時間</div><div class="lg-stat-value">{study_minutes}</div><div class="lg-stat-unit">分鐘</div></div>
            <div class="lg-stat"><div class="lg-stat-label">複習卡</div><div class="lg-stat-value">{int(log.get('remembered_cards',0))}</div><div class="lg-stat-unit">張</div></div>
            <div class="lg-stat"><div class="lg-stat-label">A2 刷題</div><div class="lg-stat-value">{int(log.get('quiz_count',0))}</div><div class="lg-stat-unit">題</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_timer_scene() -> None:
    base_seconds, goal_seconds = timer_elapsed(), DAILY_GOAL_MINUTES * 60
    running = st.session_state.timer_status == "running"
    render_lottie_state(
        "learning" if running else "paused",
        height=270,
        loop=True,
        key="cat_learning" if running else "cat_paused",
    )
    components.html(
        f"""
        <div class="scene"><div class="paris">NEXT STOP · PARIS</div><div class="tower">♜</div>
          <div id="traveller" class="traveller">●</div><div class="path"></div>
          <div id="clock" class="clock">00:00:00</div><div class="goal">今日目標 {DAILY_GOAL_MINUTES} 分鐘</div>
        </div>
        <style>
          body{{margin:0;font-family:Arial,sans-serif;color:#171717}}
          .scene{{position:relative;height:175px;overflow:hidden;border-radius:24px;background:#fff}}
          .paris{{position:absolute;left:24px;top:22px;color:#999;letter-spacing:.18em;font-size:11px}}
          .tower{{position:absolute;right:38px;bottom:18px;font-size:72px;color:#3a3a3a;transform:scaleX(.7)}}
          .path{{position:absolute;left:30px;right:70px;bottom:32px;border-bottom:3px dotted #F7A916}}
          .traveller{{position:absolute;left:28px;bottom:24px;color:#F7A916;font-size:20px;transition:left .4s linear}}
          .clock{{text-align:center;font-size:42px;font-weight:750;padding-top:55px;letter-spacing:-.03em}}
          .goal{{text-align:center;color:#7D818A;margin-top:7px;font-size:14px}}
        </style>
        <script>
          const base={base_seconds},running={str(running).lower()},goal={goal_seconds},started=Date.now();
          function draw(){{const e=base+(running?Math.floor((Date.now()-started)/1000):0);
            const h=String(Math.floor(e/3600)).padStart(2,'0'),m=String(Math.floor((e%3600)/60)).padStart(2,'0'),s=String(e%60).padStart(2,'0');
            document.getElementById('clock').textContent=`${{h}}:${{m}}:${{s}}`;
            document.getElementById('traveller').style.left=`calc(28px + ${{Math.min(e/goal,1)}} * 58%)`;}}
          draw();setInterval(draw,500);
        </script>
        """,
        height=185,
    )


def render_daily_log_form(target_date: date) -> None:
    log = get_log(target_date).copy()
    st.markdown("### 完成學習紀錄")
    with st.form(f"daily_log_{target_date.isoformat()}"):
        mood = st.radio(
            "今天學習的心情如何？", MOODS,
            index=MOODS.index(log.get("mood", "普通")) if log.get("mood") in MOODS else 2,
            horizontal=True, format_func=lambda v:f"{MOOD_ICONS[MOODS.index(v)]} {v}",
        )
        journal = st.text_area(
            "心情日記", value=log.get("journal", ""),
            placeholder="今天學習時，哪一刻讓你感覺自己進步了？", height=130, max_chars=500,
        )
        if st.form_submit_button("儲存學習紀錄", type="primary", use_container_width=True):
            log["mood"], log["journal"] = mood, journal.strip()
            if save_daily_log(log, notify=True):
                st.session_state.show_daily_log_form = False
                st.session_state.timer_status = "results"
                save_timer_state()
                st.rerun()


# =========================================================
# 5. 首頁
# =========================================================
def analyze_word(word_input: str) -> None:
    normalized = word_input.strip()
    if not normalized:
        st.warning("請先輸入英文或法文單字。")
        return
    cache_key = f"word_cache_{normalized.lower()}"
    data = st.session_state.get(cache_key)
    if not data:
        try:
            rows = supabase.table("vocabulary").select("*").eq("word", normalized).execute().data or []
            if rows:
                row = rows[0]
                data = {
                    "word":row.get("word", normalized), "lang_code":row.get("lang_code", "fr"),
                    "phonetic":row.get("phonetic", ""), "meaning":row.get("meaning", ""),
                    "example_sentence":row.get("example_sentence", ""), "sentence_translation":"",
                }
        except Exception:
            data = None
    if not data:
        loading = render_loading_animation("貓咪正在整理單字資料…", "loading_word_analysis")
        try:
            data = ai_service.get_word_analysis(normalized)
        except Exception:
            st.error("AI 服務目前忙碌，請稍候一分鐘再試。")
            return
        finally:
            loading.empty()
    if data:
        st.session_state[cache_key] = data
        st.session_state.current_data = data
        save_word_to_supabase({
            "word":data.get("word", normalized), "lang_code":data.get("lang_code", "fr"),
            "phonetic":data.get("phonetic", ""), "meaning":data.get("meaning", ""),
            "example_sentence":data.get("example_sentence", ""), "status":"review",
        })


def render_word_result() -> None:
    data = st.session_state.get("current_data")
    if not data:
        return
    word, phonetic = html.escape(str(data.get("word", ""))), html.escape(str(data.get("phonetic", "")))
    meaning, example = html.escape(str(data.get("meaning", ""))), html.escape(str(data.get("example_sentence", "")))
    st.markdown(
        f'<div class="lg-card"><div class="lg-eyebrow">單字解析</div><h2>{word}</h2><p>/{phonetic}/ · {html.escape(str(data.get("lang_code","fr")))}</p><div class="lg-note"><strong>{meaning}</strong></div><p>{example}</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("播放發音", key="home_audio"):
        try:
            audio = nlp_engine.generate_audio(data.get("word", ""), lang=data.get("lang_code", "fr"))
            if audio:
                st.audio(audio, format="audio/mp3")
        except Exception:
            st.warning("語音服務暫時無法使用。")


def render_scenarios() -> None:
    categories = {
        "職場用語":"workplace", "日常生活":"daily", "機場通關":"airport",
        "購物消費":"shopping", "餐廳點菜":"restaurant", "自我介紹":"self_intro",
        "交友與價值觀":"social",
    }
    with st.expander("情境句型與個人化設定"):
        if not st.session_state.user_profile:
            with st.form("profile_form"):
                name = st.text_input("如何稱呼你？", placeholder="例如：Cary")
                level = st.selectbox("目前程度", ["入門級 (A1)", "初級實用 (A2)", "中級流利 (B1)", "進階商務 (B2)"])
                goal = st.text_input("學習目標", placeholder="例如：能在法國生活與工作")
                interests = st.text_area("興趣與日常", placeholder="讓 AI 生成更貼近你的情境")
                if st.form_submit_button("建立個人化設定", type="primary"):
                    if name and goal:
                        profile = {"display_name":name, "current_level":level, "learning_goal":goal, "interests":interests}
                        st.session_state.user_profile = profile
                        save_profile_to_supabase(profile)
                        st.rerun()
                    else:
                        st.warning("請填寫稱呼與學習目標。")
            return
        label = st.selectbox("選擇練習情境", list(categories.keys()))
        category = categories[label]
        cache_key = f"cache_phrases_{category}"
        if st.button("產生情境句型", type="primary"):
            loading = render_loading_animation("正在準備你的情境句型…", "loading_scenarios")
            try:
                items = ai_service.generate_phrases_by_category(category, st.session_state.user_profile)
            except Exception:
                items = []
            finally:
                loading.empty()
            st.session_state[cache_key] = items
            auto_save_generated_phrases_to_db(items)
        for index, item in enumerate(st.session_state.get(cache_key, [])):
            sentence = item.get("french_sentence") or item.get("French_sentence") or ""
            phonetic = item.get("phonetic") or item.get("Phonetic") or ""
            meaning = item.get("chinese_translation") or item.get("meaning") or ""
            tip = item.get("cultural_tip") or item.get("example_sentence") or ""
            st.markdown(f"### {sentence}")
            st.caption(f"/{phonetic}/")
            st.write(meaning)
            if tip:
                st.info(tip)
            left, right = st.columns(2)
            if left.button("播放", key=f"phrase_audio_{category}_{index}", use_container_width=True):
                try:
                    audio = nlp_engine.generate_audio(sentence, lang="fr")
                    if audio:
                        st.audio(audio, format="audio/mp3")
                except Exception:
                    st.warning("語音暫時無法播放。")
            if right.button("加入複習卡", key=f"phrase_save_{category}_{index}", use_container_width=True):
                save_word_to_supabase({
                    "word":sentence, "lang_code":"fr", "phonetic":phonetic,
                    "meaning":meaning, "example_sentence":tip, "status":"review",
                })
def get_cached_text_analysis(search_text):
    """依序讀取 Session、Supabase，最後才呼叫 Gemini。"""

    search_text = str(search_text).strip()

    if not search_text:
        return None

    cache_key = (
        f"text_analysis_{search_text.lower()}"
    )

    # 第一層：Session 快取
    cached_data = st.session_state.get(cache_key)

    if cached_data:
        return cached_data

    # 第二層：Supabase
    try:
        response = (
            supabase
            .table("vocabulary")
            .select("*")
            .eq("word", search_text)
            .limit(1)
            .execute()
        )

        if response.data:
            database_item = response.data[0]

            analysis_json = database_item.get("analysis_json")

            if isinstance(analysis_json, dict):
                st.session_state[cache_key] = analysis_json
                return analysis_json

    except Exception as error:
        print(f"搜尋 Supabase 快取失敗：{error}")

    # 第三層：Gemini
    try:
        analysis_data = ai_service.get_word_analysis(
            search_text
        )

        if analysis_data:
            st.session_state[cache_key] = analysis_data

        return analysis_data

    except Exception as error:
        print(f"Gemini 搜尋失敗：{error}")
        return None


def save_search_analysis(data):
    """將完整搜尋分析存入 Supabase。"""

    if not data:
        return

    database_data = {
        "word": data.get("word", ""),
        "lang_code": data.get("lang_code", "fr"),
        "phonetic": data.get("phonetic", ""),
        "meaning": data.get("meaning", ""),
        "example_sentence": data.get(
            "example_sentence",
            ""
        ),
        "status": "review",
        "analysis_json": data
    }

    try:
        response = (
            supabase
            .table("vocabulary")
            .select("id")
            .eq("word", database_data["word"])
            .limit(1)
            .execute()
        )

        if response.data:
            (
                supabase
                .table("vocabulary")
                .update({
                    "lang_code": database_data["lang_code"],
                    "phonetic": database_data["phonetic"],
                    "meaning": database_data["meaning"],
                    "example_sentence": database_data[
                        "example_sentence"
                    ],
                    "analysis_json": data
                })
                .eq("word", database_data["word"])
                .execute()
            )

        else:
            (
                supabase
                .table("vocabulary")
                .insert(database_data)
                .execute()
            )

    except Exception as error:
        st.warning(f"搜尋結果暫時無法同步：{error}")


def play_search_audio(text, language_code, key):
    """顯示發音按鈕並按需產生音訊。"""

    if st.button(
        "🔊 播放發音",
        key=key,
        use_container_width=True
    ):
        try:
            with st.spinner("正在準備發音..."):
                audio_stream = nlp_engine.generate_audio(
                    text,
                    lang=language_code
                )

            if audio_stream:
                st.audio(
                    audio_stream,
                    format="audio/mp3"
                )
            else:
                st.caption("目前無法產生音訊")

        except Exception:
            st.warning("語音服務暫時無法使用")


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

def render_search_module():
    """首頁單字與句子搜尋功能。"""

    st.markdown("### 查詢")

    search_column, button_column = st.columns(
        [5, 1],
        vertical_alignment="bottom"
    )

    with search_column:
        search_text = st.text_input(
            "搜尋英文或法文",
            placeholder="輸入英文或法文單字、句子",
            label_visibility="collapsed",
            key="home_search_input"
        )

    with button_column:
        search_submitted = st.button(
            "查詢",
            key="home_search_button",
            type="primary",
            use_container_width=True
        )

    if search_submitted:
        if not search_text.strip():
            st.warning("請先輸入單字或句子")

        else:
            with st.spinner("貓咪正在查字典..."):
                result = get_cached_text_analysis(
                    search_text
                )

            if result:
                st.session_state.search_result = result
                save_search_analysis(result)
                st.rerun()

            else:
                st.error(
                    "目前無法完成分析，請稍後再試。"
                )

    data = st.session_state.get("search_result")

    if not data:
        return

    with st.container(border=True):
        input_type = data.get(
            "input_type",
            "word"
        )
        original_text = data.get("word", "")
        language_code = data.get(
            "lang_code",
            "fr"
        )
        phonetic = data.get("phonetic", "")
        meaning = data.get("meaning", "")

        type_label = (
            "完整句子"
            if input_type == "sentence"
            else "單字"
        )

        st.caption(
            f"{type_label} · "
            f"{'法文' if language_code == 'fr' else '英文'}"
        )

        st.markdown(f"## {original_text}")

        if phonetic:
            st.caption(f"/{phonetic}/")

        st.markdown("#### 中文翻譯")
        st.write(meaning)

        play_search_audio(
            original_text,
            language_code,
            key="search_full_audio"
        )

        st.divider()

        if input_type == "word":
            st.markdown("#### 實用例句")
            st.info(
                data.get("example_sentence", "")
            )
            st.caption(
                data.get("sentence_translation", "")
            )

            play_search_audio(
                data.get("example_sentence", ""),
                language_code,
                key="search_example_audio"
            )

        render_word_breakdown(data)

        if st.button(
            "加入複習卡",
            key="add_search_to_review",
            use_container_width=True
        ):
            save_word_to_supabase({
                "word": original_text,
                "lang_code": language_code,
                "phonetic": phonetic,
                "meaning": meaning,
                "example_sentence": data.get(
                    "example_sentence",
                    ""
                ),
                "analysis_json": data,
                "status": "review"
            })

            st.success("已加入待複習區")

def render_home() -> None:
    brand_header()
    st.markdown(f'<div class="lg-hero-title">{greeting()}</div>', unsafe_allow_html=True)
    st.caption(datetime.now(TAIPEI_TZ).strftime("%A, %B %d"))
    render_search_module()
    render_stats(get_log(local_today()))

    if st.session_state.timer_status in {"running", "paused"}:
        render_timer_scene()
        left, right = st.columns(2)
        if st.session_state.timer_status == "running":
            if left.button("暫停", use_container_width=True):
                pause_timer(); st.rerun()
        elif left.button("繼續", type="primary", use_container_width=True):
            start_timer(); st.rerun()
        if right.button("結束學習", use_container_width=True):
            finish_timer(); st.rerun()
    elif st.session_state.timer_status == "completed":
        render_lottie_state("completed", height=290, loop=False, key="cat_completed")
        st.success("今日學習完成！你又向目標靠近了一點。")
        if st.button("查看並完成今日紀錄", type="primary", use_container_width=True):
            st.session_state.show_daily_log_form = True
    elif st.session_state.timer_status == "results":
        render_lottie_state("results", height=275, loop=True, key="cat_results")
        st.success("今日成果與心情紀錄已儲存。好好休息一下吧！")
        if st.button("開始新的學習", type="primary", use_container_width=True):
            reset_timer()
            st.rerun()
    else:
        render_lottie_state("idle", height=275, loop=True, key="cat_idle")
        if st.button("開始今日學習", type="primary", use_container_width=True):
            start_timer(); st.rerun()
    if st.session_state.show_daily_log_form:
        render_daily_log_form(local_today())
    st.write("")
    render_scenarios()


# =========================================================
# 6. 日曆與月報
# =========================================================
def monthly_logs(year: int, month: int) -> list[dict]:
    prefix = f"{year:04d}-{month:02d}-"
    return [log for key, log in st.session_state.daily_logs.items() if key.startswith(prefix)]


def render_month_grid(year: int, month: int) -> None:
    active = {
        date.fromisoformat(log["study_date"]).day for log in monthly_logs(year, month)
        if int(log.get("study_seconds", 0)) > 0
    }
    cells = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        for day in week:
            muted = day.month != month
            dot = '<span class="dot"></span>' if day.day in active and not muted else ""
            cells.append(f'<div class="day {"muted" if muted else ""}"><span>{day.day}</span>{dot}</div>')
    st.markdown(
        f"""
        <style>
        .cal{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}}
        .dow{{text-align:center;color:#92959C;font-size:.75rem;padding:8px 0}}
        .day{{min-height:54px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:14px;color:#171717}}
        .day.muted{{color:#C8C9CD}} .dot{{width:6px;height:6px;background:#F7A916;border-radius:50%;margin-top:5px}}
        </style>
        <div class="lg-card"><div class="cal">{''.join(f'<div class="dow">{d}</div>' for d in ['一','二','三','四','五','六','日'])}{''.join(cells)}</div></div>
        """,
        unsafe_allow_html=True,
    )


def render_monthly_report(year: int, month: int) -> None:
    logs = monthly_logs(year, month)
    total = {
        "study_seconds":sum(int(log.get("study_seconds", 0)) for log in logs),
        "remembered_cards":sum(int(log.get("remembered_cards", 0)) for log in logs),
        "quiz_count":sum(int(log.get("quiz_count", 0)) for log in logs),
    }
    st.markdown(f"## 你的 {month} 月")
    st.caption("MONTHLY LEARNING REVIEW")
    render_stats(total, "本月學習數據")
    weekly = [0, 0, 0, 0, 0]
    for log in logs:
        day = date.fromisoformat(log["study_date"]).day
        weekly[min((day - 1)//7, 4)] += int(log.get("study_seconds", 0))//60
    highest = max(weekly + [1])
    bars = "".join(
        f'<div style="flex:1;text-align:center"><div style="height:120px;display:flex;align-items:flex-end;justify-content:center"><div style="width:34px;height:{max(5,value/highest*100):.0f}%;background:#F7A916;border-radius:9px 9px 3px 3px"></div></div><small>第{i+1}週</small></div>'
        for i, value in enumerate(weekly)
    )
    st.markdown(f'<div class="lg-card"><div class="lg-eyebrow">每週學習時間</div><div style="display:flex;gap:12px;margin-top:20px">{bars}</div></div>', unsafe_allow_html=True)
    mood_counts = {mood:0 for mood in MOODS}
    for log in logs:
        mood_counts[log.get("mood", "普通")] = mood_counts.get(log.get("mood", "普通"), 0) + 1
    main_mood = max(mood_counts, key=mood_counts.get) if logs else "尚未記錄"
    st.markdown(
        f'<div class="lg-card"><div class="lg-eyebrow">學習洞察</div><h3>本月常見心情：{main_mood}</h3><p>保持每日短時間練習，並優先加強完成率較低的題型。</p></div>',
        unsafe_allow_html=True,
    )
    render_lottie_state("results", height=220, loop=True, key="cat_monthly_results")


def render_calendar_page() -> None:
    brand_header()
    selected = st.session_state.selected_log_date
    title_col, report_col = st.columns([3, 1])
    title_col.markdown(f"## {selected.strftime('%B %Y')}")
    if report_col.button("月報", use_container_width=True):
        st.session_state.show_monthly_report = not st.session_state.show_monthly_report
    if st.session_state.show_monthly_report:
        render_monthly_report(selected.year, selected.month)
        return
    render_month_grid(selected.year, selected.month)
    selected = st.date_input("選擇日期", value=selected, max_value=local_today())
    st.session_state.selected_log_date = selected
    log = get_log(selected)
    render_stats(log)
    mood = log.get("mood", "普通")
    mood_icon = MOOD_ICONS[MOODS.index(mood)] if mood in MOODS else "😐"
    journal = html.escape(log.get("journal", "")) or "這一天還沒有留下心情日記。"
    st.markdown(
        f'<div class="lg-card"><div class="lg-eyebrow">{selected.strftime("%m月%d日")} 學習紀錄</div><div class="lg-log-row"><div class="lg-log-title">今日學習心情</div><div class="lg-pill">{mood_icon} {mood}</div></div><div class="lg-log-row"><div><div class="lg-log-title">心情日記</div><div class="lg-log-meta">{journal}</div></div></div></div>',
        unsafe_allow_html=True,
    )
    if st.button("編輯這天的紀錄", use_container_width=True):
        st.session_state.show_daily_log_form = True
    if st.session_state.show_daily_log_form:
        render_daily_log_form(selected)


# =========================================================
# 7. 複習卡
# =========================================================
def render_flashcards() -> None:
    brand_header(); st.markdown("## 複習卡")
    cards = st.session_state.review_zone
    if not cards:
        st.success("目前沒有待複習內容。")
        st.markdown('<div class="lg-cat-stage"><div class="lg-cat">🧶🐈</div></div>', unsafe_allow_html=True)
        return
    index = min(st.session_state.current_card_index, len(cards) - 1)
    card = cards[index]
    word = html.escape(str(card.get("word", "")))
    phonetic = html.escape(str(card.get("phonetic", "")))
    meaning = html.escape(str(card.get("meaning", "")))
    example = html.escape(str(card.get("example_sentence", "")))
    st.caption(f"{index + 1} / {len(cards)} · 左右滑動卡片")
    st.markdown(
        f'<div class="lg-card" style="min-height:330px;display:flex;flex-direction:column;justify-content:center;text-align:center"><h1>{word}</h1><p>/{phonetic}/</p><div style="width:52px;border-top:1px solid #E8E8EA;margin:26px auto"></div><h3>{meaning}</h3><p>{example}</p><div style="font-size:3.3rem;margin-top:16px">🐈</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("播放發音", use_container_width=True):
        try:
            audio = nlp_engine.generate_audio(card.get("word", ""), lang=card.get("lang_code", "fr"))
            if audio:
                st.audio(audio, format="audio/mp3")
        except Exception:
            st.warning("語音暫時無法播放。")
    left, right = st.columns(2)
    if left.button("← 還要複習", use_container_width=True):
        st.session_state.current_card_index = (index + 1) % len(cards)
        st.rerun()
    if right.button("記住了 →", type="primary", use_container_width=True):
        mastered = st.session_state.review_zone.pop(index)
        if mastered.get("word") not in [r.get("word") for r in st.session_state.brain_zone]:
            st.session_state.brain_zone.append(mastered)
        update_word_status_in_supabase(mastered.get("word", ""), "mastered")
        log = get_log(local_today()).copy()
        log["remembered_cards"] = int(log.get("remembered_cards", 0)) + 1
        save_daily_log(log)
        st.session_state.current_card_index = 0
        st.toast("記住 1 張，已加入今日數據")
        st.rerun()


# =========================================================
# 8. A2 刷題
# =========================================================
def render_a2_quiz() -> None:
    brand_header(); st.markdown("## A2 刷題")
    skills = {"全部":None, "閱讀 Reading":"reading", "聽力 Listening":"listening", "寫作 Writing":"writing", "口說 Speaking":"speaking"}
    selected = st.selectbox("選擇練習技能", list(skills.keys()), key="skill_selector")
    if st.button("開始刷題 / 換一批題目", type="primary", use_container_width=True):
        loading = render_loading_animation("貓咪正在載入 A2 題目…", "loading_a2_questions")
        try:
            query = supabase.table("quiz_questions").select("*").eq("is_active", True)
            if skills[selected]:
                query = query.eq("skill", skills[selected])
            questions = query.execute().data or []
            random.shuffle(questions)
            st.session_state.quiz_questions = questions[:10]
            st.session_state.quiz_index = st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.rerun()
        except Exception as exc:
            st.error(f"載入題目失敗：{exc}")
        finally:
            loading.empty()
    questions = st.session_state.quiz_questions
    if not questions:
        st.markdown('<div class="lg-cat-stage"><div class="lg-cat">🐈</div></div>', unsafe_allow_html=True)
        st.caption("選擇技能後開始今天的 A2 練習。")
        return
    index = st.session_state.quiz_index
    if index >= len(questions):
        st.success(f"本輪完成：答對 {st.session_state.quiz_score} / {len(questions)} 題")
        if st.button("再練一次", type="primary"):
            st.session_state.quiz_index = st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.rerun()
        return
    question = questions[index]
    st.caption(f"題目 {index + 1} / {len(questions)} · {question.get('skill', '')}")
    st.markdown(f'<div class="lg-card"><h3>{question.get("question_text", "")}</h3></div>', unsafe_allow_html=True)
    if question.get("skill") == "listening":
        parts = re.findall(r"[«「]?([A-Za-zÀ-ÿœæç'’. ?!,;:]+)[»」]?", question.get("question_text", ""))
        playable = next((p.strip() for p in parts if len(p.strip()) > 15), None)
        if playable and st.button("播放聽力內容"):
            try:
                audio = nlp_engine.generate_audio(playable, lang="fr")
                if audio:
                    st.audio(audio, format="audio/mp3")
            except Exception:
                st.warning("語音暫時無法使用。")
    if question.get("question_type") == "mcq":
        options = question.get("options") or []
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                options = []
        answer = st.radio("請選擇答案", options, key=f"answer_{index}")
    else:
        answer = st.text_area("輸入你的回答", key=f"answer_{index}", height=120)
    if not st.session_state.quiz_answered:
        if st.button("提交答案", type="primary", use_container_width=True):
            st.session_state.quiz_answered = True
            if question.get("question_type") == "mcq" and answer == question.get("correct_answer", ""):
                st.session_state.quiz_score += 1
            log = get_log(local_today()).copy()
            log["quiz_count"] = int(log.get("quiz_count", 0)) + 1
            save_daily_log(log)
            st.rerun()
    else:
        correct = question.get("correct_answer", "")
        if question.get("question_type") == "mcq":
            st.success("答對了！") if answer == correct else st.error(f"正確答案：{correct}")
        else:
            st.info(f"參考答案：{correct}")
        st.markdown("### 解析")
        st.write(question.get("explanation", "暫無解析"))
        if st.button("下一題 →", use_container_width=True):
            st.session_state.quiz_index += 1
            st.session_state.quiz_answered = False
            st.rerun()


# =========================================================
# 9. 固定按鈕導覽與路由
# =========================================================
NAV_KEYS = {"首頁":"home", "日曆":"calendar", "複習卡":"review", "A2刷題":"quiz"}


def navigate_to(page: str) -> None:
    st.session_state.active_page = page


active_page = st.session_state.active_page
active_nav_key = NAV_KEYS.get(active_page, "home")
st.markdown(
    f"""
    <style>
    .st-key-bottom_nav .st-key-nav_{active_nav_key} button::before {{ opacity:1!important; }}
    .st-key-bottom_nav .st-key-nav_{active_nav_key} button p {{ opacity:1!important; font-weight:750!important; }}
    .st-key-bottom_nav .st-key-nav_{active_nav_key} button::after {{
        content:""; position:absolute; bottom:1px; width:18px; height:3px;
        border-radius:999px; background:var(--lg-orange);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="bottom_nav"):
    nav_columns = st.columns(len(NAV_ITEMS), gap="small")
    for nav_column, page in zip(nav_columns, NAV_ITEMS):
        nav_column.button(
            page,
            key=f"nav_{NAV_KEYS[page]}",
            on_click=navigate_to,
            args=(page,),
            use_container_width=True,
        )

active_page = st.session_state.active_page

if active_page == "首頁":
    render_home()
elif active_page == "日曆":
    render_calendar_page()
elif active_page == "複習卡":
    render_flashcards()
else:
    render_a2_quiz()


with st.sidebar:
    st.markdown("## Language Genius")
    st.caption("學習資料總覽")
    st.metric("待複習", len(st.session_state.review_zone))
    st.metric("已記住", len(st.session_state.brain_zone))
    if st.session_state.user_profile:
        st.markdown("### 個人設定")
        st.write(st.session_state.user_profile.get("display_name", ""))
        st.caption(st.session_state.user_profile.get("current_level", ""))
        st.caption(st.session_state.user_profile.get("learning_goal", ""))
