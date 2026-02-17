import streamlit as st
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="2026 Evolution", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 注入 CSS (高大於寬、分類線框、紅色塊) ---
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    .header-box { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .flip-clock { display: flex; gap: 4px; background: #1E1E1E; padding: 10px; border-radius: 10px; }
    .flip-digit {
        background: #333; color: #FF4B4B; font-family: monospace;
        font-size: 1.3rem; font-weight: bold; padding: 3px 8px;
        border-radius: 4px; border: 1px solid #000;
        background-image: linear-gradient(to bottom, #333 49%, #111 50%, #333 51%);
    }
    .stButton>button {
        width: 100% !important; height: 130px !important; 
        border-radius: 12px !important; font-size: 0.9rem !important;
        font-weight: bold !important; white-space: normal !important;
        word-wrap: break-word !important; line-height: 1.3 !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #FF4B4B !important; color: white !important; border: none !important;
    }
    /* 這裡保留你之前的五色線框 CSS ... */
</style>
""", unsafe_allow_html=True)

# --- 3. 核心初始化 (解決 AttributeError 的關鍵) ---
# 確保所有 key 在一開始就存在於 session_state 中
if 'custom_tasks' not in st.session_state:
    st.session_state.custom_tasks = ["目標 " + str(i+1) for i in range(25)]
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
if 'is_editing' not in st.session_state:
    st.session_state.is_editing = True
if 'last_lines_count' not in st.session_state: # 修正此處
    st.session_state.last_lines_count = 0
if 'should_celebrate' not in st.session_state:
    st.session_state.should_celebrate = False

# --- 4. 頂部 Header ---
t_date = datetime(2027, 1, 1)
days_left = f"{(t_date - datetime.now()).days:03}"
st.markdown(f"""
<div class="header-box">
    <h2 style="margin:0; font-size: 1.5rem;">🎯 人生導航 BINGO盤 </h2>
    <div class="flip-clock">
        <div class="flip-digit">{days_left[0]}</div>
        <div class="flip-digit">{days_left[1]}</div>
        <div class="flip-digit">{days_left[2]}</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- 5. 邏輯函式 ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 6. 渲染賓果盤 ---
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        if st.session_state.is_editing:
            st.session_state.custom_tasks[i] = st.text_input(f"G{i}", value=st.session_state.custom_tasks[i], key=f"edit_{i}", label_visibility="collapsed")
        else:
            is_checked = st.session_state.board_state[row, col]
            if st.button(f"{'✅' if is_checked else ''}\n{st.session_state.custom_tasks[i]}", key=f"btn_{i}", type="primary" if is_checked else "secondary"):
                st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
                
                # 判定氣球噴發
                new_lines = check_bingo(st.session_state.board_state)
                if new_lines > st.session_state.last_lines_count:
                    st.session_state.should_celebrate = True
                st.session_state.last_lines_count = new_lines
                st.rerun()

# --- 7. 成就與氣球觸發 ---
if not st.session_state.is_editing:
    if st.session_state.should_celebrate:
        st.balloons()
        st.session_state.should_celebrate = False # 噴完重置
    
    current_lines = st.session_state.last_lines_count # 現在這裡絕對有值了
    if current_lines > 0:
        st.success(f"🎊 精彩！達成 {current_lines} 條連線！")

# --- 8. 底部控制 ---
st.divider()
c1, c2 = st.columns(2)
if st.session_state.is_editing:
    if c1.button("🎯 鎖定目標", use_container_width=True):
        st.session_state.is_editing = False
        st.rerun()
else:
    if c1.button("✍️ 修改內容", use_container_width=True):
        st.session_state.is_editing = True
        st.rerun()
if c2.button("🗑️ 重置進度", use_container_width=True):
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
    st.session_state.last_lines_count = 0
    st.rerun()
