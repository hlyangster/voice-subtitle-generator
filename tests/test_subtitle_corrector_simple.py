# tests/test_subtitle_corrector_simple.py
import unittest
import os
import tempfile
import pysrt
import sys
from unittest.mock import patch, MagicMock

# 確保可以導入專案模組
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from modules.subtitle_corrector import SubtitleCorrector

class TestSubtitleCorrector(unittest.TestCase):
    
    def setUp(self):
        """測試前準備工作"""
        # 創建臨時目錄存放測試文件
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 測試用 API 金鑰 (在 mock 模式中不會實際使用)
        self.test_api_key = "test_api_key"
        
        # 創建測試用 SRT 文件
        self.test_srt_path = os.path.join(self.temp_dir.name, "test.srt")
        self.create_test_srt_file(self.test_srt_path)
        
        # 創建測試用逐字稿文件
        self.test_transcript_path = os.path.join(self.temp_dir.name, "test_transcript.txt")
        self.create_test_transcript_file(self.test_transcript_path)
    
    def tearDown(self):
        """測試後清理工作"""
        self.temp_dir.cleanup()
    
    def create_test_srt_file(self, filepath):
        """創建測試用 SRT 文件"""
        subs = pysrt.SubRipFile()
        
        # 添加幾個測試字幕
        subs.append(pysrt.SubRipItem(
            index=1,
            start=pysrt.SubRipTime(0, 0, 0, 0),
            end=pysrt.SubRipTime(0, 0, 5, 0),
            text="這是一個測試字慕"  # 故意寫錯 "字幕" 為 "字慕"
        ))
        
        subs.append(pysrt.SubRipItem(
            index=2,
            start=pysrt.SubRipTime(0, 0, 5, 0),
            end=pysrt.SubRipTime(0, 0, 10, 0),
            text="句子中有錯別字和和重復的詞"  # 故意重複 "和"
        ))
        
        # 保存 SRT 文件
        subs.save(filepath, encoding="utf-8")
    
    def create_test_transcript_file(self, filepath):
        """創建測試用逐字稿文件"""
        transcript = "這是一個測試字幕。句子中有錯別字和重複的詞。"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(transcript)
    
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_init(self, mock_configure, mock_model_class):
        """測試初始化函數"""
        # 設置 mock
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # 初始化 SubtitleCorrector
        corrector = SubtitleCorrector(self.test_api_key)
        
        # 驗證 API 金鑰配置是否被調用
        mock_configure.assert_called_once_with(api_key=self.test_api_key)
        
        # 驗證模型實例化是否正確
        mock_model_class.assert_called_once_with('gemini-2.0-flash-exp')
        
        # 驗證對象屬性設置是否正確
        self.assertEqual(corrector.api_key, self.test_api_key)
        self.assertEqual(corrector.model, mock_model)
    
    def test_parse_srt(self):
        """測試 SRT 解析函數"""
        # 解析測試 SRT 文件
        srt_data = SubtitleCorrector.parse_srt(self.test_srt_path)
        
        # 驗證解析結果
        self.assertIsNotNone(srt_data)
        self.assertEqual(len(srt_data), 2)
        self.assertEqual(srt_data[1]["text"], "這是一個測試字慕")
        self.assertEqual(srt_data[2]["text"], "句子中有錯別字和和重復的詞")
        
        # 測試不存在的文件
        not_exist_path = os.path.join(self.temp_dir.name, "not_exist.srt")
        result = SubtitleCorrector.parse_srt(not_exist_path)
        self.assertIsNone(result)
    
    def test_preprocess_transcript(self):
        """測試逐字稿預處理函數"""
        # 基本文本
        text = "這是一個測試。\n換行之後的文本。"
        processed = SubtitleCorrector.preprocess_transcript(text)
        self.assertEqual(processed, "這是一個測試。 換行之後的文本。")
        
        # 包含 SSML 標籤
        text_with_ssml = "<speak>這是<emphasis>強調</emphasis>文本。</speak>"
        processed = SubtitleCorrector.preprocess_transcript(text_with_ssml)
        self.assertEqual(processed, "這是強調文本。")
        
        # 多餘空格處理
        text_with_spaces = "  多餘   空格  處理  "
        processed = SubtitleCorrector.preprocess_transcript(text_with_spaces)
        self.assertEqual(processed, "多餘 空格 處理")
    
    def test_validate_srt(self):
        """測試 SRT 驗證函數"""
        # 原始 SRT 數據
        original_srt = {
            1: {"time": "00:00:00,000 --> 00:00:05,000", "text": "這是一個測試字慕"},
            2: {"time": "00:00:05,000 --> 00:00:10,000", "text": "句子中有錯別字和和重復的詞"}
        }
        
        # 有效修改 (僅修改文本)
        modified_srt_valid = {
            1: {"time": "00:00:00,000 --> 00:00:05,000", "text": "這是一個測試字幕"},
            2: {"time": "00:00:05,000 --> 00:00:10,000", "text": "句子中有錯別字和重複的詞"}
        }
        
        is_valid, msg = SubtitleCorrector.validate_srt(original_srt, modified_srt_valid)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "驗證通過")
        
        # 無效修改 - 編號不匹配
        modified_srt_invalid_idx = {
            1: {"time": "00:00:00,000 --> 00:00:05,000", "text": "這是一個測試字幕"},
            3: {"time": "00:00:05,000 --> 00:00:10,000", "text": "句子中有錯別字和重複的詞"}
        }
        
        is_valid, msg = SubtitleCorrector.validate_srt(original_srt, modified_srt_invalid_idx)
        self.assertFalse(is_valid)
        self.assertTrue("編號不匹配" in msg)
        
        # 無效修改 - 時間戳被修改
        modified_srt_invalid_time = {
            1: {"time": "00:00:00,000 --> 00:00:05,000", "text": "這是一個測試字幕"},
            2: {"time": "00:00:05,500 --> 00:00:10,000", "text": "句子中有錯別字和重複的詞"}
        }
        
        is_valid, msg = SubtitleCorrector.validate_srt(original_srt, modified_srt_invalid_time)
        self.assertFalse(is_valid)
        self.assertTrue("時間戳被修改" in msg)

    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('google.generativeai.configure')
    def test_correct_subtitles_for_missing_files(self, mock_configure, mock_generate_content):
        """測試文件不存在的情況"""
        # 初始化 SubtitleCorrector
        corrector = SubtitleCorrector(self.test_api_key)
        
        # 測試逐字稿文件不存在
        not_exist_path = os.path.join(self.temp_dir.name, "not_exist.txt")
        error, srt, reports = corrector.correct_subtitles(not_exist_path, self.test_srt_path)
        self.assertIsNotNone(error)
        self.assertTrue("找不到逐字稿檔案" in error)
        
        # 測試SRT文件不存在
        error, srt, reports = corrector.correct_subtitles(self.test_transcript_path, not_exist_path)
        self.assertIsNotNone(error)
        self.assertTrue("找不到口語稿檔案" in error)

if __name__ == '__main__':
    unittest.main()