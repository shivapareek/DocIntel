"""
upload.py – Debug version with better error handling
----------------------------------------------------
• Saves uploaded file to ./uploads
• Extracts content from PDF/TXT with better error handling
• Indexes it into RAGService (FAISS/Chroma)
• Registers doc in both rag_service + quiz_service
• Returns doc_id + AI‑generated summary
• ALSO includes `/documents` endpoint for frontend
"""

from pathlib import Path
import shutil
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from services.parser import DocumentParser
from services.summary import generate_summary
from services.singleton import rag_service, quiz_service

# ✅ Initialize Router and Parser
router = APIRouter()
doc_parser = DocumentParser()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a document (PDF or TXT).
    Returns document summary and processing status.
    """
    try:
        logger.info(f"📁 Starting upload for file: {file.filename}")
        
        # ── Step 1: Check file format
        if not file.filename.lower().endswith((".pdf", ".txt")):
            logger.error(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

        # ── Step 2: Read file content first (before saving)
        logger.info(f"📖 Reading file content: {file.filename}")
        logger.info(f"📊 File info - Content Type: {file.content_type}, Size: {file.size}")
        
        try:
            # Reset file pointer to beginning
            await file.seek(0)
            file_content = await file.read()
            logger.info(f"✅ File content read. Size: {len(file_content)} bytes")
            
            # Debug: Print first 100 characters if available
            if len(file_content) > 0:
                try:
                    preview = file_content[:100].decode('utf-8', errors='ignore')
                    logger.info(f"📝 Content preview: {preview}")
                except:
                    logger.info(f"📝 Binary content preview: {file_content[:100]}")
            
            if len(file_content) == 0:
                # Let's check if file.size is available
                if hasattr(file, 'size') and file.size is not None:
                    logger.info(f"📊 File.size attribute: {file.size}")
                
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            
        except HTTPException:
            raise
        except Exception as read_error:
            logger.error(f"❌ Error reading file: {read_error}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {read_error}")
        
        # ── Step 3: Save file to ./uploads
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        
        logger.info(f"💾 Saving file to: {file_path}")
        
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            logger.info(f"✅ File saved successfully. Size: {file_path.stat().st_size} bytes")
        except Exception as save_error:
            logger.error(f"❌ Error saving file: {save_error}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {save_error}")

        # ── Step 4: Extract text content from file
        logger.info(f"🔍 Extracting content from: {file.filename}")
        
        try:
            if file.filename.lower().endswith(".pdf"):
                logger.info("📄 Processing as PDF")
                content = doc_parser.parse_pdf(str(file_path))
            else:
                logger.info("📝 Processing as TXT")
                content = doc_parser.parse_txt(str(file_path))
            
            logger.info(f"✅ Content extracted. Length: {len(content)} chars")
            
        except Exception as parse_error:
            logger.error(f"❌ Error parsing file: {parse_error}")
            # Try alternative text reading for TXT files
            if file.filename.lower().endswith(".txt"):
                logger.info("🔄 Trying alternative text reading...")
                try:
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    content = None
                    
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                content = f.read()
                            logger.info(f"✅ Successfully read with {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            logger.warning(f"⚠️ Failed to read with {encoding} encoding")
                            continue
                    
                    if content is None:
                        raise HTTPException(status_code=400, detail="Unable to read text file with any encoding")
                        
                except Exception as alt_error:
                    logger.error(f"❌ Alternative text reading failed: {alt_error}")
                    raise HTTPException(status_code=500, detail=f"Error reading text file: {alt_error}")
            else:
                raise HTTPException(status_code=500, detail=f"Error parsing document: {parse_error}")

        # Check if content is empty
        if not content or not content.strip():
            logger.error("❌ Document appears to be empty")
            raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable")

        # ── Step 5: Index into vector DB
        logger.info("🔍 Processing document for vector DB")
        try:
            doc_id = await rag_service.process_document(content, file.filename)
            logger.info(f"✅ Document indexed with ID: {doc_id}")
        except Exception as index_error:
            logger.error(f"❌ Error indexing document: {index_error}")
            raise HTTPException(status_code=500, detail=f"Error indexing document: {index_error}")

        # ── Step 6: Register with services
        logger.info("📋 Registering with services")
        try:
            await rag_service.register_document(doc_id, content)
            await quiz_service.register_document(document_id=doc_id, content=content)
            logger.info("✅ Document registered with services")
        except Exception as register_error:
            logger.error(f"❌ Error registering document: {register_error}")
            raise HTTPException(status_code=500, detail=f"Error registering document: {register_error}")

        # ── Step 7: Generate AI summary
        logger.info("🤖 Generating AI summary")
        try:
            summary = generate_summary(content)
            logger.info("✅ Summary generated successfully")
        except Exception as summary_error:
            logger.error(f"❌ Error generating summary: {summary_error}")
            # Don't fail the upload if summary generation fails
            summary = "Summary generation failed, but document was uploaded successfully."

        logger.info(f"🎉 Upload completed successfully for: {file.filename}")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "summary": summary,
            "content_length": len(content),
            "message": "Document processed successfully",
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error processing document: {e}")

# ✅ List uploaded documents (for frontend ChatInterface)
@router.get("/documents")
async def get_documents() -> List[Dict[str, Any]]:
    """
    Returns a list of uploaded documents with metadata.
    Used by frontend to show document dropdown.
    """
    try:
        logger.info("📋 Fetching documents list")
        documents = await rag_service.list_documents()
        logger.info(f"✅ Found {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"❌ Error in /documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to fetch documents.")