"""
routers/challenge.py – Enhanced version with detailed feedback
------------------------------------------------------------
• Uses improved QuizService with realistic question generation
• Provides detailed justifications and explanations
• Better error handling and response formatting
"""

from __future__ import annotations

import traceback
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.singleton import rag_service, quiz_service

router = APIRouter()

# ----------------------------- Schemas ----------------------------- #
class ChallengeRequest(BaseModel):
    document_id: str
    num_questions: int | None = 3

class PublicQuestion(BaseModel):
    id: str
    question: str
    options: Dict[str, str]

class ChallengeResponse(BaseModel):
    session_id: str
    questions: list[PublicQuestion]
    message: str | None = None

class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    user_answer: str  # A/B/C/D

class AnswerResponse(BaseModel):
    correct: bool
    score: int
    feedback: str
    correct_answer: str
    justification: str
    explanation: str
    user_answer: str

class BatchAnswerRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]  # {question_id: "A/B/C/D"}

class BatchAnswerResponse(BaseModel):
    results: list[Dict[str, Any]]
    overall_score: float
    total_questions: int
    correct_answers: int

# ----------------------------- Routes ------------------------------ #
@router.post("/challenge/generate", response_model=ChallengeResponse)
async def generate_challenge(req: ChallengeRequest):
    """Generate realistic, context-aware challenge questions."""
    try:
        # Validate document exists
        if not await quiz_service.rag_service.document_exists(req.document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate questions
        data = await quiz_service.generate_questions(req.document_id, req.num_questions or 3)
        
        return ChallengeResponse(
            session_id=data["session_id"],
            questions=data["questions"],
            message=f"Generated {len(data['questions'])} contextual questions from your document"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating challenge: {str(e)}")


@router.post("/challenge/evaluate", response_model=AnswerResponse)
async def evaluate_answer(req: AnswerRequest):
    """Evaluate a single answer with detailed feedback."""
    try:
        # Validate session and question
        session = quiz_service.active_quizzes.get(req.session_id)
        if not session or req.question_id not in session:
            raise HTTPException(status_code=404, detail="Invalid session or question ID")

        # Get answer metadata
        meta = session[req.question_id]
        correct_letter = meta["correct"]
        justification = meta["justification"]
        explanation = meta.get("explanation", "")
        
        # Evaluate answer
        user_answer = req.user_answer.strip().upper()
        is_correct = user_answer == correct_letter
        
        # Generate feedback
        if is_correct:
            feedback = "🎉 Excellent! You got it right!"
        else:
            feedback = f"❌ Not quite. The correct answer is {correct_letter}."
        
        # Remove answered question from session
        session.pop(req.question_id, None)
        if not session:
            quiz_service.active_quizzes.pop(req.session_id, None)

        return AnswerResponse(
            correct=is_correct,
            score=100 if is_correct else 0,
            feedback=feedback,
            correct_answer=correct_letter,
            justification=justification,
            explanation=explanation,
            user_answer=user_answer
        )
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.post("/challenge/batch-evaluate", response_model=BatchAnswerResponse)
async def batch_evaluate_answers(req: BatchAnswerRequest):
    """Evaluate all answers at once with comprehensive results."""
    try:
        # Validate session
        session = quiz_service.active_quizzes.get(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Invalid or expired session")
        
        results = []
        correct_count = 0
        total_questions = len(session)
        
        # Evaluate each answer
        for question_id, meta in session.items():
            user_answer = req.answers.get(question_id, "").strip().upper()
            correct_letter = meta["correct"]
            is_correct = user_answer == correct_letter
            
            if is_correct:
                correct_count += 1
                feedback = "🎉 Correct!"
            else:
                feedback = f"❌ Incorrect. Correct answer: {correct_letter}"
            
            results.append({
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": correct_letter,
                "is_correct": is_correct,
                "score": 100 if is_correct else 0,
                "feedback": feedback,
                "justification": meta["justification"],
                "explanation": meta.get("explanation", "")
            })
        
        # Calculate overall score
        overall_score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Clean up session
        quiz_service.active_quizzes.pop(req.session_id, None)
        
        return BatchAnswerResponse(
            results=results,
            overall_score=round(overall_score, 2),
            total_questions=total_questions,
            correct_answers=correct_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in batch evaluation: {str(e)}")


@router.get("/challenge/session/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a challenge session."""
    try:
        session = quiz_service.active_quizzes.get(session_id)
        if not session:
            return {"exists": False, "message": "Session not found or expired"}
        
        return {
            "exists": True,
            "questions_remaining": len(session),
            "question_ids": list(session.keys())
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking session: {str(e)}")


@router.delete("/challenge/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a challenge session."""
    try:
        session = quiz_service.active_quizzes.pop(session_id, None)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.get("/challenge/stats")
async def get_challenge_stats():
    """Get statistics about active challenge sessions."""
    try:
        active_sessions = len(quiz_service.active_quizzes)
        total_questions = sum(len(session) for session in quiz_service.active_quizzes.values())
        
        return {
            "active_sessions": active_sessions,
            "total_active_questions": total_questions,
            "cached_documents": len(quiz_service.documents)
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")