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
    st.header("⚙️ 賓果儀表板")
    # 使用 toggle 作為切換開關，更符合「模式切換」的直覺
    is_editing = st.toggle("✍️ 編輯模式", value=st.session_state.edit_mode)
    st.session_state.edit_mode = is_editing
    
    st.divider()
    if not st.session_state.edit_mode:
        if st.button("🗑️ 重置進度"):
            st.session_state.board_state = np.zeros((5, 5), dtype=bool)
            st.session_state.last_lines_count = 0
            st.rerun()
    else:
        st.info("💡 在主畫面編輯文字後，關閉左側「編輯模式」即可鎖定內容並開始挑戰。")

# --- 4. 邏輯函式 ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 5. 主畫面 UI ---
st.title("🎯 2026 人生進化賓果")

# A. 編輯區：僅在編輯模式顯示
if st.session_state.edit_mode:
    st.subheader("📝 修改挑戰內容")
    edit_cols = st.columns(5)
    for i in range(25):
        with edit_cols[i % 5]:
            st.session_state.custom_tasks[i] = st.text_input(
                f"G{i}", value=st.session_state.custom_tasks[i], 
                key=f"edit_in_{i}", label_visibility="collapsed"
            )
    st.warning("⚠️ 編輯中，下方挑戰功能已暫時鎖定。")

# B. 挑戰區：賓果盤渲染
st.divider()
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        task_text = st.session_state.custom_tasks[i]
        is_checked = st.session_state.board_state[row, col]
        display_label = f"{'✅' if (is_checked and not st.session_state.edit_mode) else ''}\n{task_text}"
        
        if st.button(
            display_label, key=f"btn_{i}", 
            type="primary" if (is_checked and not st.session_state.edit_mode) else "secondary",
            disabled=st.session_state.edit_mode # 編輯時不可點擊
        ):
            st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
            st.rerun()

# --- 6. 成就回饋 ---
if not st.session_state.edit_mode:
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
