import streamlit as st
import numpy as np

# --- 1. 頁面配置與五色線框 CSS ---
st.set_page_config(page_title="Solo Evolution Bingo", layout="wide") # 改為寬版佈局更適合 Dashboard
st.markdown("""
<style>
    /* 1. 基礎格子樣式 (未完成狀態) */
    .stButton>button {
        width: 100%;
        height: 110px;
        background-color: white;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3;
        color: #333333;
        white-space: normal;
        word-wrap: break-word;
    }

    /* 2. 達成任務後的狀態：變為紅色色塊 (Primary 狀態) */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 3px solid #FF4B4B !important;
        box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.3);
    }

    /* 3. 分類線框邏輯 (僅在 Secondary/未完成狀態下顯示) */
    
    /* [核心]：13格 (紅色線框) */
    div[data-testid="stButton"] > button[key="btn_12"][kind="secondary"] { border: 3px solid #FF4B4B !important; }

    /* [職涯/技能]：2, 4, 7, 9, 12, 14 格 (藍色線框) */
    div[data-testid="stButton"] > button[key="btn_1"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_3"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_6"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_8"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_11"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_13"][kind="secondary"] { border: 3px solid #1E90FF !important; }

    /* [生活/旅遊]：1, 5, 6, 10, 11, 15 格 (橘色線框) */
    div[data-testid="stButton"] > button[key="btn_0"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_4"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_5"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_9"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_10"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_14"][kind="secondary"] { border: 3px solid #FFA500 !important; }

    /* [創作/作品]：3, 8, 16, 17, 18, 19 格 (灰色線框) */
    div[data-testid="stButton"] > button[key="btn_2"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_7"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_15"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_16"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_17"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_18"][kind="secondary"] { border: 3px solid #D3D3D3 !important; }

    /* [健康/日常]：20, 21, 22, 23, 24, 25 格 (綠色線框) */
    div[data-testid="stButton"] > button[key="btn_19"][kind="secondary"], 
    div[data-testid="stButton"] > button[key="btn_20"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_21"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_22"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_23"][kind="secondary"],
    div[data-testid="stButton"] > button[key="btn_24"][kind="secondary"] { border: 3px solid #32CD32 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State ---
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
if 'last_lines_count' not in st.session_state:
    st.session_state.last_lines_count = 0
if 'custom_tasks' not in st.session_state:
    st.session_state.custom_tasks = ["目標 " + str(i+1) for i in range(25)]

# --- 3. 側邊欄：25 個輸入框與功能按鈕 ---
with st.sidebar:
    st.header("✍️ 編輯願望清單")
    
    # 建立一個索引與顏色的對照表 (依照你的規格)
    # 注意：i 是從 0 開始，所以規格格號要減 1
    for i in range(25):
        num = i + 1
        label_prefix = ""
        
        # 核心格 (13)
        if num == 13:
            label_prefix = "🔴 [核心] "
        # 職涯/技能 (2, 4, 7, 9, 12, 14)
        elif num in [2, 4, 7, 9, 12, 14]:
            label_prefix = "🔵 [職涯] "
        # 生活/旅遊 (1, 5, 6, 10, 11, 15)
        elif num in [1, 5, 6, 10, 11, 15]:
            label_prefix = "🟠 [生活] "
        # 創作/作品 (3, 8, 16, 17, 18, 19)
        elif num in [3, 8, 16, 17, 18, 19]:
            label_prefix = "⚪ [創作] "
        # 健康/日常 (20, 21, 22, 23, 24, 25)
        elif num in [20, 21, 22, 23, 24, 25]:
            label_prefix = "🟢 [日常] "
        
        # 渲染輸入框
        st.session_state.custom_tasks[i] = st.text_input(
            f"{label_prefix}格子 {num}", 
            value=st.session_state.custom_tasks[i], 
            key=f"sidebar_in_{i}"
        )
    
    # ... (下方的設定與重置按鈕不變) ...
    st.divider()
    st.header("⚙️ 系統操作")
    
    # 建立兩欄按鈕，讓佈局更對稱
    op_col1, op_col2 = st.columns(2)
    
    # 功能按鈕 1：設定 (確認並套用內容)
    if op_col1.button("✅ 設定內容", use_container_width=True):
        # 確保 custom_tasks 陣列與當前輸入框同步
        for i in range(25):
            st.session_state.custom_tasks[i] = st.session_state[f"sidebar_in_{i}"]
        
        st.toast("✅ 內容已設定完成！")
        st.rerun()
        
    # 功能按鈕 2：重置進度
    if op_col2.button("🗑️ 重置進度", use_container_width=True):
        st.session_state.board_state = np.zeros((5, 5), dtype=bool)
        st.session_state.last_lines_count = 0
        st.toast("🗑️ 勾選進度已清空")
        st.rerun()

# --- 4. 邏輯函式 ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 5. 主畫面 UI (即時預覽與挑戰) ---
st.title("🎯 2026 人生進化賓果盤")
st.write("在左側編輯內容後，直接點擊下方格子即可標註進度。")

st.divider()

# 渲染 5x5 賓果盤
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        task_text = st.session_state.custom_tasks[i]
        is_checked = st.session_state.board_state[row, col]
        display_label = f"{'✅' if is_checked else ''}\n{task_text}"
        
        if st.button(
            display_label, key=f"btn_{i}", 
            type="primary" if is_checked else "secondary"
        ):
            st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
            st.rerun()

# --- 6. 成就回饋 ---
st.divider()
current_lines = check_bingo(st.session_state.board_state)
st.subheader(f"目前連線數：{current_lines}")

if current_lines > 0 and current_lines > st.session_state.last_lines_count:
    st.balloons()
    st.toast(f"恭喜達成第 {current_lines} 條連線！")
    st.session_state.last_lines_count = current_lines
elif current_lines < st.session_state.last_lines_count:
    st.session_state.last_lines_count = current_lines

progress = st.session_state.board_state.sum() / 25
st.progress(progress)
st.caption(f"已完成 {int(st.session_state.board_state.sum())} / 25 個任務")
