# modules/openai_utils.py
"""
OpenAI 客戶端工具 - 提供統一的 OpenAI 客戶端創建方法
"""

def get_openai_client(api_key):
    """
    獲取統一的 OpenAI 客戶端
    
    Args:
        api_key: OpenAI API 金鑰
        
    Returns:
        OpenAI 客戶端實例
    """
    from openai import OpenAI
    return OpenAI(api_key=api_key)