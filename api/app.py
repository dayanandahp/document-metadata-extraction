"""
FastAPI REST API
Wraps the extraction system as a web service
"""

import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from src.text_extractor import extract_text
from src.prompt_builder import build_extraction_prompt
from src.llm_client import LLMClient
from src.post_processor import post_process

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "test")

app = FastAPI(
    title="Document Metadata Extractor",
    description="AI-powered metadata extraction from rental agreements",
    version="1.0.0"
)

# Initialize LLM client on startup
llm_client = None

@app.on_event("startup")
async def startup():
    global llm_client
    llm_client = LLMClient()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI"""
    html_path = os.path.join(TEMPLATE_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Document Metadata Extractor API</h1><p>UI template not found. Use <a href='/docs'>/docs</a> for API.</p>")


@app.get("/api")
async def api_status():
    """API status (JSON)"""
    return {"message": "Document Metadata Extractor API", "status": "running"}


class SampleRequest(BaseModel):
    filename: str


@app.get("/samples")
async def list_samples():
    """List available sample documents for testing"""
    samples = []
    if os.path.exists(SAMPLE_DIR):
        for f in sorted(os.listdir(SAMPLE_DIR)):
            if f.endswith(('.docx', '.png')):
                # Create a short display name
                display = f.replace('.pdf.docx', '').replace('.docx', '').replace('.png', '')
                # Truncate long names
                if len(display) > 35:
                    display = display[:32] + '...'
                samples.append({"name": f, "display_name": display})
    return {"samples": samples}


@app.post("/extract-sample")
async def extract_sample(req: SampleRequest):
    """Extract metadata from a sample document on the server"""
    file_path = os.path.join(SAMPLE_DIR, req.filename)

    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "Sample not found"})

    try:
        text = extract_text(file_path)
        if not text:
            return JSONResponse(status_code=400, content={"error": "Could not extract text"})

        prompt = build_extraction_prompt(text)
        raw_metadata = llm_client.extract_metadata(prompt)
        cleaned = post_process(raw_metadata)

        return {"filename": req.filename, "metadata": cleaned, "status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/extract")
async def extract_metadata(file: UploadFile = File(...)):
    """
    Upload a .docx or .png file and extract metadata
    
    Returns JSON with:
    - agreement_value
    - agreement_start_date
    - agreement_end_date
    - renewal_notice_days
    - party_one
    - party_two
    """
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Step 1: Extract text
        text = extract_text(temp_path)
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from document"}
            )
        
        # Step 2: Build prompt
        prompt = build_extraction_prompt(text)
        
        # Step 3: Get metadata from LLM
        raw_metadata = llm_client.extract_metadata(prompt)
        
        # Step 4: Post-process
        cleaned = post_process(raw_metadata)
        
        return {
            "filename": file.filename,
            "metadata": cleaned,
            "status": "success"
        }
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/health")
async def health():
    return {"status": "healthy"}