# test_project_structure.py
import os

def check_directory(path):
    if os.path.exists(path):
        print(f"✓ 資料夾存在: {path}")
        return True
    else:
        print(f"❌ 資料夾不存在: {path}")
        return False

# 測試專案結構
project_dirs = [
    "modules",
    "utils",
    "tests",
    "static",
    "templates"
]

for dir_name in project_dirs:
    check_directory(dir_name)

# 檢查基本文件
required_files = [
    "app.py",
    "requirements.txt",
    ".gitignore"
]

for file_name in required_files:
    if os.path.isfile(file_name):
        print(f"✓ 文件存在: {file_name}")
    else:
        print(f"❌ 文件不存在: {file_name}")