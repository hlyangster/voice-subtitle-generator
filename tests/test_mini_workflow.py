import sys
import os

# 獲取專案根目錄
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 將專案根目錄添加到 Python 路徑
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# tests/test_mini_workflow.py
import gradio as gr
from modules.text_preprocessing import text_preprocessing

def process_text(text, language):
    """模擬簡化的流程"""
    # 步驟1: 文本預處理
    processed_text = text_preprocessing(text, language)
    
    # 這裡只是模擬後續步驟
    result = f"處理結果（實際應用中將生成音頻和字幕）:\n\n{processed_text}"
    return processed_text, result

# 創建簡單的 Gradio 界面
with gr.Blocks(title="簡化工作流程測試") as demo:
    gr.Markdown("# 簡化版語音生成與字幕系統（測試）")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="輸入逐字稿", 
                placeholder="請在此貼上您的文本...",
                lines=5
            )
            
            language = gr.Dropdown(
                choices=["中文", "英文"], 
                label="選擇語言",
                value="中文"
            )
            
            process_btn = gr.Button("處理文本")
            
        with gr.Column():
            processed_text = gr.Textbox(
                label="預處理結果", 
                lines=5
            )
            
            result_output = gr.Textbox(
                label="最終結果", 
                lines=5
            )
    
    process_btn.click(
        fn=process_text,
        inputs=[text_input, language],
        outputs=[processed_text, result_output]
    )

if __name__ == "__main__":
    demo.launch()