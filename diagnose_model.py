import os
import google.generativeai as genai

# 確保載入環境變數
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("錯誤：未找到 GOOGLE_API_KEY")
else:
    genai.configure(api_key=api_key)
    
    print("--- 檢查可用的模型 ---")
    try:
        models = genai.list_models()
        for m in models:
            # 檢查支援 generate_content 的模型
            if 'generateContent' in m.supported_generation_methods:
                print(f"找到可用模型: {m.name}")
    except Exception as e:
        print(f"列出模型時發生錯誤: {e}")
