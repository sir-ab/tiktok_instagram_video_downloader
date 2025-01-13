# tiktok_downloader/ui.py
import gradio as gr
import asyncio

from tiktok_downloader import process_tiktok_urls_with_progress, cancel_process as tiktok_cancel, resume_process as tiktok_resume
from instagram_downloader import process_instagram_urls_with_progress, cancel_process_ig as ig_cancel, resume_process_ig as ig_resume
from config import Config



def cancel_process():
  tiktok_cancel()
  ig_cancel()
  
def resume_process():
  tiktok_resume()
  ig_resume()

# Gradio interface
with gr.Blocks() as app:
    gr.Markdown("# Social Media Downloader")
    with gr.Tabs():
        with gr.TabItem("TikTok Downloader"):
            gr.Markdown(
                "Input TikTok embed URLs directly or upload a file containing the URLs. The progress will be displayed below."
            )
            with gr.Row():
                tiktok_url_input = gr.Textbox(
                    label="TikTok Embed URLs",
                    placeholder="Enter one URL per line",
                    lines=10
                )
                tiktok_file_input = gr.File(label="Upload File (containing TikTok embed URLs)")

            with gr.Row():
                tiktok_progress_output = gr.Textbox(label="Progress", interactive=False)

            with gr.Row():
                tiktok_log_output = gr.Textbox(label="Logs", interactive=False, lines=10)

            with gr.Row():
                tiktok_downloaded_videos_gallery = gr.Gallery(label="Recently Downloaded Videos", show_label=False, elem_id="gallery", columns=[10])

            with gr.Row():
                submit_tiktok_button = gr.Button("Start Download")
                resume_tiktok_button = gr.Button("Resume Download") # ADDED RESUME BUTTON


            submit_tiktok_button.click(
                fn=process_tiktok_urls_with_progress,
                inputs=[tiktok_url_input, tiktok_file_input],
                outputs=[tiktok_progress_output, tiktok_log_output, tiktok_downloaded_videos_gallery]
            )


            resume_tiktok_button.click(
                 fn=resume_process,
                 queue=False # queue=False important for multiple functions
             ).then(
                 fn=process_tiktok_urls_with_progress,
                 inputs=[tiktok_url_input, tiktok_file_input],
                 outputs=[tiktok_progress_output, tiktok_log_output, tiktok_downloaded_videos_gallery]
             )



        with gr.TabItem("Instagram Downloader"):
            gr.Markdown("Input Instagram post URLs directly or upload a file containing the URLs.")
            with gr.Row():
                instagram_url_input = gr.Textbox(
                    label="Instagram Post URLs",
                    placeholder="Enter one URL per line",
                    lines=10
                )
                instagram_file_input = gr.File(label="Upload File (containing Instagram post URLs)")

            with gr.Row():
                instagram_progress_output = gr.Textbox(label="Progress", interactive=False)

            with gr.Row():
                instagram_log_output = gr.Textbox(label="Logs", interactive=False, lines=10)

            with gr.Row():
              instagram_downloaded_videos_gallery = gr.Gallery(label="Recently Downloaded Videos", show_label=False, elem_id="gallery", columns=[10])

            submit_instagram_button = gr.Button("Start Download")
            resume_ig_button = gr.Button("Resume Download")

            submit_instagram_button.click(
                fn=process_instagram_urls_with_progress,
                inputs=[instagram_url_input, instagram_file_input],
                outputs=[instagram_progress_output, instagram_log_output, instagram_downloaded_videos_gallery]
            )


            resume_ig_button.click(
                 fn=resume_process,
                 queue=False # queue=False important for multiple functions
             ).then(
                 fn=process_instagram_urls_with_progress,
                 inputs=[tiktok_url_input, tiktok_file_input],
                 outputs=[tiktok_progress_output, tiktok_log_output, tiktok_downloaded_videos_gallery]
             )
    cancel_button = gr.Button("Cancel All")
    cancel_button.click(fn=cancel_process)

if __name__ == "__main__":
    app.launch(allowed_paths=[Config.OUTPUT_DIR_Tiktok, Config.OUTPUT_DIR_Instagram], debug=True, inline=False)