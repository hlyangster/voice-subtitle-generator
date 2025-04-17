import requests
import json
import os
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

class APIError(Exception):
    """API 調用錯誤"""
    pass

def call_google_ai(prompt, text, api_key, model="gemini-2.0-flash"):
    """調用 Google AI API 進行文本處理
    
    Args:
        prompt (str): 提示詞模板
        text (str): 待處理文本
        api_key (str): Google AI API 金鑰
        model (str): 模型名稱，默認為 "gemini-2.0-flash"
        
    Returns:
        str: 處理後的文本
        
    Raises:
        APIError: API 調用失敗
    """
    # 構建完整提示詞
    full_prompt = prompt.format(text=text)
    
    # API 端點
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    # 請求頭
    headers = {
        "Content-Type": "application/json",
    }
    
    # 請求參數
    params = {
        "key": api_key
    }
    
    # 請求體
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40
        }
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()  # 如果狀態碼不是 200，拋出異常
        
        result = response.json()
        
        # 檢查是否有有效響應
        if "candidates" not in result or not result["candidates"]:
            raise APIError("API 返回無效響應")
        
        # 提取生成的文本
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return generated_text
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"API 請求錯誤: {str(e)}")
    except (KeyError, IndexError) as e:
        raise APIError(f"API 響應解析錯誤: {str(e)}")
    except json.JSONDecodeError as e:
        raise APIError(f"JSON 解析錯誤: {str(e)}")
    except Exception as e:
        raise APIError(f"未知錯誤: {str(e)}")

def process_with_ai(service, prompt, text, api_key, **kwargs):
    """統一的 API 調用介面
    
    Args:
        service (str): 服務類型，如 "google_ai"
        prompt (str): 提示詞
        text (str): 待處理文本
        api_key (str): API 金鑰
        **kwargs: 其他參數
        
    Returns:
        結果取決於服務類型
        
    Raises:
        ValueError: 不支持的服務
        APIError: API 調用錯誤
    """
    if service == "google_ai":
        model = kwargs.get("model", "gemini-2.0-flash")
        return call_google_ai(prompt, text, api_key, model)
    else:
        raise ValueError(f"不支持的服務: {service}")