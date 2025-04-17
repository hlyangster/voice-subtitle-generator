# modules/homophone_replacement.py

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import google.generativeai as genai

class HomophoneReplacer:
    """
    多音字替換模組，用於處理中文多音字，確保TTS語音合成的準確性
    """
    
    def __init__(self, dictionary_file=None):
        """
        初始化多音字替換器
        
        Args:
            dictionary_file (str, optional): 字典檔案路徑，如果未提供則使用預設詞庫
        """
        # 預設字典
        self.dictionary = []
        
        # 如果提供了字典檔案，則載入
        if dictionary_file and os.path.exists(dictionary_file):
            self.load_dictionary(dictionary_file)
        else:
            # 載入內置字典
            self.load_built_in_dictionary()
    
    def load_dictionary(self, dictionary_file: str) -> None:
        """
        從檔案讀取字典
        
        Args:
            dictionary_file (str): 字典檔案路徑
        """
        try:
            with open(dictionary_file, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)
            print(f"Successfully loaded dictionary from {dictionary_file}")
        except FileNotFoundError:
            print(f"Dictionary file not found at {dictionary_file}")
            raise FileNotFoundError(f"Dictionary file not found at {dictionary_file}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format in dictionary file: {e}")
            raise json.JSONDecodeError(f"Invalid JSON format in dictionary file", "", 0)
        except Exception as e:
            print(f"Error loading dictionary: {e}")
            raise
    
    def load_built_in_dictionary(self) -> None:
        """載入內置字典"""
        # 由於字典較長，這裡僅展示一部分
        self.dictionary = [
            {
                "no": 1,
                "original": "行",
                "modified": "航",
                "usecase": [
                    "行業", "行列", "銀行", "貨行", "行規", "行商", "各行各業", "行列", "行規", "一行", "兩行", "三行", "每行"
                ]
            },
            {
                "no": 2,
                "original": "會",
                "modified": "塊",
                "usecase": [
                    "會計", "會計師"
                ]
            }
            # 在實際代碼中應包含完整的字典
        ]
        print("Loaded built-in dictionary")
        
    def segment_text(self, text: str, batch_size: int = 10) -> List[str]:
        """
        將文本分成批次，每批次包含指定數量的段落
        
        Args:
            text (str): 預處理後的文本，每段以兩個換行符分隔
            batch_size (int): 每批次的段落數量
            
        Returns:
            List[str]: 分段後的批次列表
        """
        # 分割文本段落（以兩個換行符為分隔）
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 過濾空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 分批
        batches = []
        for i in range(0, len(paragraphs), batch_size):
            batch = paragraphs[i:i+batch_size]
            batches.append("\n\n".join(batch))
            
        return batches
    
    def process_with_google_ai(self, text_batches: List[str], api_key: str) -> str:
        """
        使用Google AI處理文本批次，進行斷詞
        
        Args:
            text_batches (List[str]): 文本批次列表
            api_key (str): Google AI API金鑰
            
        Returns:
            str: 合併後的處理結果
        """
        from prompts.zh_prompt import TEXT_SEGMENTATION_PROMPT
        
        # 配置Google AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        all_results = []
        
        for batch in text_batches:
            # 準備提示詞
            prompt = TEXT_SEGMENTATION_PROMPT.format(article=batch)
            
            # 呼叫API
            response = model.generate_content(prompt)
            
            # 添加結果
            all_results.append(response.text)
        
        # 合併所有結果
        return "\n\n".join(all_results)
    
    def replace_homophones(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        替換文本中的多音字
        
        Args:
            text (str): 輸入文本
            
        Returns:
            tuple: (替換後的文本, 替換報告)
        """
        if not text or not self.dictionary:
            return text, []
        
        modified_text = text
        report = []
        
        for item in self.dictionary:
            if 'usecase' in item and 'original' in item and 'modified' in item:
                original = item['original']
                modified = item['modified']
                for usecase_word in item['usecase']:
                    # 計算替換前出現次數
                    count_before = modified_text.count(usecase_word)
                    if count_before > 0:
                        # 進行替換
                        modified_text = modified_text.replace(
                            usecase_word, 
                            usecase_word.replace(original, modified)
                        )
                        
                        # 將替換資訊添加到報告中
                        report.append({
                            "original": original,
                            "modified": modified,
                            "word": usecase_word,
                            "instances": count_before
                        })
        
        # 移除斷詞符號
        final_text = modified_text.replace('^', '')
        
        return final_text, report
    
    def get_replacement_report(self, report: List[Dict[str, Any]]) -> str:
        """
        生成人類可讀的替換報告
        
        Args:
            report (List[Dict]): 替換報告列表
            
        Returns:
            str: 格式化的報告（Markdown格式）
        """
        if not report:
            return "未進行任何多音字替換"
        
        # 按原字分組
        grouped_by_original = {}
        total_replacements = 0
        
        for item in report:
            original = item['original']
            if original not in grouped_by_original:
                grouped_by_original[original] = []
            grouped_by_original[original].append(item)
            total_replacements += item['instances']
        
        # 格式化報告
        report_lines = [f"## 多音字替換報告（共替換 {total_replacements} 處）", ""]
        
        for original, items in grouped_by_original.items():
            modified = items[0]['modified']  # 替換成的字應該是一致的
            group_total = sum(item['instances'] for item in items)
            words = [f"{item['word']} ({item['instances']}次)" for item in items]
            
            report_lines.append(f"### 將「{original}」替換為「{modified}」（共 {group_total} 處）")
            report_lines.append(f"替換詞：{', '.join(words)}")
            report_lines.append("")
        
        return "\n".join(report_lines)