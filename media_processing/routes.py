from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from media_processing.video_processing import process_video_file
from media_processing.audio_processing import process_audio_file
from media_processing.image_processing import extract_text_from_image
from media_processing.tools.automate_input_processing import detect_and_process_file, detect_and_process_json
from moviepy.video.io.VideoFileClip import VideoFileClip
from media_processing.twitter_processor import TwitterMediaProcessor
from bs4 import BeautifulSoup
import os
import shutil
import requests

app = FastAPI()
# Initialize the Twitter processor
twitter_processor = TwitterMediaProcessor()
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
            result = await detect_and_process_file(file, file_path)
            os.remove(file_path)
            return result
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    elif json_data:
        return detect_and_process_json(json_data)
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type")



# New GET endpoint for Twitter media summary
@media_processing_router.get("/twitter/summary")
async def get_twitter_media_summary(url: str = Query(..., description="Twitter/X URL to process")):
    """
    Extract and summarize media content from a Twitter/X URL
    
    Parameters:
    - url: Twitter/X post URL (e.g., https://twitter.com/username/status/1234567890)
    
    Returns:
    - JSON response with media summaries, transcripts, and extracted text
    """
    
    # Validate URL format
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # # Basic Twitter URL validation
    # if not any(domain in url.lower() for domain in ['twitter.com', 'x.com']):
    #     raise HTTPException(status_code=400, detail="Please provide a valid Twitter/X URL")
    
    try:
        # Process the Twitter URL
        result = twitter_processor.process_twitter_url(url)
        
        # Check if there was an error during processing
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Return the processed results
        return JSONResponse(content={
            "status": "success",
            "data": result,
            "message": f"Successfully processed {result.get('media_count', 0)} media items from Twitter post"
        })
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        # Handle any unexpected errors
        raise HTTPException(status_code=500, detail=f"Failed to process Twitter URL: {str(e)}")

# Alternative endpoint with different URL structure
@media_processing_router.get("/twitter/analyze")
async def analyze_twitter_media(
    twitter_url: str = Query(..., description="Twitter/X URL to analyze"),
    include_raw_data: bool = Query(False, description="Include raw processing data in response")
):
    """
    Analyze and summarize media content from Twitter/X posts
    
    Parameters:
    - twitter_url: Full Twitter/X post URL
    - include_raw_data: Whether to include raw processing data (optional, default: False)
    """
    
    if not twitter_url:
        raise HTTPException(status_code=400, detail="twitter_url parameter is required")
    
    try:
        result = twitter_processor.process_twitter_url(twitter_url)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Create a formatted response
        response_data = {
            "url": result['twitter_url'],
            "total_media": result['media_count'],
            "summary": [],
            "details": []
        }
        
        # Process each media item for summary
        for media in result.get('media_results', []):
            if 'error' not in media:
                summary_item = {
                    "type": media.get('type'),
                    "summary": media.get('summary', 'No summary available')
                }
                response_data['summary'].append(summary_item)
                
                if include_raw_data:
                    response_data['details'].append(media)
        
        return JSONResponse(content={
            "status": "success",
            "data": response_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

app.include_router(media_processing_router, prefix="/media")
