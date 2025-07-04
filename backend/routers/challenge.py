"""
challenge.py  – AI Challenge‑Mode endpoints
==========================================

• POST /challenge/generate   → 3 logic‑based questions from a document
• POST /challenge/evaluate   → score one answer (correct?, score, feedback, justification, reference)
• GET  /challenge/session/{session_id} → session progress
• POST /challenge/hint       → short hint
• DELETE /challenge/session/{session_id} → finalize + summary

Everything is in‑memory; swap the QuizService implementation if you want
persistent storage or a real LLM‑powered Q‑gen / scoring pipeline.
"""
from __future__ import annotations

import uuid
import random
import traceback
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
#                               Helper functions                              #
# --------------------------------------------------------------------------- #
def _similarity(a: str, b: str) -> float:
    """Levenshtein similarity (0‑1) using difflib."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _fake_questions(num: int, difficulty: str) -> List[Dict[str, Any]]:
    """Stand‑in stub that fabricates deterministic questions."""
    sample_bank = [
        ("What is the main idea of the introduction?", "To explain the topic's context"),
        ("State one key finding from section 2.", "Dataset X outperforms baseline Y"),
        ("Why was method C chosen over method D?", "It achieves higher accuracy"),
        ("True or False: The algorithm is unsupervised.", "False"),
        ("Provide one future‑work direction mentioned.", "Scaling to real‑time data"),
    ]
    random.shuffle(sample_bank)
    out = []

    for q_text, ans in sample_bank[:num]:
        qtype = "true_false" if ans in ("True", "False") else "short_answer"
        q = {
            "id": str(uuid.uuid4()),
            "question": q_text,
            "type": qtype,
            "options": ["True", "False"] if qtype == "true_false" else None,
            "correct_answer": ans,
            "explanation": f"The document states: “{ans} …”",
            "difficulty": difficulty,
        }
        out.append(q)
    return out


# --------------------------------------------------------------------------- #
#                               Quiz  Service                                 #
# --------------------------------------------------------------------------- #
class QuizService:
    """
    Very small in‑memory service.

    sessions = {
        session_id: {
            "doc_id": str,
            "questions": [dict],            # original order
            "qmap": {question_id: dict},    # id → question
            "answers": {question_id: answer_dict},
        }
    }
    """

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    # ----------------------------- generation ------------------------------ #
    async def generate_questions(
        self, *, doc_id: str, difficulty: str, num_questions: int = 3
    ) -> Dict[str, Any]:
        questions = _fake_questions(num_questions, difficulty)
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "doc_id": doc_id,
            "questions": questions,
            "qmap": {q["id"]: q for q in questions},
            "answers": {},
        }
        return {"session_id": session_id, "questions": questions}

    # ----------------------------- evaluation ------------------------------ #
    async def evaluate_answer(
        self,
        *,
        session_id: str,
        question_id: str,
        user_answer: str,
        doc_id: str,
    ) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError("Unknown session")

        session = self.sessions[session_id]
        if question_id not in session["qmap"]:
            raise ValueError("Unknown question id")

        q = session["qmap"][question_id]
        gold = q["correct_answer"]
        sim = _similarity(user_answer, gold)
        score = round(sim * 100)  # 0‑100

        correct = score >= 80
        feedback = (
            "Excellent answer! ✅"
            if correct
            else "Close – review the key sentence. 🔍" if score >= 60 else "Not quite, try re‑reading the section. ❌"
        )

        result = {
            "correct": correct,
            "score": score,
            "feedback": feedback,
            "justification": f"Your answer matched {score}% of the expected answer.",
            "correct_answer": gold,
            "explanation": q["explanation"],
            "reference": q["explanation"],  # here we reuse explanation as reference
        }

        # store
        session["answers"][question_id] = {
            "user_answer": user_answer,
            "evaluation": result,
        }
        return result

    # ------------------------ session meta / utilities --------------------- #
    async def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError("Unknown session")
        session = self.sessions[session_id]
        answered = len(session["answers"])
        total = len(session["questions"])
        avg = (
            round(
                sum(a["evaluation"]["score"] for a in session["answers"].values())
                / answered
            )
            if answered
            else 0
        )
        return {
            "answered": answered,
            "total_questions": total,
            "average_score": avg,
        }

    async def get_hint(self, *, session_id: str, question_id: str, doc_id: str) -> str:
        if session_id not in self.sessions:
            raise ValueError("Unknown session")
        q = self.sessions[session_id]["qmap"][question_id]
        # Simple hint = first 4 words of answer
        return "Hint: " + " ".join(q["correct_answer"].split()[:4]) + "..."

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        progress = await self.get_session_progress(session_id)
        self.sessions.pop(session_id, None)
        return {"final_results": progress}


# Singleton instance
quiz_service = QuizService()

# --------------------------------------------------------------------------- #
#                              FastAPI router                                 #
# --------------------------------------------------------------------------- #
router = APIRouter()


# ------------------------------- models ----------------------------------- #
class ChallengeRequest(BaseModel):
    document_id: str
    difficulty: Optional[str] = Field(default="medium", pattern="^(easy|medium|hard)$")



class Question(BaseModel):
    id: str
    question: str
    type: str
    options: Optional[List[str]] = None
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
    score: float
    feedback: str
    justification: str
    correct_answer: str
    explanation: str
    reference: str


class HintRequest(BaseModel):
    session_id: str
    question_id: str
    document_id: str


# ------------------------------ endpoints --------------------------------- #
@router.post("/challenge/generate", response_model=ChallengeResponse)
async def generate_challenge(request: ChallengeRequest) -> ChallengeResponse:
    """Generate questions."""
    try:
        result = await quiz_service.generate_questions(
            doc_id=request.document_id,
            difficulty=request.difficulty,
            num_questions=3,
        )
        return ChallengeResponse(
            questions=result["questions"], session_id=result["session_id"]
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/challenge/evaluate", response_model=AnswerResponse)
async def evaluate_answer(request: AnswerRequest) -> AnswerResponse:
    """Score one answer."""
    try:
        result = await quiz_service.evaluate_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            doc_id=request.document_id,
        )
        return AnswerResponse(**result)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/challenge/session/{session_id}")
async def get_session_progress(session_id: str) -> Dict[str, Any]:
    try:
        data = await quiz_service.get_session_progress(session_id)
        return {"message": "Progress", "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/challenge/hint")
async def get_hint(request: HintRequest) -> Dict[str, str]:
    try:
        hint = await quiz_service.get_hint(
            session_id=request.session_id,
            question_id=request.question_id,
            doc_id=request.document_id,
        )
        return {"hint": hint}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/challenge/session/{session_id}")
async def end_session(session_id: str) -> Dict[str, Any]:
    try:
        results = await quiz_service.end_session(session_id)
        return {"message": "Session ended", **results}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
