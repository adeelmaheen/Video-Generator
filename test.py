import os
import streamlit as st
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
from moviepy.config import change_settings
from pydub import AudioSegment
import tempfile
import time
import json
import captacity
from dotenv import load_dotenv
import logging
from PyPDF2 import PdfReader
import warnings
warnings.filterwarnings("ignore")


# Configure ImageMagick path (adjust if different on your PC)
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

load_dotenv()
logging.getLogger("torch").setLevel(logging.ERROR)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_API_URL = "https://api.pexels.com/v1/search"

def generate_background_image_pexels(prompt, output_path):
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": prompt, "per_page": 1}
    response = requests.get(PEXELS_API_URL, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Pexels API error: {response.status_code} - {response.text}")
    data = response.json()
    if not data.get("photos"):
        raise Exception("No images found for the prompt.")
    image_url = data["photos"][0]["src"]["original"]
    img_response = requests.get(image_url)
    img_response.raise_for_status()
    image = Image.open(BytesIO(img_response.content))
    image.save(output_path)
    return output_path

def generate_narration(text, output_path):
    try:
        tts = gTTS(text)
        tts.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")

def cleanup_clip(clip):
    try:
        clip.close()
    except Exception:
        pass

def read_text_file(uploaded_file):
    try:
        return uploaded_file.read().decode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to read text file: {str(e)}")

def read_pdf_file(uploaded_file):
    try:
        pdf = PdfReader(uploaded_file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Failed to read PDF file: {str(e)}")

st.title("Shortrocity: AI-Generated Short Videos with Pexels Images")
st.write("Upload a script (.txt or .pdf), enter a prompt for background image, and generate a video with narration and captions.")

source_file = st.file_uploader("Upload your script (TXT or PDF)", type=["txt", "pdf"])
image_prompt = st.text_input("Background Image Prompt", value="A futuristic city at night")

st.header("Caption Settings")
with st.form("settings_form"):
    font = st.text_input("Font", value="Arial-Bold")
    font_size = st.slider("Font Size", 50, 200, 70)
    font_color = st.color_picker("Font Color", "#FFFFFF")
    stroke_width = st.slider("Stroke Width", 0, 10, 2)
    stroke_color = st.color_picker("Stroke Color", "#000000")
    submit_settings = st.form_submit_button("Save Settings")

if submit_settings or source_file:
    settings = {
        "font": font,
        "font_size": font_size,
        "font_color": font_color,
        "stroke_width": stroke_width,
        "stroke_color": stroke_color,
    }
else:
    settings = {}

if st.button("Generate Video", disabled=not source_file):
    try:
        with st.spinner("Processing..."):
            # Extract script text
            if source_file.type == "text/plain":
                source_text = read_text_file(source_file)
            elif source_file.type == "application/pdf":
                source_text = read_pdf_file(source_file)
            else:
                st.error("Unsupported file format.")
                st.stop()

            timestamp = str(int(time.time()))
            output_dir = f"shorts/{timestamp}"
            os.makedirs(output_dir, exist_ok=True)

            # Save script for reference
            script_path = os.path.join(output_dir, "script.txt")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(source_text)

            # Generate narration audio
            narration_path = os.path.join(output_dir, "narration.mp3")
            generate_narration(source_text, narration_path)

            # Generate background image
            background_path = os.path.join(output_dir, "background.png")
            generate_background_image_pexels(image_prompt, background_path)

            # Compose video with captions
            audio_clip = AudioFileClip(narration_path)
            image_clip = ImageClip(background_path, duration=audio_clip.duration).set_fps(24)  # Set fps here!
            video = image_clip.set_audio(audio_clip)

            styled_video = captacity.apply_captions_to_video(video, narration_path, settings)
            video_path = os.path.join(output_dir, "final_video.mp4")
            styled_video.write_videofile(video_path, codec="mpeg4", fps=24, verbose=False, logger=None)  # fps here too!

            # Cleanup
            cleanup_clip(styled_video)
            cleanup_clip(video)
            cleanup_clip(audio_clip)
            cleanup_clip(image_clip)

            st.success("Video generated successfully!")
            st.video(video_path)

            with open(background_path, "rb") as img_file:
                st.download_button("Download Background Image", img_file, "background.png")

            with open(narration_path, "rb") as audio_file:
                st.download_button("Download Narration Audio", audio_file, "narration.mp3")

            with open(video_path, "rb") as video_file:
                st.download_button("Download Video", video_file, "final_video.mp4")

    except Exception as e:
        st.error(f"Error: {str(e)}")

st.sidebar.header("Instructions")
st.sidebar.write("""
1. Upload a script file (.txt or .pdf).
2. Enter a background image prompt (e.g., 'mountains at sunset').
3. Adjust caption styles if needed.
4. Click 'Generate Video' to create a video with narration and captions.
5. Download the generated files.
""")
