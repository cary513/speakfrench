import streamlit as st
import numpy as np

# --- 1. 頁面配置與五色線框 CSS ---
st.set_page_config(page_title="Solo Evolution Bingo", layout="centered")

bingo_style = """
<style>
    /* 基礎格子樣式 */
    .stButton>button {
        width: 100%;
        height: 110px;
        background-color: white;
        color: #333333;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3;
        display: flex;
        align-items: center;
        justify-content: center;
        white-space: normal;
        word-wrap: break-word;
        font-size: 14px;
    }

    /* [核心] 第 13 格：紅色線框 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(13) button {
        border: 3px solid #FF4B4B !important;
        background-color: #FFF5F5;
    }

    /* [生活/旅遊] 橘色線框：1, 5, 6, 10, 11, 15, 16, 20, 21, 25 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(6) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(10) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(11) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(15) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(16) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(20) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(21) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(25) button {
        border: 3px solid #FFA500 !important;
    }

    /* [職涯/目標] 藍色線框：2, 4, 7, 9, 17, 19, 22, 24 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(7) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(9) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(17) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(19) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(22) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(24) button {
        border: 3px solid #1E90FF !important;
    }

    /* [健康/創作] 灰色線框：3, 8, 12, 14, 18, 23 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(8) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(12) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(14) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(18) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(23) button {
        border: 3px solid #D3D3D3 !important;
    }
</style>
"""
st.markdown(bingo_style, unsafe_allow_html=True)

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
