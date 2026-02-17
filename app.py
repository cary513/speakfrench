import streamlit as st
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 (行動優先：全畫面寬度) ---
st.set_page_config(page_title="2026 Evolution", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 注入 CSS：固定長方形比例、分類線框、行動端 UI ---
st.markdown("""
<style>
    /* 隱藏側邊欄並減少頂部空白 */
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* 頂部 Header：左標題、右翻牌倒數 */
    .header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    /* 翻牌鐘樣式 (移除紅色括號) */
    .flip-clock { display: flex; gap: 4px; background: #1E1E1E; padding: 10px; border-radius: 10px; }
    .flip-digit {
        background: #333; color: #FF4B4B; font-family: monospace;
        font-size: 1.3rem; font-weight: bold; padding: 3px 8px;
        border-radius: 4px; border: 1px solid #000;
        background-image: linear-gradient(to bottom, #333 49%, #111 50%, #333 51%);
    }

    /* 5x5 格子：固定長方形比例 (高 > 寬) */
    .stButton>button {
        width: 100% !important;
        height: 130px !important; /* 固定高度大於寬度，適合手機直式閱讀 */
        border-radius: 12px !important;
        font-size: 0.9rem !important;
        font-weight: bold !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.3 !important;
        transition: all 0.2s;
    }

    /* 挑戰模式：達成後的紅色塊 (Primary 狀態) */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        box-shadow: 0px 4px 12px rgba(255, 75, 75, 0.4);
    }

    /* 未達成時的五色線框規範 (Secondary 狀態) */
    /* [核心]：13格 (Key: btn_12) - 紅色線框 */
    div[data-testid="stButton"] > button[key="btn_12"][kind="secondary"] { border: 3px solid #FF4B4B !important; }

    /* [職涯/技能]：2, 4, 7, 9, 12, 14 格 - 藍色線框 */
    div[data-testid="stButton"] > button[key="btn_1"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_3"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_6"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_8"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_11"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_13"][kind="secondary"] { border: 3px solid #1E90FF !important; }

    /* [生活/旅遊]：1, 5, 6, 10, 11, 15 格 - 橘色線框 */
    div[data-testid="stButton"] > button[key="btn_0"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_4"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_5"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_9"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_10"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_14"][kind="secondary"] { border: 3px solid #FFA500 !important; }

    /* [創作/作品]：3, 8, 16, 17, 18, 19 格 - 灰色線框 */
    div[data-testid="stButton"] > button[key="btn_2"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_7"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_15"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_16"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_17"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_18"][kind="secondary"] { border: 3px solid #D3D3D3 !important; }

    /* [健康/日常]：20, 21, 22, 23, 24, 25 格 - 綠色線框 */
    div[data-testid="stButton"] > button[key="btn_19"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_20"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_21"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_22"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_23"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_24"][kind="secondary"] { border: 3px solid #32CD32 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化 Session State ---
if 'custom_tasks' not in st.session_state:
    st.session_state.custom_tasks = ["目標 " + str(i+1) for i in range(25)]
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
if 'is_editing' not in st.session_state:
    st.session_state.is_editing = True

# --- 4. 頂部自定義 Header ---
t_date = datetime(2027, 1, 1)
days_left = f"{(t_date - datetime.now()).days:03}"

st.markdown(f"""
<div class="header-box">
    <h2 style="margin:0; font-size: 1.5rem;">🎯 人生進化賓果盤</h2>
    <div style="text-align: right;">
        <div class="flip-clock">
            <div class="flip-digit">{days_left[0]}</div>
            <div class="flip-digit">{days_left[1]}</div>
            <div class="flip-digit">{days_left[2]}</div>
        </div>
        <div style="font-size: 0.6rem; color: #888; margin-top:4px; letter-spacing:1px;">DAYS TO 2027</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- 5. 核心邏輯函式 (置於渲染前) ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 6. 5x5 矩陣渲染 ---
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        if st.session_state.is_editing:
            st.session_state.custom_tasks[i] = st.text_input(
                f"G{i}", value=st.session_state.custom_tasks[i], 
                key=f"edit_{i}", label_visibility="collapsed"
            )
        else:
            is_checked = st.session_state.board_state[row, col]
            task_text = st.session_state.custom_tasks[i]
            if st.button(
                f"{'✅' if is_checked else ''}\n{task_text}", 
                key=f"btn_{i}",
                type="primary" if is_checked else "secondary"
            ):
                # 1. 更新狀態
                st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
                
                # 2. 立即判定連線狀況
                new_lines = check_bingo(st.session_state.board_state)
                
                # 3. 如果連線數增加，先存進 Session State 再 Rerun
                if new_lines > st.session_state.last_lines_count:
                    st.session_state.should_celebrate = True # 新增一個慶祝標記
                
                st.session_state.last_lines_count = new_lines
                st.rerun()

# --- 7. 成就回饋與氣球觸發 ---
if not st.session_state.is_editing:
    current_lines = st.session_state.last_lines_count
    
    # 檢查是否需要慶祝
    if st.session_state.get('should_celebrate', False):
        st.balloons()
        st.toast(f"🎊 太強了！達成第 {current_lines} 條連線！")
        st.session_state.should_celebrate = False # 噴完後關閉標記
    
    if current_lines > 0:
        st.success(f"🔥 目前已達成 {current_lines} 條連線！")
