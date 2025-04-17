# modules/audio_merge.py

import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def _check_ffmpeg(self):
    """檢查系統是否安裝了ffmpeg"""
    try:
        # 在 Hugging Face 環境中，優先檢查 /usr/bin/ffmpeg
        if os.path.exists("/usr/bin/ffmpeg"):
            subprocess.run(["/usr/bin/ffmpeg", "-version"], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True

        # 然後嘗試系統 PATH 中的 ffmpeg
        subprocess.run(["ffmpeg", "-version"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


class AudioMergeError(Exception):
    """音頻合併過程中的錯誤"""
    pass


class AudioMerger:
    """音頻合併和視頻創建處理器"""

    def __init__(self, output_dir=None):
        """
        初始化音頻合併器

        Args:
            output_dir (str, optional): 輸出目錄路徑. 默認為None，表示使用臨時目錄.
        """
        self.output_dir = output_dir if output_dir else tempfile.mkdtemp()

        # 確保輸出目錄存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _check_ffmpeg(self):
        """檢查系統是否安裝了ffmpeg"""
        try:
            subprocess.run(["ffmpeg", "-version"], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _normalize_path(self, path):
        """標準化路徑格式，處理特殊字符

        Args:
            path (str): 原始路徑

        Returns:
            str: 標準化後的路徑
        """
        # 轉換為絕對路徑
        abs_path = os.path.abspath(path)
        # 標準化路徑分隔符
        norm_path = os.path.normpath(abs_path).replace('\\', '/')
        return norm_path

    def _escape_path_for_ffmpeg(self, path):
        """為 FFmpeg 命令轉義路徑

        Args:
            path (str): 原始路徑

        Returns:
            str: 轉義後適合 FFmpeg 使用的路徑
        """
        # 將路徑轉換為 FFmpeg 兼容格式
        # 移除冒號前的驅動器標識，使用 file: 協議
        if ':' in path:
            path = 'file:' + path.replace(':', '\\:').replace('\\', '//')
        return path

    def merge_audio_files(self, audio_files, output_path):
        """
        合併多個音頻文件

        Args:
            audio_files (list): 音頻文件路徑列表
            output_path (str): 輸出文件路徑

        Returns:
            tuple: (成功標誌, 輸出路徑或錯誤消息)
        """
        if not audio_files:
            return False, "沒有提供音頻文件"

        # 確保所有文件存在
        for file_path in audio_files:
            if not os.path.exists(file_path):
                return False, f"找不到音頻文件: {file_path}"

        # 檢查ffmpeg是否可用
        if not self._check_ffmpeg():
            return False, "系統未安裝 ffmpeg，無法處理音頻"

        try:
            # 創建臨時目錄管理所有文件
            temp_dir = tempfile.mkdtemp()

            # 創建一個臨時文件列表
            file_list_path = os.path.join(temp_dir, "file_list.txt")
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    # 標準化路徑
                    norm_path = self._normalize_path(audio_file)
                    f.write(f"file '{norm_path}'\n")

            # 標準化輸出路徑
            norm_output = self._normalize_path(output_path)

            # 使用ffmpeg合併音頻
            cmd = [
                "ffmpeg",
                "-y",  # 覆寫現有文件
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                norm_output
            ]

            process = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 清理臨時目錄
            shutil.rmtree(temp_dir, ignore_errors=True)

            # 檢查輸出文件是否存在
            if not os.path.exists(output_path):
                return False, "音頻合併失敗，未生成輸出文件"

            return True, output_path

        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode(
                'utf-8', errors='replace') if e.stderr else str(e)
            return False, f"音頻合併過程出錯: {error_message}"
        except Exception as e:
            return False, f"音頻合併過程中發生未知錯誤: {str(e)}"

    def create_video_without_subtitles(self, audio_path, output_path, width=1280, height=720):
        """只創建帶有黑色背景和音頻的視頻，不包含字幕"""
        try:
            if not os.path.exists(audio_path):
                return False, f"找不到音頻文件: {audio_path}"

            # 檢查ffmpeg是否可用
            if not self._check_ffmpeg():
                return False, "系統未安裝 ffmpeg，無法處理視頻"

            # 標準化路徑
            norm_audio = self._normalize_path(audio_path)
            norm_output = self._normalize_path(output_path)

            cmd = [
                "ffmpeg",
                "-y",  # 覆寫現有文件
                "-f", "lavfi",
                "-i", f"color=c=black:s={width}x{height}:r=24",
                "-i", norm_audio,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-pix_fmt", "yuv420p",
                norm_output
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

            return True, output_path
        except Exception as e:
            return False, f"視頻生成錯誤: {str(e)}"

    def create_video_with_subtitles(self, audio_path, subtitle_path, output_path, width=1280, height=720):
        """
        創建帶字幕的視頻，採用多種備選方案確保成功率

        Args:
            audio_path (str): 音頻文件路徑
            subtitle_path (str): 字幕文件路徑
            output_path (str): 輸出視頻路徑
            width (int, optional): 視頻寬度. 默認為1280.
            height (int, optional): 視頻高度. 默認為720.

        Returns:
            tuple: (成功標誌, 輸出路徑或錯誤消息)
        """
        if not os.path.exists(audio_path):
            return False, f"找不到音頻文件: {audio_path}"

        if not os.path.exists(subtitle_path):
            return False, f"找不到字幕文件: {subtitle_path}"

        # 檢查ffmpeg是否可用
        if not self._check_ffmpeg():
            return False, "系統未安裝 ffmpeg，無法處理視頻"

        try:
            # 創建臨時工作目錄
            temp_dir = tempfile.mkdtemp()

            # 複製字幕文件到臨時位置，使用簡單文件名並處理編碼
            temp_subtitle = os.path.join(temp_dir, "simple.srt")

            # 嘗試使用不同編碼讀取字幕文件
            try:
                # 嘗試使用 UTF-8 讀取
                with open(subtitle_path, 'r', encoding='utf-8') as src:
                    content = src.read()
            except UnicodeDecodeError:
                # 如果 UTF-8 失敗，嘗試使用 BIG5 (繁體中文常用編碼)
                try:
                    with open(subtitle_path, 'r', encoding='big5') as src:
                        content = src.read()
                except UnicodeDecodeError:
                    # 最後嘗試 GBK (簡體中文常用編碼)
                    with open(subtitle_path, 'r', encoding='gbk') as src:
                        content = src.read()

            # 確保字幕內容格式正確
            if not content.strip():
                return False, "字幕文件為空"

            # 始終以 UTF-8 寫入臨時文件
            with open(temp_subtitle, 'w', encoding='utf-8') as dst:
                dst.write(content)

            # 標準化路徑
            norm_audio = self._normalize_path(audio_path)
            norm_subtitle = self._normalize_path(temp_subtitle)
            norm_output = self._normalize_path(output_path)

            # 打印調試信息
            print(f"音頻路徑: {norm_audio}")
            print(f"字幕路徑: {norm_subtitle}")
            print(f"輸出路徑: {norm_output}")

            # 方法1: 使用兩步驟方法
            # 步驟1: 創建不含字幕的黑色背景視頻
            temp_video = os.path.join(temp_dir, "temp_video.mp4")

            cmd1 = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:s={width}x{height}:r=24",
                "-i", norm_audio,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-pix_fmt", "yuv420p",
                temp_video
            ]

            subprocess.run(cmd1, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 標準化臨時視頻路徑
            norm_temp_video = self._normalize_path(temp_video)

            # 為 FFmpeg 特別處理字幕路徑
            ffmpeg_subtitle_path = f"'{norm_subtitle}'"

            try:
                # 方法2: 嘗試使用內置字幕渲染，但使用更安全的路徑格式和調整字體大小
                cmd2 = [
                    "ffmpeg",
                    "-y",
                    "-i", norm_temp_video,
                    "-vf", f"subtitles={ffmpeg_subtitle_path}:force_style='Fontname=Arial,FontSize=18,PrimaryColour=&Hffffff&,Alignment=2,MarginL=180,MarginR=180'",
                    "-c:a", "copy",
                    norm_output
                ]

                subprocess.run(cmd2, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                try:
                    # 方法3: 嘗試使用絕對路徑方式
                    subtitle_filename = os.path.basename(temp_subtitle)
                    # 複製字幕到當前工作目錄
                    current_dir_subtitle = os.path.join(
                        os.getcwd(), subtitle_filename)
                    shutil.copy2(temp_subtitle, current_dir_subtitle)

                    cmd3 = [
                        "ffmpeg",
                        "-y",
                        "-i", norm_temp_video,
                        "-vf", f"subtitles={subtitle_filename}:force_style='Fontname=Arial,FontSize=18,PrimaryColour=&Hffffff&,Alignment=2,MarginL=180,MarginR=180'",
                        "-c:a", "copy",
                        norm_output
                    ]

                    subprocess.run(
                        cmd3, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # 清理臨時文件
                    if os.path.exists(current_dir_subtitle):
                        os.remove(current_dir_subtitle)

                except subprocess.CalledProcessError:
                    try:
                        # 方法4: 使用 MOV 字幕容器
                        cmd4 = [
                            "ffmpeg",
                            "-y",
                            "-i", norm_temp_video,
                            "-f", "srt",
                            "-i", norm_subtitle,
                            "-c:v", "copy",
                            "-c:a", "copy",
                            "-c:s", "mov_text",
                            norm_output
                        ]
                        subprocess.run(
                            cmd4, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except subprocess.CalledProcessError:
                        # 方法5: 如果都失敗，只使用沒有字幕的視頻
                        shutil.copy2(temp_video, output_path)
                        print("警告: 無法添加字幕，使用無字幕視頻作為替代")

            # 清理臨時文件
            shutil.rmtree(temp_dir, ignore_errors=True)

            if not os.path.exists(output_path):
                return False, "視頻創建失敗，未生成輸出文件"

            return True, output_path

        except Exception as e:
            print(f"視頻創建錯誤: {str(e)}")
            return False, f"視頻創建過程中發生未知錯誤: {str(e)}"
