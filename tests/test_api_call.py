# tests/test_api_call.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_handler import call_google_ai
from prompts import TEXT_PREPROCESSING_PROMPTS

def test_google_ai_call():
    # 從環境變量或直接輸入獲取API金鑰
    api_key = input("請輸入Google API金鑰: ")
    
    # 測試文本
    test_text = "這是一段測試文本。它包含多個句子。這是第三句，我們想看看它是如何被分段的。列舉項目：蘋果、香蕉、橙子、葡萄，這些水果都很美味。"
    
    # 獲取中文提示詞
    prompt = TEXT_PREPROCESSING_PROMPTS["zh"]
    
    try:
        # 調用API
        print("正在調用Google AI API...")
        result = call_google_ai(prompt, test_text, api_key, model="gemini-2.0-flash")
        
        # 打印結果
        print("\n===== API調用結果 =====")
        print(result)
        print("========================")
        
        return True
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    test_google_ai_call()