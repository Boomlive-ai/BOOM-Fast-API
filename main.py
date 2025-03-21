# from flask import Flask
# from flask_cors import CORS
# from dotenv import load_dotenv
# import os

# # Import blueprints from the modules
# from factcheck.routes import factcheck_bp
# from chatbot.routes import chatbot_bp
# from media_processing.routes import media_processing_bp

# # Initialize the app
# app = Flask(__name__)
# CORS(app)
# load_dotenv()

# # Configuration
# app.config['UPLOAD_FOLDER'] = 'uploads'
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Register blueprints
# app.register_blueprint(factcheck_bp, url_prefix='/factcheck')
# app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
# app.register_blueprint(media_processing_bp, url_prefix='/media')

# @app.route('/')
# def index():
#     return {"message": "Welcome to the Boomlive!"}

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import routers from the modules
from factcheck.routes import factcheck_router
from chatbot.routes import chatbot_router
from media_processing.routes import media_processing_router

# Load environment variables
load_dotenv()

# Initialize the app
app = FastAPI(
    title="Boomlive API",
    description="API for fact-checking, chatbot, and media processing services",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Include routers
app.include_router(
    factcheck_router,
    prefix="/factcheck",
    tags=["Fact Checking"]
)

app.include_router(
    chatbot_router,
    prefix="/chatbot",
    tags=["Chatbot"]
)

app.include_router(
    media_processing_router,
    prefix="/media",
    tags=["Media Processing"]
)

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {"message": "Welcome to the Boomlive!"}

# For development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        # host="127.0.0.1",
        port=8000, # Enable auto-reload during development
        
    )