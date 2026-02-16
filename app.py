import streamlit as st
import numpy as np

# --- 1. 頁面配置與五色線框 CSS ---
st.markdown("""
<style>
    /* 1. 基礎設定：所有格子高度一致 */
    .stButton>button {
        width: 100%;
        height: 110px;
        background-color: white;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3; /* 預設灰色 */
    }

    /* 2. [紅色 - 核心] 第 13 格 */
    .stButton:nth-of-type(13) button {
        border: 3px solid #FF4B4B !important;
        background-color: #FFF5F5;
    }

    /* 3. [橘色 - 生活旅遊] 左右兩行 (1, 6, 11, 16, 21 和 5, 10, 15, 20, 25) */
    .stButton:nth-of-type(1) button, .stButton:nth-of-type(6) button, 
    .stButton:nth-of-type(11) button, .stButton:nth-of-type(16) button, 
    .stButton:nth-of-type(21) button, .stButton:nth-of-type(5) button, 
    .stButton:nth-of-type(10) button, .stButton:nth-of-type(15) button, 
    .stButton:nth-of-type(20) button, .stButton:nth-of-type(25) button {
        border: 3px solid #FFA500 !important;
    }

    /* 4. [灰色 - 創作作品] 中間十字軸 (3, 8, 12, 14, 18, 23) */
    .stButton:nth-of-type(3) button, .stButton:nth-of-type(8) button, 
    .stButton:nth-of-type(12) button, .stButton:nth-of-type(14) button, 
    .stButton:nth-of-type(18) button, .stButton:nth-of-type(23) button {
        border: 3px solid #D3D3D3 !important;
    }

    /* 5. [藍色 - 職涯目標] 其餘格子 (2, 4, 7, 9, 17, 19, 22, 24) */
    .stButton:nth-of-type(2) button, .stButton:nth-of-type(4) button, 
    .stButton:nth-of-type(7) button, .stButton:nth-of-type(9) button, 
    .stButton:nth-of-type(17) button, .stButton:nth-of-type(19) button, 
    .stButton:nth-of-type(22) button, .stButton:nth-of-type(24) button {
        border: 3px solid #1E90FF !important;
    }
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
    # 預設為你之前的職涯進化內容
    st.session_state.custom_tasks = [
        "Python 腳本", "MJ UI 指南", "數據調研", "首筆歐收", "遠端 4hr",
        "GSheets 串接", "LLM 輔助", "User Flow", "法文面試", "移動設備",
        "API 實作", "GitHub 10+", "Solo Evolution", "北極星指標", "英文作品集",
        "Firefly 合成", "A/B Test", "MVP 上線", "國際社群", "辦公危機",
        "Rive 組件", "AI UX Writing", "非同步溝通", "LinkedIn 推薦", "遠端合約"
    ]

# --- 3. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 賓果設定")
    if st.button("🔄 切換 編輯 / 挑戰 模式"):
        st.session_state.edit_mode = not st.session_state.edit_mode
        st.rerun()
    
    st.divider()
    if st.session_state.edit_mode:
        st.subheader("✍️ 編輯格子內容")
        for i in range(25):
            st.session_state.custom_tasks[i] = st.text_input(f"格子 {i+1}", value=st.session_state.custom_tasks[i], key=f"in_{i}")
    else:
        st.success("🎯 挑戰模式中")
        if st.button("🗑️ 重置進度"):
            st.session_state.board_state = np.zeros((5, 5), dtype=bool)
            st.session_state.last_lines_count = 0
            st.rerun()

# --- 4. 邏輯函式 ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 5. 主畫面 UI ---
st.title("🎯 2026 人生進化賓果")
if st.session_state.edit_mode:
    st.warning("目前為【編輯模式】，請在側邊欄填寫內容，完成後切換模式開始挑戰！")
else:
    st.write("點擊格子紀錄成就，連成一線即可解鎖氣球慶祝！")

# 渲染 5x5 賓果盤
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        task_text = st.session_state.custom_tasks[i]
        is_checked = st.session_state.board_state[row, col]
        
        # 顯示標籤：編輯模式不顯示✅，挑戰模式才顯示
        display_label = f"{'✅' if (is_checked and not st.session_state.edit_mode) else ''}\n{task_text}"
        
        if st.button(
            display_label, 
            key=f"btn_{i}", 
            type="primary" if (is_checked and not st.session_state.edit_mode) else "secondary",
            disabled=st.session_state.edit_mode
        ):
            st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
            st.rerun()

# --- 6. 成就回饋 ---
if not st.session_state.edit_mode:
    st.divider()
    current_lines = check_bingo(st.session_state.board_state)
    st.subheader(f"目前連線數：{current_lines}")

    # 只有當連線數增加時才噴氣球
    if current_lines > 0 and current_lines > st.session_state.last_lines_count:
        st.balloons()
        st.success(f"🎊 賀！達成新連線！目前總計：{current_lines} 條")
        st.session_state.last_lines_count = current_lines
    elif current_lines < st.session_state.last_lines_count:
        st.session_state.last_lines_count = current_lines

    # 進度條提示
    progress = st.session_state.board_state.sum() / 25
    st.progress(progress)
    st.caption(f"已完成 {st.session_state.board_state.sum()} / 25 個任務")
