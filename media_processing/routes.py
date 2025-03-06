from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from media_processing.video_processing import process_video_file
from media_processing.audio_processing import process_audio_file
from media_processing.image_processing import extract_text_from_image
from media_processing.tools.automate_input_processing import detect_and_process_file, detect_and_process_json
from moviepy.video.io.VideoFileClip import VideoFileClip
from bs4 import BeautifulSoup
import os
import shutil
import requests

app = FastAPI()
media_processing_router = APIRouter()
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'mp3', 'wav', 'jpg', 'jpeg', 'png', 'webp'}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@media_processing_router.get("/")
def documentation():
    return JSONResponse(content={"message": "API documentation goes here"})

@media_processing_router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        video_clip = VideoFileClip(file_path)
        duration = video_clip.duration
        transcript = process_video_file(file_path).text
        video_clip.close()
        return {"filename": file.filename, "duration": duration, "path": file_path, "transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

@media_processing_router.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        transcript = process_audio_file(file_path)
        return {"filename": file.filename, "path": file_path, "transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

@media_processing_router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        text_from_image = extract_text_from_image(file_path)
        return {"filename": file.filename, "path": file_path, "text": text_from_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@media_processing_router.post("/scrape_url")
async def scrape_url(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve page. Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().strip()
        return {"url": url, "extracted_text": page_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape URL: {str(e)}")

@media_processing_router.post("/process_input")
async def process_input(file: UploadFile = None, json_data: dict = None):
    if file:
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type.")
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            result = detect_and_process_file(file, file_path)
            os.remove(file_path)
            return result
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    elif json_data:
        return detect_and_process_json(json_data)
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type")

app.include_router(media_processing_router, prefix="/media")
