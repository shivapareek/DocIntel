"""
upload.py – Final version
-------------------------
• Saves uploaded file to ./uploads
• Extracts content from PDF/TXT
• Indexes it into RAGService (FAISS/Chroma)
• Registers doc in both rag_service + quiz_service
• Returns doc_id + AI‑generated summary
• ALSO includes `/documents` endpoint for frontend
"""

from pathlib import Path
import shutil
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from services.parser import DocumentParser
from services.summary import generate_summary
from services.singleton import rag_service, quiz_service

# ✅ Initialize Router and Parser
router = APIRouter()
doc_parser = DocumentParser()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a document (PDF or TXT).
    Returns document summary and processing status.
    """
    try:
        # ── Step 1: Check file format
        if not file.filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

        # ── Step 2: Save file to ./uploads
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ── Step 3: Extract text content from file
        content = (
            doc_parser.parse_pdf(str(file_path))
            if file.filename.lower().endswith(".pdf")
            else doc_parser.parse_txt(str(file_path))
        )
        if not content.strip():
            raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable")

        # ── Step 4: Index into vector DB
        doc_id = await rag_service.process_document(content, file.filename)

        # ── Step 5: Register with services
        await rag_service.register_document(doc_id, content)
        await quiz_service.register_document(document_id=doc_id, content=content)

        # ── Step 6: Generate AI summary
        summary = generate_summary(content)

        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "summary": summary,
            "content_length": len(content),
            "message": "Document processed successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {e}")

# ✅ ADD THIS: List uploaded documents (for frontend ChatInterface)
@router.get("/documents")
async def get_documents() -> List[Dict[str, Any]]:
    """
    Returns a list of uploaded documents with metadata.
    Used by frontend to show document dropdown.
    """
    try:
        documents = await rag_service.list_documents()
        return documents
    except Exception as e:
        print(f"❌ Error in /documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to fetch documents.")
