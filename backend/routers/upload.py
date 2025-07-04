from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os, shutil
from pathlib import Path
from typing import Dict, Any

from services.parser import DocumentParser
from services.singleton import rag_service, quiz_service   # ✅ shared instances

router = APIRouter()

# Initialize only parser locally
doc_parser = DocumentParser()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a document (PDF or TXT).
    Returns document summary and processing status.
    """
    try:
        if not file.filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(status_code=400,
                                detail="Only PDF and TXT files are supported")

        # Save file
        upload_dir = Path("uploads"); upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse text
        content = (
            doc_parser.parse_pdf(str(file_path))
            if file.filename.lower().endswith(".pdf")
            else doc_parser.parse_txt(str(file_path))
        )
        if not content.strip():
            raise HTTPException(status_code=400,
                                detail="Document appears to be empty or unreadable")

        # Build vector‑store
        doc_id = await rag_service.process_document(content, file.filename)

        # ✅ Register in QuizService so Challenge mode can find it
        await quiz_service.register_document(
            document_id=doc_id,
            content=content            # or summary if you prefer
        )

        # Generate summary
        summary = await rag_service.generate_summary(doc_id)

        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "summary": summary,
            "content_length": len(content),
            "message": "Document processed successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error processing document: {e}")
