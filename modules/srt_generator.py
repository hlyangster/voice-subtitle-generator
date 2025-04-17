# modules/srt_generator.py
import os
import re
import tempfile
from typing import List, Tuple, Optional, Dict
import openai
from pydub import AudioSegment

class SRTGenerator:
    """
    SRT字幕生成器，負責使用Whisper API將音頻文件轉換為SRT格式字幕
    """
    
    def __init__(self, temp_dir: str = "temp/subtitle"):
        """初始化SRT生成器
        
        Args:
            temp_dir: 臨時字幕檔案目錄
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def get_audio_duration(self, file_path: str) -> float:
        """使用pydub獲取音頻文件的長度（秒）
        
        Args:
            file_path: 音頻檔案路徑
            
        Returns:
            音頻時長（秒）
        """
        try:
            audio = AudioSegment.from_file(file_path)
            return audio.duration_seconds
        except Exception as e:
            print(f"獲取音頻長度失敗: {str(e)}")
            return 0.0
    
    def transcribe(self, file_path: str, api_key: str, language: str = "zh") -> str:
        """
        使用Whisper API轉錄單個音頻文件
        
        Args:
            file_path: 音頻檔案路徑
            api_key: OpenAI API金鑰
            language: 語言代碼 (zh/en/ja等)
            
        Returns:
            SRT格式的轉錄結果
        """
        # 設置API金鑰
        client = openai.OpenAI(api_key=api_key)
        
        try:
            with open(file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="srt",
                    language=language
                )
            
            # 返回SRT格式的內容
            return response
        
        except Exception as e:
            error_msg = f"轉錄失敗: {str(e)}"
            print(error_msg)
            return ""
    
    def correct_timestamps_proportionally(self, srt_content: str, audio_duration: float) -> str:
        """
        按比例校正SRT的時間戳
        
        Args:
            srt_content: SRT字幕內容
            audio_duration: 對應的音頻長度（秒）
            
        Returns:
            校正後的SRT內容
        """
        if not srt_content or not audio_duration:
            return srt_content
            
        parsed = self.parse_srt(srt_content)
        if not parsed:
            return srt_content
            
        # 獲取字幕的總時間
        last_entry = parsed[-1]
        subtitle_end_time = self.time_to_ms(last_entry['end_time'])
        
        # 計算校正因子 (音頻實際長度/字幕顯示的長度)
        correction_factor = (audio_duration * 1000) / subtitle_end_time
        
        # 應用校正
        for entry in parsed:
            start_ms = int(self.time_to_ms(entry['start_time']) * correction_factor)
            end_ms = int(self.time_to_ms(entry['end_time']) * correction_factor)
            
            entry['start_time'] = self.ms_to_time(start_ms)
            entry['end_time'] = self.ms_to_time(end_ms)
        
        # 更新SRT內容
        corrected_content = ""
        for entry in parsed:
            corrected_content += f"{entry['index']}\n"
            corrected_content += f"{entry['start_time']} --> {entry['end_time']}\n"
            corrected_content += f"{entry['text']}\n\n"
        
        return corrected_content
    
    def time_to_ms(self, time_str: str) -> int:
        """將SRT時間格式轉換為毫秒
        
        Args:
            time_str: SRT格式的時間 (00:00:00,000)
            
        Returns:
            毫秒數
        """
        hours, minutes, seconds = time_str.replace(',', '.').split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return int(total_seconds * 1000)
    
    def ms_to_time(self, ms: int) -> str:
        """將毫秒轉換為SRT時間格式
        
        Args:
            ms: 毫秒數
            
        Returns:
            SRT格式的時間字符串
        """
        seconds, ms = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(ms):03d}"
    
    def parse_srt(self, srt_content: str) -> List[Dict]:
        """
        解析SRT內容為結構化數據
        
        Args:
            srt_content: SRT字幕內容
            
        Returns:
            列表，每個元素包含序號、時間戳、文本
        """
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)'
        matches = re.findall(pattern, srt_content, re.MULTILINE)
        
        parsed = []
        for match in matches:
            index = int(match[0])
            start_time = match[1]
            end_time = match[2]
            text = match[3].strip()
            
            parsed.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
        
        return parsed
    
    def generate_srt_from_audio_files(self, audio_files: List[str], output_file: str, api_key: str, language: str = "zh") -> Tuple[bool, Optional[str]]:
        """從多個音頻文件生成合併的SRT
        
        Args:
            audio_files: 音頻文件路徑列表
            output_file: 輸出SRT文件路徑
            api_key: OpenAI API金鑰
            language: 語言代碼
            
        Returns:
            (成功狀態, SRT檔案路徑或錯誤訊息)
        """
        try:
            if not audio_files:
                return False, "未提供音頻文件"
            
            # 排序文件 (假設文件名格式為數字開頭，如 "01.mp3", "02.mp3")
            sorted_files = sorted(audio_files, key=lambda x: int(re.search(r'^\d+', os.path.basename(x)).group()) if re.search(r'^\d+', os.path.basename(x)) else float('inf'))
            
            # 為每個文件生成SRT
            temp_dir = tempfile.mkdtemp()
            srt_files = {}
            
            for i, file_path in enumerate(sorted_files):
                filename = os.path.basename(file_path)
                srt_path = os.path.join(temp_dir, f"{i+1}.srt")
                
                print(f"處理文件 {i+1}/{len(sorted_files)}: {filename}")
                
                # 獲取音頻時長
                audio_duration = self.get_audio_duration(file_path)
                
                # 使用Whisper API轉錄
                srt_content = self.transcribe(file_path, api_key, language)
                
                if srt_content:
                    # 校正時間戳
                    if audio_duration:
                        srt_content = self.correct_timestamps_proportionally(srt_content, audio_duration)
                    
                    # 保存SRT文件
                    with open(srt_path, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    
                    srt_files[filename] = {
                        'path': srt_path,
                        'content': srt_content,
                        'duration': audio_duration
                    }
                else:
                    print(f"無法轉錄: {filename}")
            
            if not srt_files:
                return False, "無法生成任何SRT文件"
            
            # 合併SRT文件
            merged_content = self._merge_srt(srt_files, language)
            
            # 保存合併後的SRT
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(merged_content)
            
            return True, output_file
        
        except Exception as e:
            return False, f"處理音頻文件失敗: {str(e)}"
    
    def _merge_srt(self, srt_files: Dict, language: str = "zh") -> str:
        """
        合併多個SRT文件
        
        Args:
            srt_files: SRT文件信息字典
            language: 語言代碼
            
        Returns:
            合併後的SRT內容
        """
        all_entries = []
        last_end_time = 0
        
        # 準備文件列表
        files_list = []
        for filename, data in srt_files.items():
            files_list.append((filename, data['path']))
        
        # 定義中文標點替換映射
        punctuation_map = {
            ',': '，',  # 逗號
            '.': '。',  # 句號
            ':': '：',  # 冒號
            '?': '？',  # 問號
            '!': '！',  # 感嘆號
        }
        
        # 按照文件名排序
        sorted_files = sorted(files_list, key=lambda x: os.path.basename(x[0]))
        
        for filename, file_path in sorted_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            parsed = self.parse_srt(srt_content)
            
            if not parsed:
                continue
            
            # 調整時間戳
            if all_entries:
                # 計算時間偏移量
                first_entry_start = self.time_to_ms(parsed[0]['start_time'])
                time_offset = last_end_time - first_entry_start
                
                # 應用偏移量
                for entry in parsed:
                    start_ms = self.time_to_ms(entry['start_time']) + time_offset
                    end_ms = self.time_to_ms(entry['end_time']) + time_offset
                    
                    entry['start_time'] = self.ms_to_time(start_ms)
                    entry['end_time'] = self.ms_to_time(end_ms)
            
            # 更新序號
            start_index = len(all_entries) + 1
            for i, entry in enumerate(parsed, start_index):
                entry['index'] = i
                
                # 如果是中文，將半形標點替換為全形標點
                if language == "zh":
                    text = entry['text']
                    for half_width, full_width in punctuation_map.items():
                        text = text.replace(half_width, full_width)
                    entry['text'] = text
            
            # 記錄最後一個條目的結束時間
            if parsed:
                last_end_time = self.time_to_ms(parsed[-1]['end_time'])
            
            all_entries.extend(parsed)
        
        # 將合併的條目轉換回SRT格式
        merged_content = ""
        for entry in all_entries:
            merged_content += f"{entry['index']}\n"
            merged_content += f"{entry['start_time']} --> {entry['end_time']}\n"
            merged_content += f"{entry['text']}\n\n"
        
        return merged_content