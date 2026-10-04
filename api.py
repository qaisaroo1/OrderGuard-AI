"""
FastAPI REST API for OrderGuard AI.
Exposes clean endpoints for PDF ingestion and structured legal action extraction.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from typing import Optional

from core.schemas import (
    ExtractionPageInfo,
    LegalActionMap,
    LegalActionResponse,
)
from core.extractor import DocumentExtractor, ExtractionError
from core.pipeline import LegalExtractionPipeline

MAX_UPLOAD_BYTES = 20 * 1024 * 1024

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


@app.post("/api/extract", response_model=LegalActionResponse)
async def extract_court_order(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    use_mock_fallback: bool = Form(False),
    model_name: str = Form("gemini-3.5-flash-lite"),
):
    """
    Upload a court order PDF or supply plain text to generate a structured Legal Action Map.
    """
    extraction_warnings = []
    extraction_pages = []
    try:
        if file:
            filename = file.filename or ""
            content = await file.read(MAX_UPLOAD_BYTES + 1)
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File too large (max 20 MB)")
            if filename.lower().endswith(".pdf"):
                extracted_data = DocumentExtractor.extract_from_pdf(content)
                text_to_analyze = extracted_data["full_text_with_pages"]
                extraction_warnings = extracted_data["warnings"]
                if not any(page["text"].strip() for page in extracted_data["pages"]):
                    raise HTTPException(
                        status_code=422,
                        detail="No readable text could be extracted from this PDF. "
                        "Check the scan and Tesseract installation.",
                    )
                extraction_pages = [
                    ExtractionPageInfo(
                        page_number=page["page"],
                        method=page["method"],
                        char_count=page["char_count"],
                        ocr_confidence=page["ocr_confidence"],
                        text_preview=page["text"][:1000],
                        raw_text=page["raw_text"],
                        urdu_ocr_text=page["urdu_ocr_text"],
                    )
                    for page in extracted_data["pages"]
                ]
            elif filename.lower().endswith((".txt", ".md")):
                text_to_analyze = content.decode("utf-8", errors="replace")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF, TXT, and Markdown files are accepted.",
                )
        elif raw_text:
            text_to_analyze = raw_text
        else:
            raise HTTPException(status_code=400, detail="Please upload a PDF file or provide raw text.")

        if not text_to_analyze.strip():
            raise HTTPException(
                status_code=422,
                detail="The provided document contains no readable text.",
            )

        request_pipeline = LegalExtractionPipeline(model_name=model_name)
        result = await run_in_threadpool(
            request_pipeline.analyze_order,
            text_to_analyze,
            use_mock_fallback=use_mock_fallback,
        )
        analysis_warnings = []
        if not result.actions:
            analysis_warnings.append(
                "Gemini did not identify actionable directives in this analysis. "
                "No obligations were created. Review the extracted page text below; "
                "analyze again only if you choose to spend another Gemini request."
            )
        return LegalActionResponse(
            **result.model_dump(),
            analysis_warnings=analysis_warnings,
            extraction_warnings=extraction_warnings,
            extraction_pages=extraction_pages,
        )

    except HTTPException:
        raise
    except ExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
