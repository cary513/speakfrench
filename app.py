import streamlit as st
import numpy as np
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Solo Evolution 2026", layout="centered", initial_sidebar_state="collapsed")

# --- 2. 注入 CSS (維持你要求的高窄長方形與五色規範) ---
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    .header-box { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .flip-clock { display: flex; gap: 4px; background: #222; padding: 8px; border-radius: 8px; }
    .flip-digit {
        background: #333; color: #FF4B4B; font-family: monospace;
        font-size: 1.3rem; font-weight: bold; padding: 2px 8px;
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
    /* 此處省略之前定義的五色線框 CSS 邏輯，請保留在你的程式碼中 */
</style>
""", unsafe_allow_html=True)

# --- 3. Google Sheets 連線與資料同步 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # 讀取試算表，若不存在則初始化
    try:
        df = conn.read(worksheet="Solo_Evolution_Bingo", ttl="0s")
        return df
    except:
        # 初始資料結構
        return None

def save_data():
    # 將目前的 session_state 轉成 DataFrame 並存回雲端
    import pandas as pd
    data = {
        "index": list(range(25)),
        "task": st.session_state.custom_tasks,
        "status": st.session_state.board_state.flatten().tolist()
    }
    df = pd.DataFrame(data)
    conn.update(worksheet="Solo_Evolution_Bingo", data=df)

# --- 4. 初始化 Session State ---
if 'custom_tasks' not in st.session_state:
    cloud_df = load_data()
    if cloud_df is not None and not cloud_df.empty:
        st.session_state.custom_tasks = cloud_df['task'].tolist()
        st.session_state.board_state = np.array(cloud_df['status']).reshape(5, 5)
    else:
        st.session_state.custom_tasks = ["目標 " + str(i+1) for i in range(25)]
        st.session_state.board_state = np.zeros((5, 5), dtype=bool)

if 'is_editing' not in st.session_state: st.session_state.is_editing = True
if 'last_lines_count' not in st.session_state: st.session_state.last_lines_count = 0
if 'should_celebrate' not in st.session_state: st.session_state.should_celebrate = False

# --- 5. 頂部 Header 與 倒數計時 ---
t_date = datetime(2027, 1, 1)
days_left = f"{(t_date - datetime.now()).days:03}"
st.markdown(f"""
<div class="header-box">
    <h2 style="margin:0; font-size: 1.6rem;">🎯 進化原力導航盤</h2>
    <div class="flip-clock">
        <div class="flip-digit">{days_left[0]}</div>
        <div class="flip-digit">{days_left[1]}</div>
        <div class="flip-digit">{days_left[2]}</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- 6. 核心連線判定邏輯 ---
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# --- 7. 5x5 矩陣渲染 ---
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        if st.session_state.is_editing:
            st.session_state.custom_tasks[i] = st.text_input(f"G{i}", value=st.session_state.custom_tasks[i], key=f"edit_{i}", label_visibility="collapsed")
        else:
            is_checked = st.session_state.board_state[row, col]
            if st.button(f"{'✅' if is_checked else ''}\n{st.session_state.custom_tasks[i]}", key=f"btn_{i}", type="primary" if is_checked else "secondary"):
                st.session_state.board_state[row, col] = not is_checked
                
                # 判定連線與寫回雲端
                new_lines = check_bingo(st.session_state.board_state)
                if new_lines > st.session_state.last_lines_count:
                    st.session_state.should_celebrate = True
                st.session_state.last_lines_count = new_lines
                save_data() # 即時同步
                st.rerun()

# --- 8. 氣球與底部控制 ---
if not st.session_state.is_editing:
    if st.session_state.should_celebrate:
        st.balloons()
        st.session_state.should_celebrate = False
    if st.session_state.last_lines_count > 0:
        st.success(f"🎊 精彩！達成 {st.session_state.last_lines_count} 條連線！")

st.divider()
c1, c2 = st.columns(2)
if st.session_state.is_editing:
    if c1.button("🎯 鎖定並同步雲端", use_container_width=True):
        save_data()
        st.session_state.is_editing = False
        st.rerun()
else:
    if c1.button("✍️ 修改內容", use_container_width=True):
        st.session_state.is_editing = True
        st.rerun()

if c2.button("🗑️ 重置進度", use_container_width=True):
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
    st.session_state.last_lines_count = 0
    save_data()
    st.rerun()
