import streamlit as st
import numpy as np

st.markdown("""
<style>
    /* 1. 基礎格子樣式：統一所有格子的大小與基礎屬性 */
    .stButton>button {
        width: 100%;
        height: 110px; /* 確保高度統一 */
        background-color: white;
        color: #333333;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.2s;
        border: 3px solid #D3D3D3; /* 預設線框粗度統一為 3px */
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* 2. [核心]：第 13 格 (中心) - 僅更換紅色線框，不放大 */
    div[data-testid="column"]:nth-child(13) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(13) button {
        border: 3px solid #FF4B4B !important;
        background-color: #FFF5F5; /* 輕微底色區分核心，但不改變大小 */
    }

    /* 3. [生活/旅遊]：橘色線框 (外圍與四角) */
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

    /* 4. [職涯/目標]：藍色線框 (對稱分佈) */
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

    /* 5. [健康/創作]：灰色線框 (中間十字軸) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(8) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(12) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(14) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(18) button,
    div[data-testid="stHorizontalBlock"] > div:nth-child(23) button {
        border: 3px solid #D3D3D3 !important;
    }

    /* 狀態回饋：點擊後維持大小不變，僅改變背景色 */
    .stButton>button:active, .stButton>button:focus {
        background-color: #F8F9FB !important;
        border-style: solid !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. 注入 CSS
st.markdown(bingo_style, unsafe_allow_html=True)

# 1. 頁面設定與標題
st.set_page_config(page_title="Custom Bingo Creator", layout="centered")
st.title("🎯 2026人生賓果清單")
st.write("輸入你的 25 個挑戰目標，打造專屬的進化地圖！")

# 2. 初始化狀態
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)
if 'last_lines_count' not in st.session_state:
    st.session_state.last_lines_count = 0
if 'custom_tasks' not in st.session_state:
    # 預設內容 (方便測試)
    st.session_state.custom_tasks = [f"任務 {i+1}" for i in range(25)]
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = True

# 3. 側邊欄：自訂內容輸入區
with st.sidebar:
    st.header("⚙️ 設定你的賓果格")
    if st.button("切換 編輯 / 挑戰 模式"):
        st.session_state.edit_mode = not st.session_state.edit_mode
    
    st.divider()
    if st.session_state.edit_mode:
        st.subheader("編輯 25 格內容")
        for i in range(25):
            st.session_state.custom_tasks[i] = st.text_input(
                f"格子 {i+1}", 
                value=st.session_state.custom_tasks[i], 
                key=f"input_{i}"
            )
    else:
        st.success("編輯模式已關閉，現在可以開始挑戰！")
        if st.button("重置所有進度"):
            st.session_state.board_state = np.zeros((5, 5), dtype=bool)
            st.session_state.last_lines_count = 0
            st.rerun()

# 4. 連線判定函式
def check_bingo(state):
    rows = np.all(state, axis=1).sum()
    cols = np.all(state, axis=0).sum()
    diag1 = np.all(np.diag(state))
    diag2 = np.all(np.diag(np.fliplr(state)))
    return int(rows + cols + diag1 + diag2)

# 5. UI 渲染
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 90px; border-radius: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 顯示賓果盤
cols = st.columns(5)
for i in range(25):
    row, col = divmod(i, 5)
    with cols[col]:
        task_text = st.session_state.custom_tasks[i]
        is_checked = st.session_state.board_state[row, col]
        
        if st.button(
            f"{'✅' if is_checked else ''}\n{task_text}", 
            key=f"btn_{i}", 
            type="primary" if is_checked else "secondary",
            disabled=st.session_state.edit_mode # 編輯模式下不能點選挑戰
        ):
            st.session_state.board_state[row, col] = not st.session_state.board_state[row, col]
            st.rerun()

# 6. 成就回饋邏輯
current_lines = check_bingo(st.session_state.board_state)

if not st.session_state.edit_mode:
    st.divider()
    st.subheader(f"目前連線數：{current_lines}")
    
    if current_lines > 0 and current_lines > st.session_state.last_lines_count:
        st.balloons()
        st.success(f"🎉 賀！達成新連線！目前總計：{current_lines}")
        st.session_state.last_lines_count = current_lines
    elif current_lines < st.session_state.last_lines_count:
        st.session_state.last_lines_count = current_lines
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

# 3. 初始化狀態 (新增一個追蹤慶祝狀態的變數)
if 'board_state' not in st.session_state:
    st.session_state.board_state = np.zeros((5, 5), dtype=bool)

# 新增：紀錄「上一次」看到的連線數，預設為 0
if 'last_lines_count' not in st.session_state:
    st.session_state.last_lines_count = 0

# ... (中間的連線判定與 UI 代碼不變) ...
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
# 7. 成就回饋邏輯
st.divider()
current_lines = check_bingo(st.session_state.board_state)

# 邏輯判斷：
# 1. 目前連線數 > 0 (達成連線條件)
# 2. 目前連線數 > 上次紀錄的連線數 (代表這是「新達成」的連線)
if current_lines > 0 and current_lines > st.session_state.last_lines_count:
    st.balloons()
    st.success(f"🎊 恭喜！你達成了一條新連線！目前總計：{current_lines} 條")
    # 更新紀錄，這樣下次點擊時，如果連線數沒增加，就不會再噴氣球
    st.session_state.last_lines_count = current_lines

elif current_lines < st.session_state.last_lines_count:
    # 如果使用者取消勾選導致連線減少，同步更新紀錄，下次連回來時才能再觸發慶祝
    st.session_state.last_lines_count = current_lines

# 顯示目前的狀態文字
if current_lines > 0:
    st.write(f"穩定發展中！目前已達成 {current_lines} 條連線")
else:
    st.write("🏃 加油！連成第一條線來解鎖慶祝動畫")
