from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from moviepy.video.io.VideoFileClip import VideoFileClip
from media_processing.video_processing import process_video_file
from media_processing.audio_processing import process_audio_file
from media_processing.image_processing import extract_text_from_image
from media_processing.url_processing import scrape_url
import shutil
import os
# Helper function to check for allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'mp3', 'wav', 'jpg', 'jpeg', 'png'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Function to detect content type and call the respective processing function

async def detect_and_process_file(file: UploadFile, file_path: str):
    """Processes the file based on its extension."""
    extension = file.filename.rsplit('.', 1)[1].lower()

    try:
        if extension in {'mp4', 'avi', 'mov', 'mkv', 'flv'}:
            # Process video
            video_clip = VideoFileClip(file_path)
            duration = video_clip.duration
            transcript = process_video_file(file_path).text
            video_clip.close()
            return {"filename": file.filename, "duration": duration, "text": transcript}

        elif extension in {'mp3', 'wav'}:
            # Process audio
            transcript = process_audio_file(file_path)
            return {"filename": file.filename, "text": transcript}

        elif extension in {'jpg', 'jpeg', 'png'}:
            # Process image
            text_from_image = extract_text_from_image(file_path)
            return {"filename": file.filename, "text": text_from_image}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    finally:
        # Clean up the file after processing
        os.remove(file_path)

async def detect_and_process_json(data: dict):
    """Process JSON data."""
    if not data:
        raise HTTPException(status_code=400, detail="No JSON data provided")

    if 'text' in data:
        return {"text": data['text']}
    
    elif 'url' in data:
        return await scrape_url(data['url'])

    else:
        raise HTTPException(status_code=400, detail="No recognizable JSON input")