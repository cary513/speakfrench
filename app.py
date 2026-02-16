import streamlit as st
import numpy as np

# --- 1. 頁面配置與五色線框 CSS ---
st.set_page_config(page_title="Solo Evolution Bingo", layout="centered")

st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 110px;
        background-color: white;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3;
        white-space: normal;
        word-wrap: break-word;
    }
    /* 精確染色邏輯 */
    div[data-testid="stButton"] > button[key="btn_12"] { border: 3px solid #FF4B4B !important; background-color: #FFF5F5 !important; }
    div[data-testid="stButton"] > button[key^="btn_0"], div[data-testid="stButton"] > button[key="btn_5"],
    div[data-testid="stButton"] > button[key="btn_10"], div[data-testid="stButton"] > button[key="btn_15"],
    div[data-testid="stButton"] > button[key="btn_20"], div[data-testid="stButton"] > button[key="btn_4"],
    div[data-testid="stButton"] > button[key="btn_9"], div[data-testid="stButton"] > button[key="btn_14"],
    div[data-testid="stButton"] > button[key="btn_19"], div[data-testid="stButton"] > button[key="btn_24"] { border: 3px solid #FFA500 !important; }
    div[data-testid="stButton"] > button[key="btn_1"], div[data-testid="stButton"] > button[key="btn_3"],
    div[data-testid="stButton"] > button[key="btn_6"], div[data-testid="stButton"] > button[key="btn_8"],
    div[data-testid="stButton"] > button[key="btn_16"], div[data-testid="stButton"] > button[key="btn_18"],
    div[data-testid="stButton"] > button[key="btn_21"], div[data-testid="stButton"] > button[key="btn_23"] { border: 3px solid #1E90FF !important; }
    div[data-testid="stButton"] > button[key="btn_2"], div[data-testid="stButton"] > button[key="btn_7"],
    div[data-testid="stButton"] > button[key="btn_11"], div[data-testid="stButton"] > button[key="btn_13"],
    div[data-testid="stButton"] > button[key="btn_17"], div[data-testid="stButton"] > button[key="btn_22"] { border: 3px solid #D3D3D3 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State ---
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
if 'last_lines_count' not in st.session_state:
    st.session_state.last_lines_count = 0
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = True
if 'custom_tasks' not in st.session_state:
    st.session_state.custom_tasks = ["任務 " + str(i+1) for i in range(25)]

# --- 3. 側邊欄：原位修改控制 ---
with st.sidebar:
    st.header("⚙️ 賓
