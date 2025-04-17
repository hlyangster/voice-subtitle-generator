# modules/subtitle_corrector.py
import google.generativeai as genai
import pysrt
import re
import os
import time
from typing import Dict, List, Tuple, Optional
from prompts.zh_prompt import SUBTITLE_CORRECTION_PROMPT

class SubtitleCorrector:
    def __init__(self, api_key: str):
        """初始化字幕校正器
        
        Args:
            api_key: Google Gemini API金鑰
        """
        self.api_key = api_key
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            raise ValueError(f"API 金鑰錯誤，請檢查設定: {e}")
    
    @staticmethod
    def parse_srt(srt_path: str) -> Optional[Dict]:
        """解析SRT檔案
        
        Args:
            srt_path: SRT檔案路徑
            
        Returns:
            字幕數據字典或None(如果解析失敗)
        """
        try:
            subs = pysrt.open(srt_path, encoding='utf-8')
            srt_data = {}
            for sub in subs:
                srt_data[sub.index] = {"time": str(sub.start) + " --> " + str(sub.end), "text": sub.text}
            return srt_data
        except Exception as e:
            print(f"解析字幕檔案錯誤: {e}")
            return None
    
    @staticmethod
    def preprocess_transcript(transcript: str) -> str:
        """預處理逐字稿
        
        Args:
            transcript: 原始逐字稿文本
            
        Returns:
            處理後的逐字稿文本
        """
        # 移除 SSML 標籤
        transcript = re.sub(r'<[^>]*?>', '', transcript)
        
        # 移除多個連續空格
        transcript = re.sub(r'\s+', ' ', transcript)
        
        # 簡單地將換行替換為空格
        transcript = transcript.replace('\n', ' ')
        
        # 移除文字前後的空白
        transcript = transcript.strip()
        return transcript
    
    @staticmethod
    def validate_srt(original_srt: Dict, modified_srt: Dict) -> Tuple[bool, str]:
        """驗證修改後的SRT是否保留了原始SRT的基本結構
        
        Args:
            original_srt: 原始SRT數據
            modified_srt: 修改後的SRT數據
            
        Returns:
            (是否有效, 錯誤信息)
        """
        # 檢查編號完整性
        if set(original_srt.keys()) != set(modified_srt.keys()):
            missing = set(original_srt.keys()) - set(modified_srt.keys())
            extra = set(modified_srt.keys()) - set(original_srt.keys())
            return False, f"編號不匹配: 缺少 {missing}, 多出 {extra}"
        
        # 檢查時間戳保持不變
        for idx in original_srt:
            if original_srt[idx]['time'] != modified_srt[idx]['time']:
                return False, f"編號 {idx} 的時間戳被修改"
        
        # 檢查文字長度變化不太大
        for idx in original_srt:
            orig_len = len(original_srt[idx]['text'])
            mod_len = len(modified_srt[idx]['text'])
            # 允許30%的文字長度變化
            if abs(orig_len - mod_len) / max(1, orig_len) > 0.3:
                return False, f"編號 {idx} 的文字長度變化過大: 原 {orig_len}, 現 {mod_len}"
        
        return True, "驗證通過"
    
    def correct_subtitles(self, transcript_file: str, srt_file: str, batch_size: int = 20) -> Tuple[Optional[str], Optional[pysrt.SubRipFile], Optional[List[str]]]:
        """進行字幕校正處理
        
        Args:
            transcript_file: 逐字稿文件路徑
            srt_file: SRT文件路徑
            batch_size: 批次大小
            
        Returns:
            (錯誤信息, 更新後的SRT對象, 修改報告列表)
        """
        # 檢查測試用逐字稿檔案是否存在
        if not os.path.exists(transcript_file):
            return f"錯誤: 找不到逐字稿檔案: {transcript_file}", None, None
        else:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            transcript_content = self.preprocess_transcript(transcript_content)

        # 檢查測試用 srt 檔案是否存在
        if not os.path.exists(srt_file):
            return f"錯誤: 找不到口語稿檔案: {srt_file}", None, None
        else:
            original_srt_data = self.parse_srt(srt_file)
            if original_srt_data is None:
                return "錯誤: 解析口語稿檔案失敗，請確認檔案內容", None, None
        
        # 創建工作副本
        srt_data = original_srt_data.copy()
        
        # 儲存所有報告
        all_reports = []
        keys = list(srt_data.keys()) # 取得編號

        # 使用固定數量的重疊
        overlap = 2  # 固定重疊2條字幕
        
        # 處理每個批次，使用固定重疊數量
        for i in range(0, len(keys), batch_size - overlap):
            end_idx = min(i + batch_size, len(keys))
            batch_keys = keys[i:end_idx]
            
            # 確保前一批次的最後部分有重疊
            context_start = max(0, i - overlap)
            context_keys = keys[context_start:i] if i > 0 else []
            
            # 準備本批次處理的數據
            batch_with_context = context_keys + batch_keys
            context_batch_data = {key: srt_data[key] for key in batch_with_context}
            
            # 在提示中標記哪些是實際需要處理的部分(非上下文)
            subtitle_lines = []
            for key in batch_with_context:
                prefix = "處理→ " if key in batch_keys else "上下文: "
                subtitle_lines.append(f"{prefix}編號{key}:{context_batch_data[key]['text']}")
            
            subtitle_content = "\n".join(subtitle_lines)
            
            # 使用來自prompts/zh_prompt.py的提示詞模板
            prompt = SUBTITLE_CORRECTION_PROMPT.format(
                subtitle_content=subtitle_content,
                transcript_content=transcript_content
            )
            
            try:
                # 添加重試機制與間隔時間
                max_retries = 3
                retry_count = 0
                retry_delay = 5  # 初始等待秒數
                
                while retry_count < max_retries:
                    try:
                        # 添加間隔時間以避免觸發限流
                        if i > 0:
                            print(f"等待 {retry_delay} 秒以避免達到API限制...")
                            time.sleep(retry_delay)
                        
                        response = self.model.generate_content(prompt)
                        corrected_subtitle = response.text
                        print(f"第 {i // (batch_size - overlap) + 1} 批次 Gemini 模型的回應：")
                        print(corrected_subtitle)
                        break  # 成功獲取回應，跳出重試循環
                        
                    except Exception as retry_error:
                        retry_count += 1
                        if "429" in str(retry_error):
                            print(f"遇到配額限制 (429)，重試 {retry_count}/{max_retries}...")
                            retry_delay *= 2  # 指數退避策略
                        else:
                            # 其他錯誤，直接拋出
                            raise retry_error
                        
                        if retry_count >= max_retries:
                            raise retry_error
                
                # 使用 re.split 分割字幕和報告
                parts = re.split(r'<<<分隔符號>>>', corrected_subtitle, maxsplit=1) # 只分割一次
                
                # 改進的字幕解析方法
                corrected_lines = parts[0].strip().split('\n')
                
                # 建立一個映射表來追踪已處理的編號
                processed_indices = set()
                
                for line in corrected_lines:
                    # 確保只處理「處理→」標記的編號字幕行
                    match = re.match(r'(?:處理→ )?編號(\d+):(.*)', line)
                    if match:
                        index = int(match.group(1))
                        corrected_text = match.group(2).strip()
                        
                        # 確保此編號在當前批次中且需要處理
                        if index in batch_keys:
                            srt_data[index]['text'] = corrected_text
                            processed_indices.add(index)
                
                # 檢查是否所有批次中的編號都被處理了
                for index in batch_keys:
                    if index not in processed_indices:
                        print(f"警告：編號 {index} 在AI處理後丟失，保持原始字幕內容")
                
                # 處理報告部分
                if len(parts) > 1:
                    report = parts[1] # 取得修改清單文字
                    report_lines = report.strip().split('\n')
                    all_reports.extend(report_lines)

            except Exception as e:
                return f"第 {i // (batch_size - overlap) + 1} 批次修正過程失敗：{e}", None, None
        
        # 驗證修改後的SRT結構
        is_valid, error_msg = self.validate_srt(original_srt_data, srt_data)
        if not is_valid:
            return f"SRT結構驗證失敗: {error_msg}", None, None
        
        # 寫回 SRT 檔案
        new_subs = []
        for index, data in sorted(srt_data.items()):  # 確保按編號順序排序
            time_str = data['time']
            start_str, end_str = time_str.split(" --> ")
            start = pysrt.srtitem.SubRipTime.from_string(start_str)
            end = pysrt.srtitem.SubRipTime.from_string(end_str)
            new_subs.append(pysrt.SubRipItem(index=index, start=start, end=end, text=data['text']))
        
        # 將 new_subs 轉換為 SubRipFile 物件
        new_srt = pysrt.SubRipFile(items=new_subs)
        
        return None, new_srt, all_reports