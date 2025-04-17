# tests/test_preprocessing.py
import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.text_preprocessing import preprocess_text, validate_text, validate_api_key, PreprocessingError
from utils.api_handler import APIError

class TestTextPreprocessing(unittest.TestCase):
    
    def test_validate_text(self):
        # 測試空文本
        with self.assertRaises(PreprocessingError):
            validate_text("")
        
        # 測試有效文本
        self.assertTrue(validate_text("這是一段測試文本。"))
    
    def test_validate_api_key(self):
        # 測試空API金鑰
        with self.assertRaises(PreprocessingError):
            validate_api_key("")
        
        # 測試格式不正確的API金鑰
        with self.assertRaises(PreprocessingError):
            validate_api_key("invalid key with spaces!")
        
        # 測試有效API金鑰
        self.assertTrue(validate_api_key("valid_api_key_123"))
    
    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY"), "需要設置GOOGLE_API_KEY環境變量")
    def test_preprocess_text_integration(self):
        # 集成測試 - 需要有效的API金鑰
        api_key = os.getenv("GOOGLE_API_KEY")
        sample_text = "這是一段測試文本。它應該被正確分段。這是第三句，比較長，應該被分成多個部分。"
        
        result = preprocess_text(sample_text, "zh", api_key)
        
        # 檢查結果是否包含預期的格式
        self.assertIn("---", result)
        
        # 檢查是否有分段
        segments = [s for s in result.split("---") if s.strip()]
        self.assertGreater(len(segments), 1)

if __name__ == "__main__":
    unittest.main()