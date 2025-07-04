from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


from fastapi import Request
from services.singleton import rag_service  # ✅ use shared instance


router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    document_id: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class QuestionResponse(BaseModel):
    answer: str
    justification: str
    source_snippets: List[str]
    confidence: float

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(payload: QuestionRequest) -> QuestionResponse:
    """
    Answer a question based on the uploaded document.
    """
    print("📩 /api/qa/ask called with:", payload.question)

    try:
        doc_exists = await rag_service.document_exists(payload.document_id)
        if not doc_exists:
            raise HTTPException(status_code=404, detail="Document not found")

        result = await rag_service.answer_question(
            question=payload.question,
            doc_id=payload.document_id,
            conversation_history=payload.conversation_history or []
        )

        return QuestionResponse(
            answer=result["answer"],
            justification=result["justification"],
            source_snippets=result["source_snippets"],
            confidence=result["confidence"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")



@router.post("/clarify")
async def clarify_question(request: QuestionRequest) -> Dict[str, Any]:
    """
    Suggest clarifications or related questions based on the user's question
    """
    try:
        doc_exists = await rag_service.document_exists(request.document_id)
        if not doc_exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        suggestions = await rag_service.suggest_clarifications(
            question=request.question,
            doc_id=request.document_id
        )
        
        return {
            "suggestions": suggestions,
            "original_question": request.question
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating clarifications: {str(e)}")

@router.get("/context/{doc_id}")
async def get_document_context(doc_id: str) -> Dict[str, Any]:
    """
    Get document context and metadata
    """
    try:
        context = await rag_service.get_document_context(doc_id)
        return context
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document context: {str(e)}")

@router.post("/search")
async def search_document(request: QuestionRequest) -> Dict[str, Any]:
    """
    Search for relevant passages in the document
    """
    try:
        doc_exists = await rag_service.document_exists(request.document_id)
        if not doc_exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        results = await rag_service.search_document(
            query=request.question,
            doc_id=request.document_id,
            top_k=5
        )
        
        return {
            "query": request.question,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching document: {str(e)}")