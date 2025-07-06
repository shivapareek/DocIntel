import uuid
import random
import json
import re
from collections import Counter
from typing import Dict, Any, List, Tuple
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

from services.rag import RAGService


class QuizService:
    """Enhanced service for generating contextual, balanced MCQ questions."""

    def __init__(self, rag_service: RAGService = None):
        self.rag_service = rag_service or RAGService()
        self.active_quizzes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.documents: Dict[str, str] = {}
        self.used_questions: Dict[str, set] = {}  # Track used questions per document
        
        # Load environment variables
        load_dotenv()
        
        # Improved question templates with better variety
        self.question_templates = {
            "definition": [
                "What does {term} mean in this context?",
                "How is {term} best described?",
                "Which statement best defines {term}?",
                "What is the meaning of {term}?",
                "{term} can be defined as:"
            ],
            "purpose": [
                "What is the primary purpose of {concept}?",
                "Why is {concept} important?",
                "What objective does {concept} serve?",
                "The main goal of {concept} is to:",
                "What problem does {concept} solve?"
            ],
            "process": [
                "How does {process} work?",
                "What are the steps involved in {process}?",
                "Which approach is used for {process}?",
                "The {process} involves:",
                "What is the methodology behind {process}?"
            ],
            "comparison": [
                "What is the main difference between {concept1} and {concept2}?",
                "How does {concept1} compare to {concept2}?",
                "What advantage does {concept1} have over {concept2}?",
                "Which is more effective: {concept1} or {concept2}?",
                "What distinguishes {concept1} from {concept2}?"
            ],
            "application": [
                "When would you use {concept}?",
                "In which scenario is {concept} most applicable?",
                "What is a practical application of {concept}?",
                "Where is {concept} commonly implemented?",
                "Which situation requires {concept}?"
            ],
            "technical": [
                "Which technology is used for {feature}?",
                "What framework supports {functionality}?",
                "How is {feature} implemented?",
                "Which tool is best for {task}?",
                "What technology stack includes {component}?"
            ]
        }

    async def register_document(self, document_id: str, content: str) -> None:
        """Cache document text for faster MCQ generation."""
        self.documents[document_id] = content
        self.used_questions[document_id] = set()
        print(f"📌 Registered doc {document_id} (len={len(content)}) in QuizService")

    async def generate_questions(self, doc_id: str, num_questions: int = 3) -> Dict[str, Any]:
        """Generate diverse, contextual MCQ questions."""
        
        # Load document content
        if doc_id not in self.documents:
            if not await self.rag_service.document_exists(doc_id):
                raise ValueError("Document not found")
            doc_data = self.rag_service.documents[doc_id]
            self.documents[doc_id] = doc_data["content"]
            self.used_questions[doc_id] = set()

        content = self.documents[doc_id]
        
        # Extract key concepts and information
        concepts = self._extract_concepts(content)
        
        # Generate session
        session_id = str(uuid.uuid4())
        session_data: Dict[str, Dict[str, Any]] = {}
        questions: List[Dict[str, Any]] = []

        # Generate diverse questions
        attempts = 0
        max_attempts = num_questions * 3
        
        while len(questions) < num_questions and attempts < max_attempts:
            attempts += 1
            
            try:
                question_data = await self._create_contextual_question(
                    content, concepts, doc_id, len(questions)
                )
                
                # Check if question is unique
                question_signature = self._get_question_signature(question_data["question"])
                if question_signature not in self.used_questions[doc_id]:
                    self.used_questions[doc_id].add(question_signature)
                    
                    q_id = f"q_{len(questions) + 1}"
                    questions.append({
                        "id": q_id,
                        "question": question_data["question"],
                        "options": question_data["options"],
                    })
                    
                    session_data[q_id] = {
                        "correct": question_data["correct_letter"],
                        "justification": question_data["justification"],
                        "explanation": question_data["explanation"]
                    }
                    
            except Exception as e:
                print(f"Error generating question: {e}")
                continue

        # If we couldn't generate enough unique questions, fill with simpler ones
        while len(questions) < num_questions:
            question_data = await self._create_fallback_question(content, len(questions))
            
            q_id = f"q_{len(questions) + 1}"
            questions.append({
                "id": q_id,
                "question": question_data["question"],
                "options": question_data["options"],
            })
            
            session_data[q_id] = {
                "correct": question_data["correct_letter"],
                "justification": question_data["justification"],
                "explanation": question_data["explanation"]
            }

        self.active_quizzes[session_id] = session_data

        return {
            "session_id": session_id,
            "questions": questions,
        }

    def _extract_concepts(self, content: str) -> Dict[str, List[str]]:
        """Extract key concepts from document content."""
        concepts = {
            "technical_terms": [],
            "processes": [],
            "tools": [],
            "concepts": [],
            "methods": [],
            "features": [],
            "benefits": [],
            "challenges": []
        }
        
        # Technical terms patterns
        tech_patterns = [
            r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b',  # CamelCase terms
            r'\b(?:API|SDK|UI|UX|ML|AI|IoT|VR|AR|3D)\b',  # Acronyms
            r'\b\w+(?:\.js|\.py|\.java|\.cpp|\.go)\b',  # File extensions
            r'\b(?:React|Vue|Angular|Django|Flask|Spring|Laravel)\b'  # Frameworks
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts["technical_terms"].extend(matches)
        
        # Process-related terms
        process_patterns = [
            r'\b(?:development|implementation|deployment|testing|optimization|integration|migration)\b',
            r'\b(?:analysis|design|planning|execution|monitoring|evaluation)\b',
            r'\b(?:installation|configuration|setup|initialization|compilation)\b'
        ]
        
        for pattern in process_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts["processes"].extend(matches)
        
        # Extract sentences with key concepts
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
        for sentence in sentences[:50]:  # Limit to first 50 sentences
            if any(keyword in sentence.lower() for keyword in ['is', 'are', 'means', 'refers to', 'involves']):
                concepts["concepts"].append(sentence)
        
        # Clean and deduplicate
        for key in concepts:
            if key == "concepts":
                concepts[key] = concepts[key][:10]  # Limit concept sentences
            else:
                concepts[key] = list(set([
                    term.strip() for term in concepts[key] 
                    if len(term.strip()) > 2 and len(term.strip()) < 30
                ]))[:15]  # Limit other categories
        
        return concepts

    def _get_question_signature(self, question: str) -> str:
        """Create a signature for question uniqueness check."""
        # Remove common words and create signature
        words = question.lower().split()
        important_words = [w for w in words if w not in ['what', 'which', 'how', 'when', 'where', 'why', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']]
        return ' '.join(sorted(important_words))

    async def _create_contextual_question(self, content: str, concepts: Dict[str, List[str]], doc_id: str, question_index: int) -> Dict[str, Any]:
        """Create a contextual question with balanced options."""
        
        # Choose question type based on available concepts
        available_types = []
        if concepts["technical_terms"]:
            available_types.extend(["definition", "technical", "application"])
        if concepts["processes"]:
            available_types.extend(["process", "purpose"])
        if concepts["concepts"]:
            available_types.extend(["definition", "purpose", "application"])
        
        if not available_types:
            available_types = ["general"]
        
        question_type = random.choice(available_types)
        
        if question_type == "technical" and concepts["technical_terms"]:
            return await self._create_technical_question(content, concepts)
        elif question_type == "process" and concepts["processes"]:
            return await self._create_process_question(content, concepts)
        elif question_type == "definition" and (concepts["technical_terms"] or concepts["concepts"]):
            return await self._create_definition_question(content, concepts)
        elif question_type == "application" and concepts["technical_terms"]:
            return await self._create_application_question(content, concepts)
        else:
            return await self._create_general_question(content, concepts)

    async def _create_technical_question(self, content: str, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create a technical question with balanced options."""
        
        term = random.choice(concepts["technical_terms"])
        
        # Find context around the term
        context = self._find_context(content, term)
        if not context:
            raise ValueError("No context found for term")
        
        # Generate question
        templates = [
            f"Which technology is mentioned for handling {term.lower()}?",
            f"What is used to implement {term.lower()}?",
            f"How is {term.lower()} managed in the system?",
            f"What framework supports {term.lower()}?"
        ]
        
        question = random.choice(templates)
        
        # Extract answer from context
        answer = self._extract_answer_from_context(context, term)
        
        # Generate balanced distractors
        distractors = self._generate_balanced_distractors(answer, "technical")
        
        # Create options with similar lengths
        options = [answer] + distractors
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": f"Based on the document context: {context[:100]}...",
            "explanation": f"The document clearly mentions {answer} in relation to {term}."
        }

    async def _create_process_question(self, content: str, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create a process-oriented question."""
        
        process = random.choice(concepts["processes"])
        
        context = self._find_context(content, process)
        if not context:
            raise ValueError("No context found for process")
        
        templates = [
            f"What is the main approach for {process}?",
            f"How is {process} handled?",
            f"What method is used for {process}?",
            f"Which strategy is employed for {process}?"
        ]
        
        question = random.choice(templates)
        answer = self._extract_answer_from_context(context, process)
        distractors = self._generate_balanced_distractors(answer, "process")
        
        options = [answer] + distractors
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": f"The document describes this approach for {process}.",
            "explanation": f"Based on the content analysis, {answer} is the method used for {process}."
        }

    async def _create_definition_question(self, content: str, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create a definition question."""
        
        # Try to find a term with a clear definition
        term = None
        definition = None
        
        if concepts["concepts"]:
            concept_sentence = random.choice(concepts["concepts"])
            if ' is ' in concept_sentence or ' are ' in concept_sentence:
                parts = concept_sentence.split(' is ' if ' is ' in concept_sentence else ' are ')
                if len(parts) == 2:
                    term = parts[0].strip()
                    definition = parts[1].strip()
        
        if not term and concepts["technical_terms"]:
            term = random.choice(concepts["technical_terms"])
            context = self._find_context(content, term)
            if context:
                definition = self._extract_answer_from_context(context, term)
        
        if not term or not definition:
            raise ValueError("Could not create definition question")
        
        question = f"What is {term}?"
        
        # Generate contextual distractors
        distractors = self._generate_balanced_distractors(definition, "definition")
        
        options = [definition] + distractors
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == definition)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": f"The document defines {term} as {definition}.",
            "explanation": f"This definition is explicitly mentioned in the document."
        }

    async def _create_application_question(self, content: str, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create an application-based question."""
        
        term = random.choice(concepts["technical_terms"])
        context = self._find_context(content, term)
        
        if not context:
            raise ValueError("No context found for application question")
        
        templates = [
            f"When would you use {term}?",
            f"What is {term} primarily used for?",
            f"In which scenario is {term} most beneficial?",
            f"What is the main application of {term}?"
        ]
        
        question = random.choice(templates)
        answer = self._extract_answer_from_context(context, term)
        distractors = self._generate_balanced_distractors(answer, "application")
        
        options = [answer] + distractors
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": f"The document shows {term} is used for {answer}.",
            "explanation": f"Based on the context, {term} is applied in this scenario."
        }

    async def _create_general_question(self, content: str, concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create a general question using RAG."""
        
        # Generate a contextual query
        queries = [
            "What is the main topic discussed?",
            "What is the primary focus?",
            "What key concept is explained?",
            "What is the main subject?",
            "What does this document discuss?"
        ]
        
        query = random.choice(queries)
        
        # Get answer from RAG
        doc_id = list(self.documents.keys())[0]
        rag_response = await self.rag_service.answer_question(query, doc_id)
        answer = rag_response["answer"][:80]  # Limit length
        
        question = "What is the main focus of this document?"
        
        # Generate contextual distractors
        distractors = self._generate_balanced_distractors(answer, "general")
        
        options = [answer] + distractors
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": rag_response.get("justification", "Based on document analysis"),
            "explanation": "This answer represents the main theme of the document."
        }

    async def _create_fallback_question(self, content: str, question_index: int) -> Dict[str, Any]:
        """Create a simple fallback question."""
        
        # Extract first meaningful sentence
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
        if not sentences:
            sentences = [content[:100]]
        
        sentence = sentences[0]
        
        # Create simple question
        question = "What is mentioned in the document?"
        answer = sentence[:60] + "..." if len(sentence) > 60 else sentence
        
        # Simple distractors
        distractors = [
            "Database management and optimization strategies",
            "User interface design and development practices",
            "Security protocols and implementation methods"
        ]
        
        options = [answer] + distractors[:3]
        options = self._balance_option_lengths(options)
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": "This information is mentioned in the document.",
            "explanation": "This content is directly from the document."
        }

    def _find_context(self, content: str, term: str) -> str:
        """Find context around a term."""
        sentences = content.split('.')
        for sentence in sentences:
            if term.lower() in sentence.lower():
                return sentence.strip()
        return ""

    def _extract_answer_from_context(self, context: str, term: str) -> str:
        """Extract answer from context."""
        # Simple extraction - find the part that explains the term
        sentences = context.split('.')
        for sentence in sentences:
            if term.lower() in sentence.lower():
                # Extract the relevant part
                words = sentence.split()
                if len(words) > 5:
                    return ' '.join(words[:8]) + "..."
        return context[:50] + "..."

    def _generate_balanced_distractors(self, correct_answer: str, category: str) -> List[str]:
        """Generate contextually relevant distractors with similar lengths."""
        
        distractor_pools = {
            "technical": [
                "Database optimization and query processing",
                "User interface design and implementation",
                "Security protocols and authentication methods",
                "Performance monitoring and system analysis",
                "API development and integration services",
                "Machine learning algorithms and data processing",
                "Cloud infrastructure and deployment strategies"
            ],
            "process": [
                "Iterative development and continuous integration",
                "Agile methodology with sprint-based planning",
                "Waterfall approach with sequential phases",
                "DevOps practices and automated deployment",
                "Test-driven development and quality assurance",
                "Scrum framework with daily stand-ups"
            ],
            "definition": [
                "A systematic approach to problem-solving",
                "A framework for organizing and structuring data",
                "A method for optimizing system performance",
                "A protocol for secure communication",
                "A technique for improving user experience",
                "A strategy for managing complex workflows"
            ],
            "application": [
                "Building scalable web applications",
                "Implementing secure authentication systems",
                "Optimizing database query performance",
                "Developing responsive user interfaces",
                "Creating automated testing frameworks",
                "Managing distributed system architectures"
            ],
            "general": [
                "Software development methodologies and practices",
                "System architecture and design patterns",
                "Data management and analytics strategies",
                "User experience and interface optimization",
                "Performance monitoring and improvement techniques",
                "Security implementation and best practices"
            ]
        }
        
        pool = distractor_pools.get(category, distractor_pools["general"])
        
        # Filter distractors that are too similar to correct answer
        correct_words = set(correct_answer.lower().split())
        filtered_distractors = []
        
        for distractor in pool:
            distractor_words = set(distractor.lower().split())
            overlap = len(correct_words & distractor_words)
            if overlap < len(correct_words) * 0.5:  # Less than 50% word overlap
                filtered_distractors.append(distractor)
        
        return random.sample(filtered_distractors, min(3, len(filtered_distractors)))

    def _balance_option_lengths(self, options: List[str]) -> List[str]:
        """Balance option lengths to avoid obvious answers."""
        
        # Calculate target length (average of all options)
        total_length = sum(len(option) for option in options)
        target_length = total_length // len(options)
        
        balanced_options = []
        for option in options:
            if len(option) > target_length + 20:
                # Truncate long options
                balanced_options.append(option[:target_length + 10] + "...")
            elif len(option) < target_length - 20:
                # Pad short options with descriptive text
                balanced_options.append(option + " and related components")
            else:
                balanced_options.append(option)
        
        return balanced_options

    async def grade(self, session_id: str, answers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Evaluate submitted answers with detailed feedback."""
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
                "justification": meta["justification"],
                "explanation": meta["explanation"]
            })
        
        return results