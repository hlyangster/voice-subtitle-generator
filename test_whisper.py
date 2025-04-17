import os
import tempfile
import gradio as gr
from openai import OpenAI
from datetime import timedelta
from pydub import AudioSegment


def format_time(seconds):
    """將秒數轉換為 SRT 時間格式 (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def create_srt(segments):
    """從語音識別區段創建 SRT 字幕格式"""
    srt_content = ""
    for i, segment in enumerate(segments, start=1):
        # 使用物件屬性方式存取
        start_time = format_time(segment.start)
        end_time = format_time(segment.end)
        text = segment.text.strip()

        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

    return srt_content


def audio_to_srt(audio_input, api_key):
    """處理上傳的音訊並回傳 SRT 檔案"""
    # 基本驗證
    if audio_input is None:
        return None, "請上傳音訊檔案"
    if not api_key or not api_key.strip():
        return None, "請輸入 OpenAI API 金鑰"

    try:
        # 建立 OpenAI 客戶端
        client = OpenAI(api_key=api_key)

        # 準備檔案
        temp_dir = tempfile.mkdtemp()
        temp_audio_path = os.path.join(temp_dir, "temp_audio.mp3")
        srt_output_path = os.path.join(temp_dir, "output.srt")

        # 轉換音訊格式
        audio = AudioSegment.from_file(audio_input)
        audio.export(temp_audio_path, format="mp3")

        # 直接方法：請求 OpenAI 返回 SRT 格式
        with open(temp_audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh",
                response_format="srt"  # 直接請求 SRT 格式
            )

        # 寫入 SRT 檔案
        with open(srt_output_path, "w", encoding="utf-8") as srt_file:
            srt_file.write(response)

        return srt_output_path, "字幕生成成功！"

    except Exception as e:
        return None, f"處理過程中發生錯誤: {str(e)}"


# 建立 Gradio 介面
with gr.Blocks(title="中文語音轉 SRT 字幕") as app:
    gr.Markdown("# 中文語音轉 SRT 字幕工具")
    gr.Markdown("### 上傳中文語音檔案，自動生成 SRT 字幕檔")

    with gr.Row():
        with gr.Column():
            api_key_input = gr.Textbox(
                label="OpenAI API 金鑰",
                placeholder="輸入您的 OpenAI API 金鑰",
                type="password"
            )

            audio_input = gr.Audio(
                label="上傳中文語音檔案",
                type="filepath"
            )

            convert_btn = gr.Button("轉換為 SRT 字幕", variant="primary")
            status_msg = gr.Textbox(
                label="處理狀態", placeholder="等待轉換...", interactive=False)

        with gr.Column():
            srt_output = gr.File(label="下載 SRT 字幕檔")

    convert_btn.click(
        fn=audio_to_srt,
        inputs=[audio_input, api_key_input],
        outputs=[srt_output, status_msg]
    )

    gr.Markdown("""
    ## 使用說明
    1. 輸入您的 OpenAI API 金鑰
    2. 上傳中文語音檔案（支援各種音訊格式）
    3. 點擊「轉換為 SRT 字幕」按鈕
    4. 等待處理完成後下載 SRT 檔案
    """)

# 啟動 Gradio 應用
if __name__ == "__main__":
    app.launch(share=True)
