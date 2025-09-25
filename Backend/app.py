import base64
from fastapi import FastAPI, Query, File, UploadFile
from PIL import Image
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

# Load environment variables from a .env file
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError(" GEMINI_API_KEY not found in .env file. Please set it in Backend/.env")

# Configure the Gemini API
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Setup the FastAPI application
app = FastAPI(title="Meme Intelligence Bot API")

# Add CORS middleware to allow your extension to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For development only.
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- File Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "memes.csv"
TRENDING_FILE = DATA_DIR / "trending_formats.jsonl" # Path to Pathway's output

# --- Create starter dataset if it's missing ---
if not CSV_FILE.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {
            "caption": "When you fix a bug at 3am",
            "format": "drake",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "caption": "Explaining my code to a coworker",
            "format": "distracted boyfriend",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "caption": "Me after writing one line of code",
            "format": "drake",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]).to_csv(CSV_FILE, index=False)

# --- API Endpoints ---
@app.post("/remix_image")
async def remix_image(file: UploadFile = File(...)):
    """
    Remixes a meme image into a witty IIT student life version using Gemini multimodal API and Pillow.
    """
    try:
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes))
        image = image.convert('RGB')
        max_size = (512, 512)
        image.thumbnail(max_size)
        buf = BytesIO()
        image.save(buf, format='JPEG')
        processed_bytes = buf.getvalue()
        image_b64 = base64.b64encode(processed_bytes).decode('utf-8')
        prompt = "Remix the meme in this image into a witty IIT student life version under 20 words."
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        return JSONResponse(content={"remix": response.text.strip()})
    except Exception as e:
        return JSONResponse(content={"remix": f"Error: {str(e)}"}, status_code=500)
   

import base64
from fastapi.responses import JSONResponse
# --- API Endpoints ---
@app.post("/explain_image")
async def explain_image(file: UploadFile = File(...)):
    """
    Explains why a meme image is funny using the Gemini multimodal API, with Pillow for image processing.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        # Use Pillow to open and process the image
        image = Image.open(BytesIO(image_bytes))
        # Optionally, convert to RGB and resize (example: max 512px)
        image = image.convert('RGB')
        max_size = (512, 512)
        image.thumbnail(max_size)
        # Save processed image to bytes
        buf = BytesIO()
        image.save(buf, format='JPEG')
        processed_bytes = buf.getvalue()
        image_b64 = base64.b64encode(processed_bytes).decode('utf-8')
        prompt = "Explain this meme image in one or two simple sentences so anyone can understand why it's funny. Avoid complex words and keep it casual."
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        return JSONResponse(content={"explanation": response.text.strip()})
    except Exception as e:
        return JSONResponse(content={"explanation": f"Error: {str(e)}"}, status_code=500)

@app.get("/")
def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Meme Intelligence Bot API is running!"}


@app.get("/trending")
def get_trending():
    """
    Uses the LLM to generate today's trending meme format, stores it in the trending_formats.jsonl dataset, and returns it.
    """
    from datetime import datetime
    import json
    try:
        # Use LLM to generate today's trending meme format
        prompt = "Give me the name of a meme format that is trending today. Only return the meme format name, nothing else."
        response = model.generate_content(prompt)
        trending_format = response.text.strip().replace('\n', '')
        # Store in trending_formats.jsonl
        entry = {
            "format": trending_format,
            "count": 1,
            "diff": 1,
            "time": int(datetime.utcnow().timestamp() * 1000)
        }
        # Ensure data dir exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRENDING_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"trending_meme": trending_format}
    except Exception as e:
        return {"trending_meme": f"Error generating or saving trend: {str(e)}"}


@app.get("/explain")
def explain_meme(meme: str = Query(..., min_length=1)):
    """
    Explains why a meme caption is funny using the Gemini API.
    """
    try:
        response = model.generate_content(
            f"Explain this meme caption in plain, simple language and why it's funny:\n\n\"{meme}\""
        )
        return {"explanation": response.text.strip()}
    except Exception as e:
        return {"explanation": f"Error: {str(e)}"}


@app.get("/remix")
def remix_meme(meme: str = Query(..., min_length=1)):
    """
    Remixes a meme caption into an IIT student life version using the Gemini API.
    """
    try:
        response = model.generate_content(
            f"Remix the meme caption '{meme}' into a witty IIT student life version under 20 words."
        )
        return {"remix": response.text.strip()}
    except Exception as e:
        return {"remix": f"Error: {str(e)}"}