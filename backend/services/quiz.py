import uuid, random
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.rag import RAGService


class QuizService:
    """
    Service for generating and evaluating quiz questions
    """

    def __init__(self):
        self.rag_service = RAGService()
        self.sessions: Dict[str, Any] = {}     # active quiz sessions
        self.documents: Dict[str, str] = {}    # {document_id: full_text}

        # Question templates
        self.question_templates = {
            "comprehension": [
                "What is the main argument presented in the document about {}?",
                "How does the document explain {}?",
                "What evidence does the document provide for {}?",
                "According to the document, what is the significance of {}?"
            ],
            "analysis": [
                "What can be inferred from the document about {}?",
                "How does {} relate to {} based on the document?",
                "What are the implications of {} mentioned in the document?",
                "What pattern or trend does the document suggest about {}?"
            ],
            "application": [
                "Based on the document, how could {} be applied in practice?",
                "What would be the consequences if {} (from the document) were implemented?",
                "How does the document's discussion of {} connect to real‑world scenarios?"
            ]
        }

    # ------------------------------------------------------------------ #
    # NEW: register_document                                             #
    # ------------------------------------------------------------------ #
    async def register_document(self, document_id: str, content: str):
        """
        Store document content for later quiz generation.
        Call this right after a successful upload.
        """
        self.documents[document_id] = content
        print(f"📌 Registered document in QuizService: {document_id} "
              f"(len={len(content)} chars)")

    # ------------------------------------------------------------------ #
    # Question generation                                                #
    # ------------------------------------------------------------------ #
    async def generate_questions(
        self,
        doc_id: str,
        difficulty: str = "medium",
        num_questions: int = 3,
    ) -> Dict[str, Any]: 
        
        """Generate quiz questions from document."""
        
        try:
            # 1️⃣  Get document text (from local cache first)
            if doc_id in self.documents:
                content = self.documents[doc_id]
            else:
                # fallback – verify via RAGService
                if not await self.rag_service.document_exists(doc_id):
                    raise Exception("Document not found")

                ctx = await self.rag_service.get_document_context(doc_id)
                content = ctx["preview"]
                # option: cache it
                self.documents[doc_id] = content

            # 2️⃣  Generate session & key concepts
            session_id = str(uuid.uuid4())
            key_concepts = self._extract_key_concepts(content)

            # 3️⃣  Build questions list
            questions = [
                await self._generate_single_question(doc_id, key_concepts, difficulty, i)
                for i in range(num_questions)
            ]

            # 4️⃣  Save session
            self.sessions[session_id] = {
                "doc_id": doc_id,
                "questions": questions,
                "answers": {},
                "score": 0,
                "total_questions": num_questions,
                "difficulty": difficulty,
                "created_at": datetime.now().isoformat(),
            }

            return {"session_id": session_id, "questions": questions}

        except Exception as e:
            raise Exception(f"Error generating questions: {e}") from e

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Very naïve keyword extraction."""
        common = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "this",
            "that", "these", "those"
        }
        concepts: List[str] = []
        for sentence in content.split("."):
            for word in sentence.split():
                w = word.strip('.,!?;:"()[]{}').lower()
                if len(w) > 3 and w.isalpha() and w not in common:
                    concepts.append(w)
        counts = Counter(concepts)
        return [k for k, _ in counts.most_common(10)]

    async def _generate_single_question(
        self,
        doc_id: str,
        key_concepts: List[str],
        difficulty: str,
        idx: int,
    ) -> Dict[str, Any]:
        q_id = f"q_{idx}"
        qt_pool = (
            ["comprehension"]
            if difficulty == "easy"
            else ["comprehension", "analysis"]
            if difficulty == "medium"
            else ["comprehension", "analysis", "application"]
        )
        q_type = random.choice(qt_pool)
        concept = random.choice(key_concepts) if key_concepts else "the main topic"
        template = random.choice(self.question_templates[q_type])
        q_text = template.format(concept) if "{}" in template else template

        answer = await self.rag_service.answer_question(question=q_text, doc_id=doc_id)
        q_format = random.choice(["short_answer", "multiple_choice"])
        options = (
            await self._generate_multiple_choice_options(q_text, answer["answer"], doc_id)
            if q_format == "multiple_choice"
            else None
        )
        return {
            "id": q_id,
            "question": q_text,
            "type": q_format,
            "options": options,
            "correct_answer": answer["answer"],
            "explanation": answer["justification"],
            "difficulty": difficulty,
            "concept": concept,
        }

    async def _generate_multiple_choice_options(
        self,
        question: str,
        correct: str,
        doc_id: str,
    ) -> List[str]:
        opts = [correct]
        distractors = [
            "This information is not provided in the document.",
            "The document presents a different perspective on this topic.",
            "According to the document, this is not the primary focus.",
        ]
        opts.extend(distractors[:2])
        hits = await self.rag_service.search_document(query=question, doc_id=doc_id, top_k=3)
        if hits:
            opts.append(f"The document states: {hits[-1]['content'][:100]}...")
        random.shuffle(opts)
        return opts[:4]

    # ------------------------------------------------------------------ #
    # Answer evaluation / feedback / session mgmt unchanged              #
    # ------------------------------------------------------------------
    # ... (keep the rest of your existing methods: evaluate_answer, etc.)

    async def evaluate_answer(self, session_id, question_id, user_answer, doc_id):
        # ✅ Example logic — replace with your own evaluation process
        questions = self.sessions[session_id]["questions"]
        question = next((q for q in questions if q["id"] == question_id), None)

        if question is None:
            raise ValueError(f"Question ID {question_id} not found in session.")
        correct = user_answer.strip().lower() == question["correct_answer"].strip().lower()

        return {
            "correct": correct,
            "feedback": "Well done!" if correct else "Try again.",
            "correct_answer": question["correct_answer"],
            "explanation": question["explanation"],
            "justification": "Based on context from document.",
            "score": 1.0 if correct else 0.0
        }
