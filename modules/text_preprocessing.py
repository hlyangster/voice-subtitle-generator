import re
from prompts import TEXT_PREPROCESSING_PROMPTS
from utils.api_handler import process_with_ai, APIError

class PreprocessingError(Exception):
    """文本預處理錯誤"""
    pass

def validate_text(text):
    """驗證文本是否有效
    
    Args:
        text (str): 待驗證文本
        
    Returns:
        bool: 是否有效
        
    Raises:
        PreprocessingError: 文本無效
    """
    if not text or not text.strip():
        raise PreprocessingError("文本不能為空")
    
    # 可以添加更多驗證邏輯
    return True

def validate_api_key(api_key):
    """驗證 API 金鑰是否有效
    
    Args:
        api_key (str): API 金鑰
        
    Returns:
        bool: 是否有效
        
    Raises:
        PreprocessingError: API 金鑰無效
    """
    if not api_key or not api_key.strip():
        raise PreprocessingError("API 金鑰不能為空")
    
    # 簡單的格式檢查，實際使用中可能需要更嚴格的驗證
    if not re.match(r'^[A-Za-z0-9_\-]+$', api_key.strip()):
        raise PreprocessingError("API 金鑰格式不正確")
    
    return True

def format_processed_text(processed_text):
    """格式化處理後的文本
    
    Args:
        processed_text (str): 處理後的原始文本
        
    Returns:
        str: 格式化後的文本
    """
    # 清理文本，移除多餘空行和無關內容
    lines = processed_text.strip().split('\n')
    result_lines = []
    
    # 標記是否已經開始處理實際內容
    content_started = False
    
    for line in lines:
        # 跳過提示詞說明部分
        if not content_started:
            if line.strip() and not line.startswith('請處理以下逐字稿') and not line.startswith('Please process'):
                content_started = True
            else:
                continue
        
        # 保留實際處理結果
        result_lines.append(line)
    
    # 合併並返回結果
    return '\n'.join(result_lines)

def preprocess_text(text, language, api_key):
    """預處理文本
    
    Args:
        text (str): 原始文本
        language (str): 語言代碼 ("zh" 或 "en")
        api_key (str): Google AI API 金鑰
        
    Returns:
        str: 處理後的文本
        
    Raises:
        PreprocessingError: 處理過程中的錯誤
    """
    try:
        # 驗證輸入
        validate_text(text)
        validate_api_key(api_key)
        
        # 獲取對應語言的提示詞
        prompt = TEXT_PREPROCESSING_PROMPTS.get(language)
        if not prompt:
            raise PreprocessingError(f"不支持的語言: {language}")
        
        # 調用 API 處理文本
        processed_text = process_with_ai("google_ai", prompt, text, api_key)
        
        # 格式化處理結果
        formatted_text = format_processed_text(processed_text)
        
        return formatted_text
        
    except APIError as e:
        raise PreprocessingError(f"API 錯誤: {str(e)}")
    except Exception as e:
        raise PreprocessingError(f"預處理錯誤: {str(e)}")