import streamlit as st
import numpy as np

# 1. 產品內容定義 (24格 + 1格核心)
tasks = [
    "Python 自動化腳本", "MJ UI 風格指南", "數據驅動調研", "首筆歐元/美金收入", "遠端工作 4hr+",
    "GSheets 串接 App", "LLM 輔助 PRD", "User Flow 測試", "法文技術面試", "移動式設備配置",
    "API 串接實作", "GitHub 提交 10+", "Solo Evolution", "定義北極星指標", "英文作品集網站",
    "Firefly 圖片合成", "A/B Testing 報告", "MVP 產品上線", "加入國際技術社群", "克服異地辦公危機",
    "Rive 互動組件", "AI UX Writing", "非同步溝通模式", "LinkedIn 海外推薦", "獲得遠端合約"
]

# 2. 頁面設定
st.set_page_config(page_title="Solo Evolution Bingo", layout="centered")
st.title("🚀 職涯進化：數位遊牧賓果")
st.write("點擊你已達成的里程碑，解鎖你的數位遊牧地圖！")

# 3. 初始化狀態 (State Management)
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)

# 4. 連線判定邏輯 (Algorithm)
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# 5. UI 佈局 (CSS 注入優化視覺)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 100px;
        white-space: normal;
        word-wrap: break-word;
        border-radius: 10px;
        font-size: 14px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 6. 渲染 5x5 矩陣
lines_completed = check_bingo(st.session_state.board_state)

cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        # 根據狀態決定按鈕樣式
        btn_label = tasks[i]
        if st.session_state.board_state[row, col]:
            button_type = "primary" # 已達成
            label = f"✅\n{btn_label}"
        else:
            button_type = "secondary" # 未達成
            label = btn_label
            
        if st.button(label, key=f"btn_{i}", type=button_type):
            st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
            st.rerun()

# 7. 成就回饋
st.divider()
st.subheader(f"目前連線數：{lines_completed}")

if lines_completed > 0:
    st.balloons()
    st.success(f"太棒了！你已經解鎖了 {lines_completed} 條職涯連線！")
