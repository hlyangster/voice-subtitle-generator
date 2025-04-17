# tests/test_integration.py
import unittest
import os
import tempfile
import zipfile
import time
import sys
from unittest.mock import patch, MagicMock

# 確保可以導入專案模組
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 導入需要測試的函數
from app import generate_tts, generate_subtitle

class TestIntegration(unittest.TestCase):
    """整合測試：測試語音生成與字幕校正的端到端流程"""
    
    def setUp(self):
        """測試前準備工作"""
        # 創建臨時目錄
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 測試數據
        self.test_text = "這是一個測試文本，用於生成語音和字幕。"
        self.test_api_key = "test_api_key"
        self.test_voice = "訓練長"
        self.test_emotion = "neutral"
        self.test_speed = 1.0
        self.test_custom_pronunciation = ""
        self.batch_size = 20
        
        # 創建模擬的音頻ZIP文件
        self.test_zip_path = os.path.join(self.temp_dir.name, "test_audio.zip")
        self._create_test_audio_zip(self.test_zip_path)
        
        # 創建模擬的逐字稿文件
        self.test_transcript_path = os.path.join(self.temp_dir.name, "test_transcript.txt")
        with open(self.test_transcript_path, "w", encoding="utf-8") as f:
            f.write(self.test_text)
    
    def tearDown(self):
        """測試後清理工作"""
        self.temp_dir.cleanup()
    
    def _create_test_audio_zip(self, zip_path):
        """創建測試用的音頻ZIP文件"""
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # 創建一個空的MP3文件
            mp3_path = os.path.join(self.temp_dir.name, "test.mp3")
            with open(mp3_path, 'wb') as f:
                f.write(b'dummy_mp3_content')
            zipf.write(mp3_path, os.path.basename(mp3_path))
    
    @patch('modules.tts_generator.TTSGenerator')
    def test_generate_tts(self, mock_tts_generator_class):
        """測試語音生成函數"""
        # 設置模擬的TTSGenerator
        mock_tts_generator = MagicMock()
        mock_tts_generator_class.return_value = mock_tts_generator
        
        # 模擬生成的MP3文件列表和ZIP文件路徑
        mp3_files = [os.path.join(self.temp_dir.name, f"chunk_{i}.mp3") for i in range(3)]
        zip_path = os.path.join(self.temp_dir.name, "audio.zip")
        
        # 創建這些文件
        for mp3_file in mp3_files:
            with open(mp3_file, 'wb') as f:
                f.write(b'dummy_mp3_content')
        
        with open(zip_path, 'wb') as f:
            f.write(b'dummy_zip_content')
        
        # 設置模擬的generate_speech方法返回值
        mock_tts_generator.generate_speech.return_value = (mp3_files, zip_path)
        
        # 調用generate_tts函數
        status, file_list, output_zip, transcript_file = generate_tts(
            self.test_text,
            self.test_api_key,
            self.test_voice,
            self.test_emotion,
            self.test_speed,
            self.test_custom_pronunciation
        )
        
        # 驗證結果
        self.assertEqual(status, "語音生成成功!")
        self.assertIsNotNone(file_list)
        self.assertEqual(output_zip, zip_path)
        self.assertIsNotNone(transcript_file)
        self.assertTrue(os.path.exists(transcript_file))
        
        # 檢查逐字稿內容
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertEqual(content, self.test_text)
        
        # 驗證TTSGenerator的初始化
        mock_tts_generator_class.assert_called_once()
        
        # 驗證generate_speech方法的調用
        mock_tts_generator.generate_speech.assert_called_once_with(
            self.test_text,
            voice_name=self.test_voice,
            emotion=self.test_emotion,
            speed=self.test_speed,
            custom_pronunciation=self.test_custom_pronunciation,
            progress_callback=unittest.mock.ANY
        )
    
    @patch('modules.srt_generator.SRTGenerator')
    @patch('modules.subtitle_corrector.SubtitleCorrector')
    @patch('zipfile.ZipFile')
    def test_generate_subtitle(self, mock_zipfile, mock_subtitle_corrector_class, mock_srt_generator_class):
        """測試字幕生成與校正函數"""
        # 設置模擬的SRTGenerator
        mock_srt_generator = MagicMock()
        mock_srt_generator_class.return_value = mock_srt_generator
        
        # 設置模擬的SubtitleCorrector
        mock_subtitle_corrector = MagicMock()
        mock_subtitle_corrector_class.return_value = mock_subtitle_corrector
        
        # 模擬初始SRT文件路徑
        initial_srt_path = os.path.join(self.temp_dir.name, "initial.srt")
        with open(initial_srt_path, 'w', encoding='utf-8') as f:
            f.write('dummy srt content')
        
        # 模擬校正後的SRT文件和報告
        mock_srt = MagicMock()
        mock_srt.save = MagicMock()
        reports = ["編號1: 原文: 測試, 修正後: 測試修正"]
        
        # 設置模擬方法的返回值
        mock_srt_generator.generate_srt_from_transcript.return_value = (True, initial_srt_path)
        mock_subtitle_corrector.correct_subtitles.return_value = (None, mock_srt, reports)
        
        # 調用generate_subtitle函數
        status, srt_file, report_file = generate_subtitle(
            self.test_zip_path,
            self.test_transcript_path,
            self.test_api_key,
            self.batch_size
        )
        
        # 驗證結果
        self.assertEqual(status, "字幕生成與校正成功!")
        self.assertIsNotNone(srt_file)
        self.assertIsNotNone(report_file)
        
        # 驗證SRTGenerator的初始化和方法調用
        mock_srt_generator_class.assert_called_once_with(
            temp_dir=str(unittest.mock.ANY),
            api_key=self.test_api_key
        )
        mock_srt_generator.generate_srt_from_transcript.assert_called_once()
        
        # 驗證SubtitleCorrector的初始化和方法調用
        mock_subtitle_corrector_class.assert_called_once_with(self.test_api_key)
        mock_subtitle_corrector.correct_subtitles.assert_called_once_with(
            self.test_transcript_path,
            initial_srt_path,
            self.batch_size
        )
        
        # 驗證保存SRT文件和報告
        mock_srt.save.assert_called_once()
    
    @patch('modules.srt_generator.SRTGenerator')
    @patch('modules.subtitle_corrector.SubtitleCorrector')
    def test_generate_subtitle_failure(self, mock_subtitle_corrector_class, mock_srt_generator_class):
        """測試字幕生成失敗的情況"""
        # 設置模擬的SRTGenerator
        mock_srt_generator = MagicMock()
        mock_srt_generator_class.return_value = mock_srt_generator
        
        # 模擬SRT生成失敗
        mock_srt_generator.generate_srt_from_transcript.return_value = (False, "初始字幕生成失敗: 測試錯誤")
        
        # 調用generate_subtitle函數
        status, srt_file, report_file = generate_subtitle(
            self.test_zip_path,
            self.test_transcript_path,
            self.test_api_key,
            self.batch_size
        )
        
        # 驗證結果
        self.assertTrue("初始字幕生成失敗" in status)
        self.assertIsNone(srt_file)
        self.assertIsNone(report_file)
        
        # 驗證SubtitleCorrector沒有被調用
        mock_subtitle_corrector_class.assert_not_called()
    
    def test_generate_subtitle_missing_files(self):
        """測試缺少輸入文件的情況"""
        # 測試缺少音頻文件
        status, srt_file, report_file = generate_subtitle(
            None,
            self.test_transcript_path,
            self.test_api_key,
            self.batch_size
        )
        
        self.assertTrue("請先生成音頻文件" in status)
        self.assertIsNone(srt_file)
        self.assertIsNone(report_file)
        
        # 測試缺少逐字稿文件
        status, srt_file, report_file = generate_subtitle(
            self.test_zip_path,
            None,
            self.test_api_key,
            self.batch_size
        )
        
        self.assertTrue("找不到逐字稿文件" in status)
        self.assertIsNone(srt_file)
        self.assertIsNone(report_file)
        
        # 測試缺少API金鑰
        status, srt_file, report_file = generate_subtitle(
            self.test_zip_path,
            self.test_transcript_path,
            "",
            self.batch_size
        )
        
        self.assertTrue("請提供 Google Gemini API 金鑰" in status)
        self.assertIsNone(srt_file)
        self.assertIsNone(report_file)
    
    @patch('zipfile.ZipFile')
    def test_generate_subtitle_empty_zip(self, mock_zipfile):
        """測試ZIP文件中沒有MP3文件的情況"""
        # 模擬空的ZIP文件
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        mock_zip_instance.extractall = MagicMock()
        
        # 設置臨時目錄無文件
        with patch('os.listdir', return_value=[]):
            status, srt_file, report_file = generate_subtitle(
                self.test_zip_path,
                self.test_transcript_path,
                self.test_api_key,
                self.batch_size
            )
        
        self.assertTrue("未在ZIP文件中找到MP3音頻" in status)
        self.assertIsNone(srt_file)
        self.assertIsNone(report_file)

if __name__ == '__main__':
    unittest.main()