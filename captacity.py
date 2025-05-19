# import whisper
# import os
# from moviepy.editor import TextClip, CompositeVideoClip
# from moviepy.video.tools.drawing import color_gradient

# # Load the Whisper model
# def load_whisper_model():
#     model = whisper.load_model("base")
#     return model

# # Function to generate captions using Whisper
# def generate_captions(audio_file):
#     model = load_whisper_model()
#     result = model.transcribe(audio_file, word_timestamps=True)
    
#     captions = [
#         {
#             "text": segment["text"],
#             "start": segment["start"],
#             "end": segment["end"]
#         }
#         for segment in result["segments"]
#     ]
#     return captions

# # Function to apply styling to captions
# def apply_styling(captions, settings):
#     # Default settings in case no settings are provided
#     default_settings = {
#         "font": "Arial-Bold",
#         "font_size": 70,
#         "font_color": "white",
#         "stroke_width": 2,
#         "stroke_color": "black",
#         "highlight_current_word": False,
#         "word_highlight_color": "red",
#         "line_count": 2,
#         "padding": 50,
#         "shadow_strength": 1.0,
#         "shadow_blur": 0.1
#     }

#     # Update the settings with user-provided settings
#     settings = {**default_settings, **settings}

#     # Prepare caption clips
#     caption_clips = []
    
#     for caption in captions:
#         text = caption["text"]
#         start = caption["start"]
#         end = caption["end"]

#         # Generate text clip for the caption
#         txt_clip = TextClip(
#             text,
#             fontsize=settings["font_size"],
#             font=settings["font"],
#             color=settings["font_color"],
#             stroke_width=settings["stroke_width"],
#             stroke_color=settings["stroke_color"],
#             size=(1920, 1080),
#             align="center",
#             method="caption"
#         )
        
#         # Add shadow effect if required
#         if settings["shadow_strength"] > 0:
#             txt_clip = txt_clip.set_opacity(0.7).set_position(("center", "center"))
        
#         # Apply padding
#         txt_clip = txt_clip.margin(left=settings["padding"], right=settings["padding"], top=settings["padding"], bottom=settings["padding"])

#         # Positioning based on line count
#         if settings["line_count"] == 1:
#             txt_clip = txt_clip.set_position(("center", 0.8), relative=True)
#         elif settings["line_count"] == 2:
#             txt_clip = txt_clip.set_position(("center", 0.7), relative=True)
        
#         # Set the start and end times for the caption
#         txt_clip = txt_clip.set_start(start).set_end(end)

#         # Append the styled caption to the list of caption clips
#         caption_clips.append(txt_clip)

#     return caption_clips

# # Function to combine captions with video and apply them
# def apply_captions_to_video(video_clip, audio_file, settings):
#     captions = generate_captions(audio_file)
#     caption_clips = apply_styling(captions, settings)

#     # Composite the caption clips with the video
#     video_with_captions = CompositeVideoClip([video_clip] + caption_clips)
#     return video_with_captions


import whisper
from moviepy.editor import TextClip, CompositeVideoClip

# Load Whisper model
def load_whisper_model():
    model = whisper.load_model("base")
    return model

# Generate captions from audio using Whisper
def generate_captions(audio_file):
    model = load_whisper_model()
    result = model.transcribe(audio_file, word_timestamps=True)
    
    captions = [
        {
            "text": segment["text"],
            "start": segment["start"],
            "end": segment["end"]
        }
        for segment in result["segments"]
    ]
    return captions

# Apply styling to captions (font, color, etc.)
def apply_styling(captions, settings):
    # Default settings
    default_settings = {
        "font": "Arial-Bold",
        "font_size": 70,
        "font_color": "white",
        "stroke_width": 2,
        "stroke_color": "black",
        "line_count": 2,
        "padding": 50,
    }

    settings = {**default_settings, **settings}
    caption_clips = []

    for caption in captions:
        text = caption["text"]
        start = caption["start"]
        end = caption["end"]

        # Create TextClip for caption
        txt_clip = TextClip(
            text,
            fontsize=settings["font_size"],
            font=settings["font"],
            color=settings["font_color"],
            stroke_width=settings["stroke_width"],
            stroke_color=settings["stroke_color"],
            size=(1920, 1080),
            align="center",
            method="caption"
        )

        txt_clip = txt_clip.set_position(("center", "center")).set_start(start).set_end(end)
        caption_clips.append(txt_clip)

    return caption_clips

# Apply captions to video
def apply_captions_to_video(video_clip, audio_file, settings):
    captions = generate_captions(audio_file)
    caption_clips = apply_styling(captions, settings)

    # Combine video and caption clips
    final_video = CompositeVideoClip([video_clip] + caption_clips)
    return final_video
