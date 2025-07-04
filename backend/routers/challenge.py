from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from services.singleton import quiz_service  # ✅ Singleton shared service
import traceback  # ✅ For debugging

router = APIRouter()

# Request and Response Models
class ChallengeRequest(BaseModel):
    document_id: str
    difficulty: Optional[str] = "medium"  # Options: easy, medium, hard

class Question(BaseModel):
    id: str
    question: str
    type: str  # "multiple_choice", "short_answer", "true_false"
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: str
    difficulty: str

class ChallengeResponse(BaseModel):
    questions: List[Question]
    session_id: str

class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    user_answer: str
    document_id: str

class AnswerResponse(BaseModel):
    correct: bool
    feedback: str
    correct_answer: str
    explanation: str
    justification: str
    score: float

class HintRequest(BaseModel):
    session_id: str
    question_id: str
    document_id: str


# -----------------------------
# Routes
# -----------------------------

@router.post("/challenge/generate", response_model=ChallengeResponse)
async def generate_challenge(request: ChallengeRequest) -> ChallengeResponse:
    """
    Generate logic-based questions from a document
    """
    try:
        result = await quiz_service.generate_questions(
            doc_id=request.document_id,
            difficulty=request.difficulty,
            num_questions=3
        )
        return ChallengeResponse(
            questions=result["questions"],
            session_id=result["session_id"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating challenge: {str(e)}")


@router.post("/challenge/evaluate", response_model=AnswerResponse)
async def evaluate_answer(request: AnswerRequest) -> AnswerResponse:
    """
    Evaluate user's answer to a challenge question
    """
    try:
        result = await quiz_service.evaluate_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            doc_id=request.document_id
        )
        return AnswerResponse(
            correct=result["correct"],
            feedback=result["feedback"],
            correct_answer=result["correct_answer"],
            explanation=result["explanation"],
            justification=result["justification"],
            score=result["score"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.get("/challenge/session/{session_id}")
async def get_session_progress(session_id: str) -> Dict[str, Any]:
    """
    Get challenge session progress and metadata
    """
    try:
        progress = await quiz_service.get_session_progress(session_id)
        return {
            "message": "Session progress retrieved",
            "data": progress
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting session progress: {str(e)}")


@router.post("/challenge/hint")
async def get_hint(request: HintRequest) -> Dict[str, str]:
    """
    Get a hint for a specific challenge question
    """
    try:
        hint = await quiz_service.get_hint(
            session_id=request.session_id,
            question_id=request.question_id,
            doc_id=request.document_id
        )
        return {"hint": hint}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting hint: {str(e)}")


@router.delete("/challenge/session/{session_id}")
async def end_session(session_id: str) -> Dict[str, str]:
    """
    End a challenge session and return final results
    """
    try:
        results = await quiz_service.end_session(session_id)
        return {
            "message": "Session ended successfully",
            **results
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")
