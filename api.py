"""
FastAPI REST API for OrderGuard AI.
Exposes clean endpoints for PDF ingestion and structured legal action extraction.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

from core.schemas import LegalActionMap
from core.extractor import DocumentExtractor
from core.pipeline import LegalExtractionPipeline

app = FastAPI(
    title="OrderGuard AI - API",
    description="Autonomous Legal Action Mapping & Execution Engine",
    version="1.0.0"
)

# Enable CORS for cross-origin requests from frontend (React, Next.js, Streamlit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = LegalExtractionPipeline()


@app.get("/")
def root():
    return {
        "project": "OrderGuard AI",
        "description": "Autonomous Legal Action Mapping & Execution Engine",
        "status": "online",
        "endpoints": {
            "docs": "/docs",
            "extract_pdf": "POST /api/extract",
            "sample": "GET /api/sample"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "OrderGuard AI Pipeline"}


@app.get("/api/sample", response_model=LegalActionMap)
def get_sample_action_map():
    """
    Returns a validated sample Legal Action Map.
    Useful for immediate frontend integration without needing an API key.
    """
    return pipeline._get_mock_action_map()


@app.post("/api/extract", response_model=LegalActionMap)
async def extract_court_order(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    use_mock_fallback: bool = Form(True)
):
    """
    Upload a court order PDF or supply plain text to generate a structured Legal Action Map.
    """
    try:
        if file:
            content = await file.read()
            # If uploaded file is a PDF
            if file.filename.lower().endswith(".pdf"):
                extracted_data = DocumentExtractor.extract_from_pdf(content)
                text_to_analyze = extracted_data["full_text_with_pages"]
            else:
                # Text or markdown file
                text_to_analyze = content.decode("utf-8", errors="ignore")
        elif raw_text:
            text_to_analyze = raw_text
        else:
            raise HTTPException(status_code=400, detail="Please upload a PDF file or provide raw text.")

        if not text_to_analyze.strip():
            raise HTTPException(status_code=400, detail="The provided document contains no readable text.")

        # Process through Gemini AI pipeline
        result = pipeline.analyze_order(text_to_analyze, use_mock_fallback=use_mock_fallback)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
