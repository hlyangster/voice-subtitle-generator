# test_environment.py
print("環境測試開始...")

# 測試基本庫是否正確安裝
try:
    import gradio as gr
    print("✓ Gradio 導入成功")
    
    import numpy as np
    print("✓ NumPy 導入成功")
    
    import requests
    print("✓ Requests 導入成功")
    
    import dotenv
    print("✓ python-dotenv 導入成功")
    
    # 如果您已經創建了自己的模組，也可以嘗試導入
    # 例如：from modules.text_preprocessing import text_preprocessing
    # print("✓ 文本預處理模組導入成功")
    
    print("所有庫導入測試通過！")
    
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    
print("環境測試完成")