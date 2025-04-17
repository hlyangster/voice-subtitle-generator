# utils/api_handler.py

import requests
import json
import os
# from dotenv import load_dotenv # <-- REMOVE THIS

# 加載環境變量
# load_dotenv() # <-- REMOVE THIS

class APIError(Exception):
    """API 調用錯誤"""
    pass

# --- Improved call_google_ai ---
def call_google_ai(prompt: str, text: str, api_key: str, model: str = "gemini-1.5-flash") -> str: # Changed default model, added type hints
    """調用 Google AI API (Generative Language API) 進行文本處理.

    Args:
        prompt (str): 提示詞模板 (應該包含一個 {text} 佔位符).
        text (str): 待處理文本.
        api_key (str): Google AI API 金鑰.
        model (str): 模型名稱，例如 "gemini-1.5-flash", "gemini-1.5-pro".

    Returns:
        str: 模型生成的文本.

    Raises:
        APIError: API 調用或響應處理失敗.
        ValueError: 如果 API Key 未提供.
    """
    if not api_key:
         # Raise ValueError for missing key, as it's a prerequisite, not an API error
         raise ValueError("Google AI API 金鑰未提供。")
    if not prompt:
         raise ValueError("提示詞模板 (prompt) 為空。")
    # Text can be empty, depending on the prompt's design

    try:
        # 構建完整提示詞 (Safely format)
        full_prompt = prompt.format(text=text)
    except KeyError:
         # If prompt doesn't contain {text}, handle gracefully or raise error
         print(f"警告: 提供的提示詞模板未包含 '{{text}}' 佔位符。將直接使用模板。")
         # Decide: raise error or use prompt as is? Using prompt as is for now.
         full_prompt = prompt
         # If text placeholder is required:
         # raise ValueError("提示詞模板必須包含 '{text}' 佔位符。")

    # API 端點 (使用 v1beta, 確認這是否是最新或推薦的版本)
    # Models list: https://ai.google.dev/models/gemini
    # Check if the model requires 'tunedModels' endpoint etc.
    # Assuming standard model endpoint for now.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # 請求頭
    headers = {
        "Content-Type": "application/json",
        # Authorization header is NOT used here, key is a query parameter
    }

    # 請求參數 (API Key)
    params = {
        "key": api_key
    }

    # 請求體
    # Reference: https://ai.google.dev/docs/rest_api_reference
    data = {
        "contents": [
            {
                "role": "user", # Specify role
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,  # Lower temp for more deterministic output
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 8192, # Set a reasonable max token limit if needed
            # "stopSequences": ["..."] # Optional stop sequences
        },
        # Optional Safety Settings:
        # "safetySettings": [
        #    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" }
        # ]
    }

    try:
        print(f"調用 Google AI API: model={model}, url={url}") # Log call
        # Add timeout to the request
        response = requests.post(url, headers=headers, params=params, json=data, timeout=90) # 90 seconds timeout

        # Check for non-200 status codes explicitly
        if response.status_code != 200:
             # Try to get error details from the response body if possible
             error_details = ""
             try:
                  error_json = response.json()
                  error_details = error_json.get('error', {}).get('message', response.text)
             except json.JSONDecodeError:
                  error_details = response.text # Use raw text if not JSON
             raise APIError(f"API 請求失敗 (HTTP {response.status_code}): {error_details}")

        # --- Process successful response (status code 200) ---
        result = response.json()

        # Validate response structure and check for safety blocks or empty results
        if not result.get("candidates"):
            # Check for promptFeedback for blockage reasons
            block_reason = result.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                 raise APIError(f"API 請求被阻止，原因: {block_reason}")
            else:
                 # Empty response without blockage
                 print("警告: API 返回了空的 'candidates' 列表。")
                 # Decide what to return: empty string or raise error?
                 # Returning empty string might be safer for downstream processing.
                 return "" # Return empty string for no valid candidate

        # Extract generated text from the first candidate
        try:
            first_candidate = result["candidates"][0]
            # Check finishReason (e.g., "STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER")
            finish_reason = first_candidate.get("finishReason", "UNKNOWN")
            if finish_reason != "STOP" and finish_reason != "MAX_TOKENS":
                 # Log or potentially raise error for non-standard finish reasons
                 print(f"警告: 生成完成原因 '{finish_reason}' (非 STOP 或 MAX_TOKENS)。可能存在安全問題或引用問題。")
                 # Check safety ratings if needed: first_candidate.get("safetyRatings", [])

            generated_text = first_candidate["content"]["parts"][0]["text"]
            print(f"成功從 Google AI API 獲取響應 (完成原因: {finish_reason})。")
            return generated_text.strip() # Return stripped text

        except (KeyError, IndexError, TypeError) as e:
            # Handle errors in navigating the expected JSON structure
            print(f"解析 API 成功響應時出錯: {e}")
            print(f"接收到的 JSON 結構: {json.dumps(result, indent=2)}") # Log the structure
            raise APIError(f"API 成功響應解析錯誤: {str(e)}")

    except requests.exceptions.Timeout:
         raise APIError(f"API 請求超時 (超過 90 秒)。")
    except requests.exceptions.RequestException as e:
         # Handle connection errors, etc.
         raise APIError(f"API 網絡請求錯誤: {str(e)}")
    # Removed redundant JSONDecodeError catch, handled by status code check or RequestException
    # Removed redundant broad Exception catch, specific errors handled above

# --- process_with_ai function seems fine, acts as a dispatcher ---
def process_with_ai(service: str, prompt: str, text: str, api_key: str, **kwargs) -> str: # Added type hints
    """統一的 AI 模型調用介面.

    Args:
        service (str): 服務類型 (目前僅支持 "google_ai").
        prompt (str): 提示詞模板.
        text (str): 待處理文本.
        api_key (str): 對應服務的 API 金鑰.
        **kwargs: 特定服務的額外參數 (例如 'model' for google_ai).

    Returns:
        str: AI 模型處理後的文本.

    Raises:
        ValueError: 如果服務不支持或缺少必要參數 (如 api_key).
        APIError: 如果底層 API 調用失敗.
    """
    if service == "google_ai":
        # Default to a known stable model if not provided
        model = kwargs.get("model", "gemini-1.5-flash")
        if not api_key:
             # Propagate the ValueError from the underlying function if key is missing
             raise ValueError("調用 Google AI 需要提供 api_key。")
        try:
            # Pass only relevant args
            return call_google_ai(prompt=prompt, text=text, api_key=api_key, model=model)
        except ValueError as ve: # Catch potential ValueErrors from call_google_ai
             raise ve
        except APIError as ae: # Propagate APIError
             raise ae
        except Exception as e: # Catch unexpected errors during the call
             import traceback
             print(f"調用 process_with_ai (google_ai) 時發生未知錯誤: {traceback.format_exc()}")
             raise APIError(f"調用 google_ai 時發生未知錯誤: {e}") from e
    else:
        raise ValueError(f"不支持的服務類型: {service}")