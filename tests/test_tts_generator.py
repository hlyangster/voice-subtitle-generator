# tests/test_tts_generator.py

import unittest
import os
import json
import tempfile
from pathlib import Path
import shutil
import sys
from unittest.mock import patch, MagicMock

# 確保可以導入專案模組
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from modules.tts_generator import TTSGenerator, TTSGenerationError
from modules import HAILUO_GROUP_ID, TTS_VOICES, TTS_EMOTIONS

class TestTTSGenerator(unittest.TestCase):
    """測試TTS生成器功能"""
    
    def setUp(self):
        """每個測試前執行的設置"""
        # 創建臨時目錄用於測試
        self.temp_dir = tempfile.mkdtemp()
        self.api_key = "test_api_key"  # 測試用的API Key
        self.tts_generator = TTSGenerator(self.api_key, output_dir=self.temp_dir)
        
        # 用於測試的文本
        self.test_text = "這是一個測試文本。---這是另一段測試文本。"
    
    def tearDown(self):
        """每個測試後執行的清理"""
        # 刪除臨時目錄
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """測試初始化功能"""
        # 測試使用預設group_id
        tts = TTSGenerator(self.api_key)
        self.assertEqual(tts.group_id, HAILUO_GROUP_ID)
        
        # 測試自定義group_id
        custom_group_id = "custom_group_id"
        tts = TTSGenerator(self.api_key, group_id=custom_group_id)
        self.assertEqual(tts.group_id, custom_group_id)
        
        # 測試輸出目錄
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_merge_pronunciation_dict(self):
        """測試發音字典合併功能"""
        # 測試空自定義詞條
        merged_dict = self.tts_generator.merge_pronunciation_dict(None)
        self.assertEqual(merged_dict, self.tts_generator.DEFAULT_PRONUNCIATION_DICT)
        
        # 測試自定義詞條
        custom_entries = "字詞1/(zici1),字詞2/(zici2)"
        merged_dict = self.tts_generator.merge_pronunciation_dict(custom_entries)
        
        # 檢查是否包含默認詞條
        for entry in self.tts_generator.DEFAULT_PRONUNCIATION_DICT["tone"]:
            self.assertIn(entry, merged_dict["tone"])
        
        # 檢查是否包含自定義詞條
        self.assertIn("字詞1/(zici1)", merged_dict["tone"])
        self.assertIn("字詞2/(zici2)", merged_dict["tone"])
    
    @patch('requests.post')
    def test_text_to_speech_success(self, mock_post):
        """測試成功的TTS轉換"""
        # 模擬成功的API響應
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "audio": "01020304"  # 16進制的音頻數據
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # 調用TTS轉換
        output_file = os.path.join(self.temp_dir, "test.mp3")
        result = self.tts_generator._text_to_speech(
            "測試文本",
            self.tts_generator.DEFAULT_VOICE_SETTINGS,
            self.tts_generator.DEFAULT_AUDIO_SETTINGS,
            self.tts_generator.DEFAULT_PRONUNCIATION_DICT,
            output_file
        )
        
        # 檢查結果
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        
        # 檢查API調用參數
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {self.api_key}")
        self.assertEqual(kwargs['headers']['Content-Type'], "application/json")
        
        # 檢查請求數據
        request_data = json.loads(kwargs['data'])
        self.assertEqual(request_data['model'], 'speech-01-hd')
        self.assertEqual(request_data['text'], '測試文本')
        self.assertEqual(request_data['voice_setting'], self.tts_generator.DEFAULT_VOICE_SETTINGS)
        self.assertEqual(request_data['audio_setting'], self.tts_generator.DEFAULT_AUDIO_SETTINGS)
        self.assertEqual(request_data['pronunciation_dict'], self.tts_generator.DEFAULT_PRONUNCIATION_DICT)
    
    @patch('requests.post')
    def test_text_to_speech_api_error(self, mock_post):
        """測試API錯誤的處理"""
        # 模擬API錯誤
        mock_post.side_effect = Exception("API error")
        
        # 調用TTS轉換
        output_file = os.path.join(self.temp_dir, "test.mp3")
        result = self.tts_generator._text_to_speech(
            "測試文本",
            self.tts_generator.DEFAULT_VOICE_SETTINGS,
            self.tts_generator.DEFAULT_AUDIO_SETTINGS,
            self.tts_generator.DEFAULT_PRONUNCIATION_DICT,
            output_file
        )
        
        # 檢查結果
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_file))
    
    @patch('modules.tts_generator.TTSGenerator._text_to_speech')
    def test_generate_speech(self, mock_tts):
        """測試生成語音功能"""
        # 模擬成功的TTS轉換，並實際創建文件
        def mock_text_to_speech_side_effect(text, voice_settings, audio_settings, pronunciation_dict, output_filename):
            # 創建一個實際的文件以通過檢查
            with open(output_filename, 'wb') as f:
                f.write(b'dummy audio data')
            return True
        
        mock_tts.side_effect = mock_text_to_speech_side_effect
        
        # 調用生成語音功能
        progress_callback = MagicMock()
        result = self.tts_generator.generate_speech(
            self.test_text,
            voice_name="訓練長",
            emotion="neutral",
            speed=1.0,
            custom_pronunciation="自定義詞條/(zidingyi)",
            progress_callback=progress_callback
        )
        
        # 檢查結果
        mp3_files, zip_path = result
        self.assertEqual(len(mp3_files), 2)  # 應該有兩個MP3文件
        self.assertTrue(os.path.exists(zip_path))
        
        # 檢查進度回調是否被調用
        self.assertGreater(progress_callback.call_count, 0)
    
    @patch('modules.tts_generator.TTSGenerator._text_to_speech')
    def test_generate_speech_error(self, mock_tts):
        """測試生成語音出錯的情況"""
        # 模擬TTS轉換失敗
        mock_tts.return_value = False
        
        # 調用生成語音功能，應該拋出異常
        with self.assertRaises(TTSGenerationError):
            self.tts_generator.generate_speech(
                self.test_text,
                voice_name="訓練長",
                emotion="neutral",
                speed=1.0
            )
    
    def test_invalid_parameters(self):
        """測試無效參數的處理"""
        # 測試無效的語音名稱
        with self.assertRaises(TTSGenerationError):
            self.tts_generator.generate_speech(
                self.test_text,
                voice_name="不存在的語音",
                emotion="neutral",
                speed=1.0
            )
        
        # 測試無效的情緒
        with self.assertRaises(TTSGenerationError):
            self.tts_generator.generate_speech(
                self.test_text,
                voice_name="訓練長",
                emotion="不存在的情緒",
                speed=1.0
            )
        
        # 測試無效的語速
        with self.assertRaises(TTSGenerationError):
            self.tts_generator.generate_speech(
                self.test_text,
                voice_name="訓練長",
                emotion="neutral",
                speed=3.0  # 超出範圍
            )

# 啟動測試
if __name__ == '__main__':
    unittest.main()