import streamlit as st
import numpy as np

# --- 1. 頁面配置與五色線框 CSS (針對 Key 精確鎖定) ---
st.markdown("""
<style>
    /* 1. 基礎格子樣式 */
    .stButton>button {
        width: 100%;
        height: 110px;
        background-color: white;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3; /* 預設灰色 */
        white-space: normal;
        word-wrap: break-word;
    }

    /* 2. [紅色 - 核心] 第 13 格 (編號 12) */
    div[data-testid="stButton"] > button[key="btn_12"] {
        border: 3px solid #FF4B4B !important;
        background-color: #FFF5F5 !important;
    }

    /* 3. [橘色 - 生活旅遊] 左右兩行 (0,5,10,15,20 和 4,9,14,19,24) */
    div[data-testid="stButton"] > button[key="btn_0"], div[data-testid="stButton"] > button[key="btn_5"],
    div[data-testid="stButton"] > button[key="btn_10"], div[data-testid="stButton"] > button[key="btn_15"],
    div[data-testid="stButton"] > button[key="btn_20"], div[data-testid="stButton"] > button[key="btn_4"],
    div[data-testid="stButton"] > button[key="btn_9"], div[data-testid="stButton"] > button[key="btn_14"],
    div[data-testid="stButton"] > button[key="btn_19"], div[data-testid="stButton"] > button[key="btn_24"] {
        border: 3px solid #FFA500 !important;
    }

    /* 4. [藍色 - 職涯目標] (1,3,6,8,16,18,21,23) */
    div[data-testid="stButton"] > button[key="btn_1"], div[data-testid="stButton"] > button[key="btn_3"],
    div[data-testid="stButton"] > button[key="btn_6"], div[data-testid="stButton"] > button[key="btn_8"],
    div[data-testid="stButton"] > button[key="btn_16"], div[data-testid="stButton"] > button[key="btn_18"],
    div[data-testid="stButton"] > button[key="btn_21"], div[data-testid="stButton"] > button[key="btn_23"] {
        border: 3px solid #1E90FF !important;
    }

    /* 5. [灰色 - 創作作品] 中間十字 (2,7,11,13,17,22) */
    div[data-testid="stButton"] > button[key="btn_2"], div[data-testid="stButton"] > button[key="btn_7"],
    div[data-testid="stButton"] > button[key="btn_11"], div[data-testid="stButton"] > button[key="btn_13"],
    div[data-testid="stButton"] > button[key="btn_17"], div[data-testid="stButton"] > button[key="btn_22"] {
        border: 3px solid #D3D3D3 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 側邊欄與模式控制 (原位修改邏輯) ---
with st.sidebar:
    st.header("⚙️ 賓果儀表板")
    
    # 使用 radio 或 toggle 來讓狀態更明確，避免按鈕跳轉感的誤解
    mode_label = "✍️ 正在編輯內容" if st.session_state.edit_mode else "🎯 正在挑戰中"
    if st.checkbox(mode_label, value=st.session_state.edit_mode, key="mode_toggle"):
        st.session_state.edit_mode = True
    else:
        st.session_state.edit_mode = False

    st.divider()
    
    if st.session_state.edit_mode:
        st.info("💡 修改說明：在下方編輯區輸入完畢後，取消勾選左側「正在編輯」即可開始挑戰。")
    else:
        if st.button("🗑️ 重置所有進度"):
            st.session_state.board_state = np.zeros((5, 5), dtype=bool)
            st.session_state.last_lines_count = 0
            st.rerun()

# --- 4. 主畫面內容區 (編輯與顯示整合) ---
if st.session_state.edit_mode:
    st.subheader("📝 編輯你的 25 格願望清單")
    # 使用 columns 讓編輯區不要太長
    edit_cols = st.columns(5)
    for i in range(25):
        with edit_cols[i % 5]:
            st.session_state.custom_tasks[i] = st.text_input(
                f"格子 {i+1}", 
                value=st.session_state.custom_tasks[i], 
                key=f"edit_in_{i}",
                label_visibility="collapsed" # 隱藏標籤讓畫面更乾淨
            )
else:
    st.write("點擊格子紀錄成就，連成一線即可解鎖氣球慶祝！")

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
