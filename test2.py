import os
import streamlit as st
import google.generativeai as gena
from google.cloud import aiplatform
# from google.cloud.aiplatform.generative_models import GenerativeModel  
from io import BytesIO
from PIL import Image
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
from moviepy.config import change_settings
import tempfile
import time
import captacity
from pydub import AudioSegment
from PyPDF2 import PdfReader
import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("torch").setLevel(logging.ERROR)

# Configure ImageMagick (adjust path if needed)
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# Initialize AI Platform with project and region
PROJECT_ID = "932729024321-1bqqr5t4ipslo74attbvf93kivncpgmp.apps.googleusercontent.com"  # Replace with your GCP project ID
REGION = "us-central1"          # Replace with your desired region
aiplatform.init(project=PROJECT_ID, location=REGION)

SERVICE_ACCOUNT_FILE = r"C:\Users\lenovo\Downloads\service-account.json"  # Use raw string or escape backslashes

def generate_image_gemini(prompt, output_path):
    """
    Generates an image using the Gemini image generation model.

    Args:
        prompt (str): Text prompt to generate the image.
        output_path (str): Path to save the generated image.

    Returns:
        str or None: Path of saved image or None if error.
    """
    model =genai. GenerativeModel('gemini-1.5-pro-001')  # Or whichever model you are using
    try:
        response = model.generate_images(prompt=prompt, number_of_images=1)
        image = Image.open(BytesIO(response.images[0]))
        image.save(output_path)
        return output_path
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None



def generate_narration(text: str, output_path: str) -> str:
    """
    Generate narration audio from text using Google Text-to-Speech (gTTS).

    Args:
        text (str): Text to convert to speech.
        output_path (str): File path to save the generated audio.

    Returns:
        str: Path where the audio is saved.
    """
    tts = gTTS(text)
    tts.save(output_path)
    return output_path


def read_pdf(uploaded_file) -> str:
    """
    Extract text content from an uploaded PDF file.

    Args:
        uploaded_file: File-like object representing the PDF.

    Returns:
        str: Extracted text from the PDF.
    """
    pdf = PdfReader(uploaded_file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text


def cleanup_clip(clip):
    """
    Safely close a MoviePy clip object to release resources.

    Args:
        clip: MoviePy clip object.
    """
    try:
        clip.close()
    except Exception as e:
        print(f"Error cleaning up clip: {e}")


# Streamlit app starts here
st.title("Gemini-Powered AI Video Generator")

# File uploader for script input (.txt or .pdf)
source_file = st.file_uploader("Upload Script (.txt or .pdf)", type=["txt", "pdf"])

# Image prompt input for background generation
image_prompt = st.text_input("Background Image Prompt", "A futuristic city at night")

st.header("Caption Settings")
with st.form("settings_form"):
    font = st.text_input("Font", value="Arial-Bold")
    font_size = st.slider("Font Size", 50, 200, 70)
    font_color = st.color_picker("Font Color", "#FFFFFF")
    stroke_width = st.slider("Stroke Width", 0, 10, 2)
    stroke_color = st.color_picker("Stroke Color", "#000000")
    submit_settings = st.form_submit_button("Save Settings")

settings = {}
if submit_settings or source_file:
    settings = {
        "font": font,
        "font_size": font_size,
        "font_color": font_color,
        "stroke_width": stroke_width,
        "stroke_color": stroke_color,
    }

source_text = ""  # To hold the script text globally


def generate_video():
    """
    Generate a video by creating narration and background, then applying captions.

    Returns:
        tuple: Paths to (video_path, background_image_path, narration_audio_path)
    """
    global source_text

    if source_file is None:
        st.error("Please upload a file first.")
        return None, None, None

    # Read the text from the uploaded file
    if source_file.type == "application/pdf":
        source_text = read_pdf(source_file)
    else:
        source_text = source_file.read().decode("utf-8")

    timestamp = str(int(time.time()))
    output_dir = os.path.join("shorts", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Generate narration audio
    narration_path = os.path.join(output_dir, "narration.mp3")
    generate_narration(source_text, narration_path)

    # Generate background image
    background_path = os.path.join(output_dir, "background.png")
    generate_image_gemini(image_prompt, background_path)

    # Load clips
    audio_clip = AudioFileClip(narration_path)
    image_clip = ImageClip(background_path, duration=audio_clip.duration).set_fps(24)

    # Combine audio and image to make a video clip
    video = image_clip.set_audio(audio_clip)

    # Apply captions with given settings
    styled_video = captacity.apply_captions_to_video(video, narration_path, settings)

    # Export final video
    video_path = os.path.join(output_dir, "final_video.mp4")
    styled_video.write_videofile(
        video_path,
        codec="mpeg4",
        fps=24,
        verbose=False,
        logger=None,
    )

    # Cleanup resources
    cleanup_clip(styled_video)
    cleanup_clip(video)
    cleanup_clip(audio_clip)
    cleanup_clip(image_clip)

    return video_path, background_path, narration_path


if st.button("Generate Video", disabled=not source_file):
    try:
        with st.spinner("Generating video..."):
            video_path, background_path, narration_path = generate_video()
            if video_path:
                st.success("Video generated successfully!")
                st.video(video_path)

                # Download buttons
                with open(background_path, "rb") as img_file:
                    st.download_button("Download Background Image", img_file, "background.png")

                with open(narration_path, "rb") as audio_file:
                    st.download_button("Download Narration Audio", audio_file, "narration.mp3")

                with open(video_path, "rb") as video_file:
                    st.download_button("Download Video", video_file, "final_video.mp4")
            else:
                st.error("Video generation failed.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
