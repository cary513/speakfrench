import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import spacy

# 因為我們已經在 requirements.txt 中強制安裝了模型，
# 這裡只需要直接載入即可，不需要再寫下載邏輯
@st.cache_resource
def load_nlp():
    return spacy.load("fr_core_news_md")

nlp = load_nlp()
# 設定頁面配置
st.set_page_config(page_title="VocaGraph Prototype", layout="wide")

# 加載法語模型
@st.cache_resource
def load_nlp():
    return spacy.load("fr_core_news_md")

nlp = load_nlp()

# 模擬語義數據庫 (實際開發可串接 ConceptNet API)
mock_data = {
    "travail": {
        "verbs": ["postuler", "travailler", "démissionner"],
        "context": ["bureau", "télétravail", "entreprise"],
        "slang": ["boulot", "taf"]
    },
    "manger": {
        "verbs": ["cuisiner", "déjeuner", "dîner"],
        "context": ["restaurant", "cuisine", "nourriture"],
        "slang": ["bouffer"]
    }
}

st.title("🌌 VocaGraph: 法語語義星系原型")
st.sidebar.header("控制面板")
target_word = st.sidebar.text_input("輸入法語單字 (如: travail, manger)", "travail").lower()

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("語義關聯圖譜 (Semantic Galaxy)")
    
    if target_word in mock_data:
        # 建立 NetworkX 圖表
        G = nx.Graph()
        G.add_node(target_word, size=30, color="#FF4B4B", label=target_word.upper())
        
        for category, words in mock_data[target_word].items():
            for word in words:
                G.add_node(word, size=15, title=category)
                G.add_edge(target_word, word, weight=1)

        # 轉化為 Pyvis 互動圖表
        net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
        net.from_nx(G)
        net.repulsion()
        
        # 儲存並讀取 HTML
        path = "html_graph.html"
        net.save_graph(path)
        with open(path, 'r', encoding='utf-8') as f:
            html_data = f.read()
        components.html(html_data, height=550)
    else:
        st.warning("目前僅支持示範單字：travail, manger")

with col2:
    st.subheader("AI 語境提取分析")
    
    sample_text = st.text_area("模擬抓取的法語新聞/論壇文本：", 
                               "Le télétravail change la nature du travail en entreprise. "
                               "Beaucoup de gens préfèrent bosser au café.")
    
    if st.button("執行 NLP 分析"):
        doc = nlp(sample_text)
        
        st.write("**提取到的動詞與標籤：**")
        for token in doc:
            if token.pos_ == "VERB" or token.lemma_ == target_word:
                st.info(f"詞條: {token.text} | 原形: {token.lemma_} | 詞性: {token.pos_}")
        
        # 模擬口語辨識
        if "bosser" in sample_text or "boulot" in sample_text:
            st.success("💡 偵測到道地口語 (Argot): 'bosser' -> 意同 'travailler'")

st.divider()
st.caption("Solo Evolution - 法語學習開發原型 v1.0")
