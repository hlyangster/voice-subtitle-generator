# test_gradio.py
import gradio as gr

def echo(message):
    return message

demo = gr.Interface(
    fn=echo,
    inputs=gr.Textbox(placeholder="輸入任何文本..."),
    outputs="text",
    title="環境測試 - Echo 應用"
)

if __name__ == "__main__":
    demo.launch()