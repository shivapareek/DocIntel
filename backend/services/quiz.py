import uuid
import random
import json
from collections import Counter
from typing import Dict, Any, List

from services.rag import RAGService


class QuizService:
    """Service for generating and evaluating MCQ‑based quizzes."""

    def __init__(self, rag_service: RAGService = None):
        # Shared RAG service
        self.rag_service = rag_service or RAGService()

        # Active MCQ sessions → {session_id: {q_id: question_data}}
        self.active_quizzes: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Cached docs so we don’t pull from RAG repeatedly
        self.documents: Dict[str, str] = {}

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    async def register_document(self, document_id: str, content: str) -> None:
        """Cache document text for faster MCQ generation."""
        self.documents[document_id] = content
        print(f"📌 Registered doc {document_id} (len={len(content)}) in QuizService")

    async def generate_questions(self, doc_id: str, num_questions: int = 3) -> Dict[str, Any]:
        """Return fresh MCQs + opaque session_id (answers hidden)."""
        # 1️⃣  Load / cache full text
        if doc_id not in self.documents:
            if not await self.rag_service.document_exists(doc_id):
                raise ValueError("Document not found")
            ctx = await self.rag_service.get_document_context(doc_id)
            self.documents[doc_id] = ctx["preview"]

        content = self.documents[doc_id]

        # 2️⃣  Extract key concepts for question variety
        concepts = self._extract_key_concepts(content)

        # 3️⃣  Build MCQs
        session_id = str(uuid.uuid4())
        session_data: Dict[str, Dict[str, Any]] = {}
        questions: List[Dict[str, Any]] = []

        for idx in range(num_questions):
            q_id = f"q_{idx + 1}"
            q_text, options_dict, correct_letter, justification = await self._build_single_mcq(doc_id, concepts)
            questions.append({
                "id": q_id,
                "question": q_text,
                "options": options_dict,  # {"A": "…", "B": "…", …}
            })
            session_data[q_id] = {
                "correct": correct_letter,
                "justification": justification,
            }

        self.active_quizzes[session_id] = session_data

        return {
            "session_id": session_id,
            "questions": questions,
        }

    async def grade(self, session_id: str, answers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Evaluate submitted option letters {q_id: "A"}."""
        key = self.active_quizzes.pop(session_id, None)
        if key is None:
            raise ValueError("Invalid or expired session_id")

        results: List[Dict[str, Any]] = []
        for q_id, meta in key.items():
            user_letter = answers.get(q_id, "").upper()
            correct_letter = meta["correct"]
            is_right = user_letter == correct_letter
            results.append({
                "id": q_id,
                "your": user_letter,
                "correct": correct_letter,
                "is_right": is_right,
                "score": 100 if is_right else 0,
                "justification": meta["justification"]
            })
        return results

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------
    def _extract_key_concepts(self, text: str) -> List[str]:
        common = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "this",
            "that", "these", "those",
        }
        words: List[str] = []
        for sentence in text.split("."):
            for word in sentence.split():
                token = word.strip(".,!?;:'\"()[]{}\\").lower()
                if len(token) > 3 and token.isalpha() and token not in common:
                    words.append(token)
        counts = Counter(words)
        return [k for k, _ in counts.most_common(15)]

    async def _build_single_mcq(self, doc_id: str, concepts: List[str]):
        concept = random.choice(concepts) if concepts else "the given document"
        question = f"According to the document, what best describes {concept}?"

        # Correct answer via RAG
        answer = await self.rag_service.answer_question(question=question, doc_id=doc_id)
        correct_text = answer["answer"].strip()
        justification = answer.get("justification", "")

        # Distractors
        distractors = await self._generate_distractors(question, correct_text, doc_id)

        # Shuffle options
        all_opts = distractors + [correct_text]
        random.shuffle(all_opts)
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, all_opts)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == correct_text)

        return question, options_dict, correct_letter, justification

    async def _generate_distractors(self, question: str, correct: str, doc_id: str) -> List[str]:
        distractors: List[str] = []
        generic_pool = [
            "This detail is not covered in the document.",
            "The document discusses a different aspect.",
            "No specific information is given on this point.",
            "This statement contradicts the document's conclusion.",
        ]
        distractors.extend(random.sample(generic_pool, k=2))

        hits = await self.rag_service.search_document(query=question, doc_id=doc_id, top_k=3)
        if hits:
            snippet = hits[-1]["content"][:120].split(".")[0]
            distractors.append(snippet.strip() + " …")

        uniq = [d for d in distractors if d != correct][:3]
        return uniq