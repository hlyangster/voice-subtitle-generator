#!/usr/bin/env python
# run_tests.py
"""
運行所有測試或指定測試的腳本

使用方式:
- 運行所有測試: python run_tests.py
- 運行指定測試模塊: python run_tests.py test_tts_generator
"""

import unittest
import sys
import os
from pathlib import Path

# 確保可以導入test模塊
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# 測試目錄
test_dir = script_dir / "tests"

def run_all_tests():
    """運行tests目錄下的所有測試"""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(test_dir)
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)

def run_specific_test(test_name):
    """運行指定的測試模塊"""
    test_module = f"tests.{test_name}"
    try:
        test_suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
        test_runner = unittest.TextTestRunner(verbosity=2)
        test_runner.run(test_suite)
    except ImportError:
        print(f"無法導入測試模塊: {test_module}")
        print(f"請確保 {test_name}.py 存在於 tests 目錄中")

def run_api_test():
    """運行API測試腳本"""
    from scripts.test_hailuo_api import test_hailuo_api
    test_hailuo_api()

if __name__ == "__main__":
    # 檢查是否指定了特定測試
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "api":
            # 特殊情況: 運行API測試
            print("運行Hailuo API測試...")
            run_api_test()
        else:
            # 運行指定的單元測試
            print(f"運行測試: {test_name}")
            run_specific_test(test_name)
    else:
        # 運行所有測試
        print("運行所有測試...")
        run_all_tests()