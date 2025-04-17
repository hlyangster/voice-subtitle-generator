# tests/test_segmentation.py
import sys
import os
from pathlib import Path

# 將專案根目錄加入到 Python 路徑
current_dir = Path(__file__).parent  # tests 目錄
project_root = current_dir.parent    # 專案根目錄
sys.path.append(str(project_root))

from modules.homophone_replacement import HomophoneReplacer

# 測試文本
test_text = """這是第一段文本。這段文本約有三十個字左右。

這是第二段文本。這也是一段測試文本，大約也有三十個字。

這是第三段。很短。

這是第四段文本，用於測試分段邏輯是否正確工作，確保每批次能包含正確數量的段落。

這是第五段文本，繼續測試。

這是第六段文本，繼續測試。

這是第七段文本，繼續測試。

這是第八段文本，繼續測試。

這是第九段文本，繼續測試。

這是第十段文本，繼續測試。

這是第十一段文本，這應該屬於第二批次。
"""

replacer = HomophoneReplacer()
batches = replacer.segment_text(test_text, batch_size=10)

print(f"總共分成 {len(batches)} 批次")
for i, batch in enumerate(batches):
    print(f"\n--- 批次 {i+1} ---")
    print(batch)
    print(f"字數：{len(batch)}")