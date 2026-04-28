import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import json

# 初始化 OpenAI 客戶端 (或使用 Claude API)
client = OpenAI(api_key="你的API_KEY")

def get_word_info(word):
    # 調用 LLM 取得單字詳細資訊
    response = client.chat.completions.create(
        model="gpt-4o", # 或 claude-3-5-sonnet
        messages=[
            {"role": "system", "content": "You are a dictionary assistant. Return JSON only."},
            {"role": "user", "content": f"Explain the word: {word} in Traditional Chinese."}
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def play_audio(word, lang='fr'):
    # 生成語音檔案
    tts = gTTS(text=word, lang=lang)
    tts.save("temp_audio.mp3")
    return "temp_audio.mp3"

# --- Streamlit UI 介面 ---
st.title("AI 語言學習卡片")

word_input = st.text_input("輸入你想學習的單字 (法文或英文):")

if word_input:
    # 1. 取得 AI 解析資料
    data = get_word_info(word_input)
    
    # 2. 顯示結果
    st.subheader(f"{data['word']} [{data['phonetic']}]")
    st.write(f"**意思：** {data['meaning']}")
    st.info(f"**例句：** {data['example_sentence']}\n\n({data['sentence_translation']})")
    
    # 3. 發音功能
    audio_path = play_audio(word_input)
    audio_file = open(audio_path, 'rb')
    st.audio(audio_file.read(), format='audio/mp3')
