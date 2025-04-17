# tests/test_srt_generator_simple.py
import unittest
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock

# 確保可以導入專案模組
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from modules.srt_generator import SRTGenerator

class TestSRTGenerator(unittest.TestCase):
    
    def setUp(self):
        """測試前準備工作"""
        # 創建臨時目錄存放測試文件
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 創建測試用音頻文件 (只是一個空文件)
        self.test_audio_path = os.path.join(self.temp_dir.name, "test_audio.mp3")
        with open(self.test_audio_path, "wb") as f:
            f.write(b"dummy_audio_data")
        
        # 測試用逐字稿
        self.test_transcript = "這是一個測試字幕內容。這是第二句，用於檢查分段功能。"
    
    def tearDown(self):
        """測試後清理工作"""
        self.temp_dir.cleanup()
    
    def test_init(self):
        """測試初始化函數"""
        # 測試基本初始化
        generator = SRTGenerator(temp_dir=self.temp_dir.name)
        self.assertEqual(generator.temp_dir, self.temp_dir.name)
        
        # 檢查創建的目錄
        self.assertTrue(os.path.exists(self.temp_dir.name))
    
    @patch('subprocess.run')
    def test_generate_srt_from_transcript(self, mock_run):
        """測試從逐字稿生成SRT的函數"""
        # 設置模擬返回值
        mock_process = MagicMock()
        mock_process.stdout = "10.0"
        mock_run.return_value = mock_process
        
        generator = SRTGenerator(temp_dir=self.temp_dir.name)
        
        # 指定輸出文件
        output_file = os.path.join(self.temp_dir.name, "output.srt")
        
        # 調用測試函數
        success, srt_path = generator.generate_srt_from_transcript(
            self.test_audio_path,
            self.test_transcript,
            output_file
        )
        
        # 驗證結果
        self.assertTrue(success)
        self.assertEqual(srt_path, output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # 檢查文件內容
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 檢查SRT格式的基本要素
            self.assertIn("-->", content)  # 包含時間標記
            self.assertIn("1", content)    # 包含編號
            self.assertIn("00:", content)  # 包含時間格式
    
    def test_generate_srt_nonexistent_audio(self):
        """測試使用不存在的音頻文件"""
        generator = SRTGenerator(temp_dir=self.temp_dir.name)
        
        non_existent_path = os.path.join(self.temp_dir.name, "non_existent.mp3")
        output_file = os.path.join(self.temp_dir.name, "error_output.srt")
        
        # 調用測試函數
        success, error_message = generator.generate_srt_from_transcript(
            non_existent_path,
            self.test_transcript,
            output_file
        )
        
        # 驗證結果
        self.assertFalse(success)
        self.assertIn("找不到音頻檔案", error_message)

if __name__ == '__main__':
    unittest.main()