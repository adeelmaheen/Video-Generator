import os
import streamlit as st
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from pydub import AudioSegment
import tempfile
import time
import json
import cv2
import numpy as np
from dotenv import load_dotenv
import logging
from PyPDF2 import PdfReader
import warnings
import subprocess  # For ffmpeg operations
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()
logging.getLogger("torch").setLevel(logging.ERROR)

# Configuration
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_API_URL = "https://api.pexels.com/v1/search"
FPS = 24
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

def generate_background_image_pexels(prompt, output_path):
    """Fetch image from Pexels API"""
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
    """Generate audio narration using gTTS"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")

def create_video_from_image(image_path, audio_path, output_path):
    """Create video from static image and audio using ffmpeg"""
    try:
        # Get audio duration
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000  # Convert ms to seconds
        
        # Create video using ffmpeg
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite without asking
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure even dimensions
            '-shortest',
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except Exception as e:
        raise Exception(f"Video creation failed: {str(e)}")

def add_captions_to_video(video_path, audio_path, output_path, settings):
    """Add captions to video (simplified version)"""
    # This is a placeholder - implement your captioning logic here
    # For now, we'll just copy the video as-is
    import shutil
    shutil.copyfile(video_path, output_path)
    return output_path

def read_text_file(uploaded_file):
    """Read text from uploaded file"""
    try:
        return uploaded_file.read().decode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to read text file: {str(e)}")

def read_pdf_file(uploaded_file):
    """Read text from PDF file"""
    try:
        pdf = PdfReader(uploaded_file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Failed to read PDF file: {str(e)}")

def cleanup_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

# Streamlit UI
st.title("Shortrocity: AI-Generated Short Videos with Pexels Images")
st.write("Upload a script (.txt or .pdf), enter a prompt for background image, and generate a video with narration.")

# File upload and settings
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
            # Create unique output directory
            timestamp = str(int(time.time()))
            output_dir = os.path.join("output", timestamp)
            os.makedirs(output_dir, exist_ok=True)

            # Process source file
            if source_file.type == "text/plain":
                source_text = read_text_file(source_file)
            elif source_file.type == "application/pdf":
                source_text = read_pdf_file(source_file)
            else:
                st.error("Unsupported file format.")
                st.stop()

            # Save script
            script_path = os.path.join(output_dir, "script.txt")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(source_text)

            # Generate narration
            narration_path = os.path.join(output_dir, "narration.mp3")
            generate_narration(source_text, narration_path)

            # Generate background image
            background_path = os.path.join(output_dir, "background.jpg")
            generate_background_image_pexels(image_prompt, background_path)

            # Create video
            raw_video_path = os.path.join(output_dir, "raw_video.mp4")
            create_video_from_image(background_path, narration_path, raw_video_path)

            # Add captions
            final_video_path = os.path.join(output_dir, "final_video.mp4")
            add_captions_to_video(raw_video_path, narration_path, final_video_path, settings)

            # Display results
            st.success("Video generated successfully!")
            st.video(final_video_path)

            # Download buttons
            with open(background_path, "rb") as img_file:
                st.download_button("Download Background Image", img_file, "background.jpg")

            with open(narration_path, "rb") as audio_file:
                st.download_button("Download Narration Audio", audio_file, "narration.mp3")

            with open(final_video_path, "rb") as video_file:
                st.download_button("Download Video", video_file, "final_video.mp4")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.stop()

# Instructions sidebar
st.sidebar.header("Instructions")
st.sidebar.write("""
1. Upload a script file (.txt or .pdf)
2. Enter a background image prompt
3. Adjust caption styles if needed
4. Click 'Generate Video'
5. Download the generated files
""")

# Cleanup temporary files on app restart
cleanup_files(os.path.join(TEMP_DIR, "*"))