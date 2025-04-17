# tests/test_dictionary.py
import sys
from pathlib import Path

# 將專案根目錄加入到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from modules.homophone_replacement import HomophoneReplacer

# 測試字典載入
dictionary_path = project_root / "data" / "default_dictionary.json"
replacer = HomophoneReplacer(dictionary_path)

# 測試簡單替換
text = "銀行的行業規範很重要，重新制定後需要協調各行各業執行"
replaced_text, report = replacer.replace_homophones(text)
print(f"原始文本: {text}")
print(f"替換後文本: {replaced_text}")
print(replacer.get_replacement_report(report))