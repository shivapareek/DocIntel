

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.singleton import rag_service  

router = APIRouter()



class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None         
    conversation_history: Optional[List[Dict[str, str]]] = []


class QuestionResponse(BaseModel):
    answer: str
    justification: str
    source_snippets: List[str]
    confidence: float


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(payload: QuestionRequest) -> QuestionResponse:
    """
    Intelligent question‑answering with justification + confidence.
    Falls back to friendly error msg if anything breaks.
    """

    try:
        # Core RAG call
        result = await rag_service.answer_question(
            question=payload.question,
            doc_id=payload.document_id or "",
            conversation_history=payload.conversation_history or [],
        )


        return QuestionResponse(
            answer=result["answer"],
            justification=result["justification"],
            source_snippets=result["source_snippets"],
            confidence=result["confidence"],
        )

    except Exception as e:
        print(" ask_question error:", str(e))

        # Context‑aware friendly fallback
        error_msg = (
            "Kuch issue aaya question process karte waqt. "
            + (
                "Document sahi se upload hua hai na? Dubara try karo ya naya doc upload karo."
                if payload.document_id
                else "Different question puchh ke dekho, ya doc upload karke detail analysis karao."
            )
        )

        return QuestionResponse(
            answer=error_msg,
            justification="System error – graceful fallback",
            source_snippets=[],
            confidence=0.0,
        )


@router.post("/clarify")
async def clarify_question(request: QuestionRequest) -> Dict[str, Any]:
    """
    Return clarification suggestions if question vague / doc missing.
    """
    try:
        if request.document_id and not await rag_service.document_exists(
            request.document_id
        ):
            return {
                "suggestions": [
                    "Pehle document upload karo detailed analysis ke liye",
                    "Example: 'Web development me kaun‑kaun si technologies hoti hain?'",
                    "Ya general questions puchho bina doc ke",
                ],
                "original_question": request.question,
                "context": "no_document",
            }

        suggestions = await rag_service.suggest_clarifications(
            question=request.question, doc_id=request.document_id or ""
        )

        return {
            "suggestions": suggestions,
            "original_question": request.question,
            "context": "document_available"
            if request.document_id
            else "general_chat",
        }

    except Exception as e:
        print(" clarify_question error:", str(e))
        return {
            "suggestions": [
                "Apna sawaal thoda aur specific banao",
                "e.g., 'Main technologies kaun‑si hain?' ya 'Key concepts explain karo'",
            ],
            "original_question": request.question,
            "context": "error_recovery",
        }


@router.get("/context/{doc_id}")
async def get_document_context(doc_id: str) -> Dict[str, Any]:
    """
    Return stored context + helper metadata for a document.
    """
    try:
        context = await rag_service.get_document_context(doc_id)

        context.update(
            analysis_ready=True,
            supported_queries=[
                "What technologies are mentioned?",
                "What are the main points?",
                "Explain the key concepts",
                "Summarize the document",
                "What methodologies are used?",
            ],
        )
        return context

    except Exception as e:
        print(" get_document_context error:", str(e))
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Document not found or other error",
                "suggestion": "Document sahi se upload hua hai confirm karo",
                "doc_id": doc_id,
            },
        )


@router.post("/search")
async def search_document(request: QuestionRequest) -> Dict[str, Any]:
    """
    Search inside a document and return relevance‑ranked snippets.
    """
    try:
        if not request.document_id:
            return {
                "query": request.question,
                "results": [],
                "message": "Document ID missing",
                "suggestion": "Pehle doc upload karo phir search karo",
            }

        if not await rag_service.document_exists(request.document_id):
            return {
                "query": request.question,
                "results": [],
                "message": "Document not found",
                "suggestion": "Document upload check karo, ID correct hai?",
            }

        results = await rag_service.search_document(
            query=request.question, doc_id=request.document_id, top_k=5
        )

        enhanced_results = [
            {
                **r,
                "rank": idx + 1,
                "snippet_length": len(r["content"]),
                "relevance_category": (
                    "high" if r["relevance_score"] > 0.8 else
                    "medium" if r["relevance_score"] > 0.5 else
                    "low"
                ),
            }
            for idx, r in enumerate(results)
        ]

        return {
            "query": request.question,
            "results": enhanced_results,
            "message": f"{len(results)} passages mil gaye",
            "total_results": len(results),
            "search_quality": "high" if results else "no_results",
        }

    except Exception as e:
        print(" search_document error:", str(e))
        return {
            "query": request.question,
            "results": [],
            "message": "Search me error aaya",
            "suggestion": "Query rephrase karo ya doc availability check karo",
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Lightweight health‑check for monitoring
    """
    return {
        "status": "healthy",
        "message": "Enhanced QA service running 🟢",
        "features": {
            "basic_chat": "✅",
            "document_analysis": "✅",
            "intelligent_responses": "✅",
            "context_understanding": "✅",
            "technology_extraction": "✅",
            "multilingual_support": "✅ Hindi/English",
        },
        "capabilities": [
            "Smart document analysis",
            "Context‑aware answers",
            "Clarification suggestions",
            "Source citation with snippets",
            "Relevance‑ranked search",
            "Live health monitoring",
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
