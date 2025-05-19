import os
import streamlit as st
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from pydub import AudioSegment
import tempfile
import time
import subprocess
from PyPDF2 import PdfReader
import warnings
from dotenv import load_dotenv
warnings.filterwarnings("ignore")

# Configuration
load_dotenv()
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_API_URL = "https://api.pexels.com/v1/search"
FPS = 24

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

def get_audio_duration(audio_path):
    """Get duration of audio file using ffprobe"""
    cmd = [
        'ffprobe',
        '-i', audio_path,
        '-show_entries', 'format=duration',
        '-v', 'quiet',
        '-of', 'csv=p=0'
    ]
    try:
        duration = float(subprocess.check_output(cmd).decode('utf-8').strip())
        return duration
    except Exception as e:
        raise Exception(f"Failed to get audio duration: {str(e)}")

def create_video_with_ffmpeg(image_path, audio_path, output_path):
    """Create video using ffmpeg"""
    try:
        duration = get_audio_duration(audio_path)
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite without asking
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-shortest',
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg failed with code {e.returncode}: {e.stderr.decode()}")
    except Exception as e:
        raise Exception(f"Video creation failed: {str(e)}")

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
st.title("Shortrocity: AI-Generated Short Videos")
st.write("Upload a script (.txt or .pdf), enter a prompt for background image, and generate a video with narration.")

# File upload and settings
source_file = st.file_uploader("Upload your script (TXT or PDF)", type=["txt", "pdf"])
image_prompt = st.text_input("Background Image Prompt", value="A futuristic city at night")

if st.button("Generate Video", disabled=not source_file):
    try:
        with st.spinner("Processing..."):
            # Create temp directory
            timestamp = str(int(time.time()))
            temp_dir = tempfile.mkdtemp()
            
            # Process source file
            if source_file.type == "text/plain":
                source_text = read_text_file(source_file)
            elif source_file.type == "application/pdf":
                source_text = read_pdf_file(source_file)
            else:
                st.error("Unsupported file format.")
                st.stop()

            # Generate narration
            narration_path = os.path.join(temp_dir, "narration.mp3")
            generate_narration(source_text, narration_path)

            # Generate background image
            background_path = os.path.join(temp_dir, "background.jpg")
            generate_background_image_pexels(image_prompt, background_path)

            # Create video
            video_path = os.path.join(temp_dir, "output.mp4")
            create_video_with_ffmpeg(background_path, narration_path, video_path)

            # Display results
            st.success("Video generated successfully!")
            st.video(video_path)

            # Download buttons
            with open(video_path, "rb") as video_file:
                st.download_button(
                    label="Download Video",
                    data=video_file,
                    file_name="generated_video.mp4",
                    mime="video/mp4"
                )

    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        # Cleanup temporary files
        cleanup_files(narration_path, background_path, video_path)

# Instructions sidebar
st.sidebar.header("Instructions")
st.sidebar.write("""
1. Upload a script file (.txt or .pdf)
2. Enter a background image prompt
3. Click 'Generate Video'
4. Download your video
""")