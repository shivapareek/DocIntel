"""
routers/challenge.py – final version
-----------------------------------
• Uses **singleton.quiz_service** (which already shares the global RAG instance).
• No embedded quiz logic here; this file is now just a thin FastAPI router.
• Supports:
    POST /api/challenge/generate   → returns 3 fresh MCQs
    POST /api/challenge/evaluate   → grade one answer at a time (A/B/C/D)
"""

from __future__ import annotations

import traceback
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.singleton import quiz_service  # ✅ shared quiz/RAG instance

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

# ----------------------------- Routes ------------------------------ #
@router.post("/challenge/generate", response_model=ChallengeResponse)
async def generate_challenge(req: ChallengeRequest):
    try:
        data = await quiz_service.generate_questions(req.document_id, req.num_questions or 3)
        return ChallengeResponse(**data)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/challenge/evaluate", response_model=AnswerResponse)
async def evaluate_answer(req: AnswerRequest):
    try:
        # grade one question at a time using existing session data
        session = quiz_service.active_quizzes.get(req.session_id)
        if not session or req.question_id not in session:
            raise ValueError("Invalid session or question id")

        meta = session[req.question_id]
        correct_letter = meta["correct"]
        justification = meta["justification"]
        is_correct = req.user_answer.strip().upper() == correct_letter

        # Optionally remove the question entry so it can't be re‑answered
        session.pop(req.question_id, None)
        if not session:
            quiz_service.active_quizzes.pop(req.session_id, None)

        return AnswerResponse(
            correct=is_correct,
            score=100 if is_correct else 0,
            feedback="✅ Correct!" if is_correct else "❌ Incorrect",
            correct_answer=correct_letter,
            justification=justification,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
