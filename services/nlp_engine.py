import spacy
import streamlit as st

class NLPEngine:
    @st.cache_resource
    def get_model(self):
        # 載入模型，建議使用小型模型以提升載入速度
        return spacy.load("fr_core_news_md")

nlp_engine = NLPEngine()
