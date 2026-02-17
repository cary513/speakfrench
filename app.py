import streamlit as st
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 (行動優先：不使用側邊欄) ---
st.set_page_config(page_title="2026 Evolution", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 注入行動端優化 CSS ---
st.markdown("""
<style>
    /* 隱藏側邊欄按鈕 (手機端更乾淨) */
    [data-testid="collapsedControl"] { display: none; }
    
    /* 頂部 Header 佈局 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    /* 翻牌計時器縮小版 (適合手機) */
    .mini-flip-container {
        display: flex;
        gap: 4px;
        background: #222;
        padding: 8px;
        border-radius: 8px;
    }
    .mini-flip-card {
        background: #333;
        color: #FF4B4B;
        font-family: monospace;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #000;
    }

    /* 賓果格子優化 */
    .stButton>button {
        width: 100%;
        height: 80px; /* 手機端高度稍微調降 */
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: bold;
        padding: 5px !important;
    }
    
    /* 編輯輸入框樣式優化 */
    div[data-testid="stTextInput"] > div {
        padding: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化狀態 ---
if 'custom_tasks' not in st.session_state:
    st.session_state.custom_tasks = ["目標 " + str(i+1) for i in range(25)]
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)

# --- 4. 頂部欄位：左標題、右倒數 ---
t_date = datetime(2027, 1, 1)
days_left = f"{(t_date - datetime.now()).days:03}"

header_col1, header_col2 = st.columns([2, 1])
with header_col1:
    st.title("🎯 人生進化賓果")
with header_col2:
    st.markdown(f"""
    <div class="mini-flip-container">
        <div class="mini-flip-card">{days_left[0]}</div>
        <div class="mini-flip-card">{days_left[1]}</div>
        <div class="mini-flip-card">{days_left[2]}</div>
    </div>
    <div style="font-size: 0.6rem; color: #888; text-align: center;">DAYS TO 2027</div>
    """, unsafe_allow_html=True)

# --- 5. 模式切換與控制 ---
edit_mode = st.toggle("✍️ 編輯模式 (關閉後可進行挑戰點擊)", value=True)

# --- 6. 5x5 核心矩陣 (編輯與挑戰整合) ---
def check_bingo(state):
    return int(np.all(state, axis=1).sum() + np.all(state, axis=0).sum() + np.all(np.diag(state)) + np.all(np.diag(np.fliplr(state))))

cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        if edit_mode:
            # 編輯模式：直接顯示輸入框
            st.session_state.custom_tasks[i] = st.text_input(
                f"G{i+1}", 
                value=st.session_state.custom_tasks[i], 
                key=f"edit_{i}", 
                label_visibility="collapsed"
            )
        else:
            # 挑戰模式：顯示賓果按鈕
            is_checked = st.session_state.board_state[row, col]
            task_text = st.session_state.custom_tasks[i]
            if st.button(
                f"{'✅' if is_checked else ''}\n{task_text}", 
                key=f"btn_{i}",
                type="primary" if is_checked else "secondary"
            ):
                st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
                st.rerun()

# --- 7. 成就反饋 ---
if not edit_mode:
    st.divider()
    current_lines = check_bingo(st.session_state.board_state)
    st.write(f"🔥 目前連線：{current_lines}")
    if st.button("🗑️ 重置進度"):
        st.session_state.board_state = np.zeros((5, 5), dtype=bool)
        st.rerun()
