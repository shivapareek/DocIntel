from pathlib import Path
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.parser import DocumentParser
from services.summary import generate_summary
from services.singleton import rag_service, quiz_service

router = APIRouter()
parser = DocumentParser()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and process a document. Returns its summary and metadata."""
    try:
        filename = file.filename or "uploaded_file"

        # Validate file format
        if not filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

        await file.seek(0)
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Save the file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # Parse content
        try:
            if filename.lower().endswith(".pdf"):
                content = parser.parse_pdf(str(file_path))
            else:
                content = parser.parse_txt(str(file_path))
        except Exception:
            # Fallback decoding for TXT
            if filename.lower().endswith(".txt"):
                content = None
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                if content is None:
                    raise HTTPException(status_code=400, detail="Unable to read text file")
            else:
                raise HTTPException(status_code=500, detail="Error parsing document")

        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="Document is empty or unreadable")

        # Index and register
        doc_id = await rag_service.process_document(content, filename)
        await rag_service.register_document(doc_id, content)
        await quiz_service.register_document(doc_id, content)

        try:
            summary = generate_summary(content)
        except Exception:
            summary = "Summary generation failed, but document was uploaded."

        return {
            "success": True,
            "document_id": doc_id,
            "filename": filename,
            "summary": summary,
            "content_length": len(content),
            "message": "Document processed successfully",
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Unexpected error in document upload")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

@router.get("/documents")
async def get_documents() -> List[Dict[str, Any]]:
    """List uploaded documents for selection."""
    try:
        return await rag_service.list_documents()
    except Exception:
        logger.exception("Error listing documents")
        raise HTTPException(status_code=500, detail="Unable to fetch documents.")
