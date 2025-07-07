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
    """Enhanced service for generating contextual, meaningful MCQ questions."""

    def __init__(self, rag_service: RAGService = None):
        self.rag_service = rag_service or RAGService()
        self.active_quizzes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.documents: Dict[str, str] = {}
        self.used_questions: Dict[str, set] = {}
        
        load_dotenv()

    async def register_document(self, document_id: str, content: str) -> None:
        """Cache document text for quiz generation."""
        self.documents[document_id] = content
        self.used_questions[document_id] = set()
        print(f"📌 Registered doc {document_id} for quiz generation")

    async def generate_questions(self, doc_id: str, num_questions: int = 3) -> Dict[str, Any]:
        """Generate meaningful, contextual MCQ questions from document content."""
        
        if doc_id not in self.documents:
            if not await self.rag_service.document_exists(doc_id):
                raise ValueError("Document not found")
            doc_data = self.rag_service.documents[doc_id]
            self.documents[doc_id] = doc_data["content"]
            self.used_questions[doc_id] = set()

        content = self.documents[doc_id]
        
        # Clean and prepare content
        cleaned_content = self._deep_clean_text(content)
        
        # Extract meaningful information
        key_facts = self._extract_key_facts(cleaned_content)
        concepts = self._extract_concepts(cleaned_content)
        
        session_id = str(uuid.uuid4())
        session_data: Dict[str, Dict[str, Any]] = {}
        questions: List[Dict[str, Any]] = []

        # Generate diverse questions with better RAG integration
        for i in range(num_questions):
            try:
                if i == 0:
                    # First question: Main topic/purpose using RAG
                    question_data = await self._create_main_topic_question_rag(doc_id, cleaned_content)
                elif i == 1:
                    # Second question: Technical detail using RAG
                    question_data = await self._create_technical_question_rag(doc_id, cleaned_content)
                else:
                    # Third question: Concept/process using RAG
                    question_data = await self._create_concept_question_rag(doc_id, cleaned_content)
                
                # Validate question quality
                if not self._is_valid_question(question_data):
                    question_data = await self._create_fallback_question(cleaned_content, i)
                
                q_id = f"q_{i + 1}"
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
                print(f"Error generating question {i+1}: {e}")
                # Create fallback question
                question_data = await self._create_fallback_question(cleaned_content, i)
                q_id = f"q_{i + 1}"
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

    def _deep_clean_text(self, text: str) -> str:
        """Deep clean text by removing ALL unwanted symbols and formatting."""
        # Remove common formatting symbols
        text = re.sub(r'[•▪▫◦‣⁃⚫⚪●○◆◇■□▲△▼▽]', '', text)
        text = re.sub(r'[→←↑↓↔↕⇒⇐⇑⇓]', '', text)
        text = re.sub(r'[※※※★☆✓✗✘❌✅]', '', text)
        text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', text)
        text = re.sub(r'[⊙⊚⊛⊜⊝⊞⊟⊠⊡]', '', text)
        text = re.sub(r'[◉◎⚬⚮⚯]', '', text)
        
        # Remove unwanted brackets and parentheses patterns
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # Remove list numbering patterns
        text = re.sub(r'^\s*\d+[\.\)]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[a-zA-Z][\.\)]\s*', '', text, flags=re.MULTILINE)
        
        # Remove dashes and formatting
        text = re.sub(r'\s*[-–—]\s*', ' ', text)
        text = re.sub(r'\s*[:|;]\s*', ': ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove casual/informal expressions
        casual_patterns = [
            r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bkya\b', r'\bkar\b', 
            r'\brahe\b', r'\bho\b', r'\bhain\b', r'\baur\b', r'\bbhai\b',
            r'\byaar\b', r'\bdost\b', r'\bkaise\b', r'\bkaisi\b', r'\bkyun\b',
            r'\bkab\b', r'\bkahan\b', r'\bkaun\b', r'\bkitna\b', r'\bkitni\b',
            r'\bacha\b', r'\baccha\b', r'\btheek\b', r'\bthik\b', r'\bsahi\b',
            r'\bgalat\b', r'\bnahi\b', r'\bnahin\b', r'\bhaan\b', r'\bha\b'
        ]
        
        for pattern in casual_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove short meaningless words
        text = re.sub(r'\b\w{1,2}\b', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _extract_key_facts(self, content: str) -> List[str]:
        """Extract key factual information from content."""
        facts = []
        
        # Split into meaningful sentences
        sentences = []
        for sentence in content.split('.'):
            sentence = sentence.strip()
            if (len(sentence) > 40 and 
                len(sentence) < 300 and 
                self._has_meaningful_content(sentence)):
                sentences.append(sentence)
        
        # Look for technical/factual sentences
        fact_indicators = [
            r'(?:system|application|project|software|platform)\s+(?:is|uses|implements|provides|supports|features)',
            r'(?:developed|built|created|designed|implemented)\s+(?:using|with|in|for)',
            r'(?:technology|framework|language|database|tool)\s+(?:used|employed|utilized)',
            r'(?:includes|contains|provides|offers|supports)\s+(?:features|functionality|capabilities)',
            r'(?:based\s+on|powered\s+by|utilizing|leveraging)\s+[\w\s]+',
            r'(?:architecture|design|structure|implementation)\s+(?:follows|uses|incorporates)'
        ]
        
        for sentence in sentences:
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in fact_indicators):
                clean_sentence = self._clean_sentence(sentence)
                if clean_sentence and len(clean_sentence) > 50:
                    facts.append(clean_sentence)
        
        return facts[:6]

    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts and processes from content."""
        concepts = []
        
        # Technical terms
        tech_patterns = [
            r'\b(?:React|Vue|Angular|Node|Express|Django|Flask|FastAPI|Spring|Laravel)\b',
            r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+|C#|PHP|Ruby|Go|Rust|Swift)\b',
            r'\b(?:MongoDB|MySQL|PostgreSQL|Redis|Firebase|SQLite|Oracle|MariaDB)\b',
            r'\b(?:Docker|Kubernetes|AWS|Azure|GCP|Heroku|Vercel|Netlify)\b',
            r'\b(?:HTML|CSS|Bootstrap|Tailwind|SCSS|SASS|Material-UI|Chakra)\b',
            r'\b(?:Machine Learning|AI|Deep Learning|Neural Network|TensorFlow|PyTorch)\b',
            r'\b(?:REST|GraphQL|gRPC|WebSocket|HTTP|HTTPS|JSON|XML)\b',
            r'\b(?:Git|GitHub|GitLab|Jenkins|CI/CD|DevOps|Agile|Scrum)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend(matches)
        
        # Remove duplicates
        unique_concepts = list(set([c.strip() for c in concepts if len(c.strip()) > 2]))
        return unique_concepts[:10]

    def _has_meaningful_content(self, text: str) -> bool:
        """Check if text has meaningful technical/professional content."""
        meaningful_indicators = [
            r'\b(?:system|application|software|platform|project|development|implementation)\b',
            r'\b(?:technology|framework|language|database|API|interface|architecture)\b',
            r'\b(?:user|client|server|data|process|method|function|feature)\b',
            r'\b(?:analysis|design|testing|deployment|maintenance|optimization)\b',
            r'\b(?:requirements|specifications|documentation|solution|approach)\b'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in meaningful_indicators)

    def _clean_sentence(self, sentence: str) -> str:
        """Clean a sentence for use in questions/answers."""
        # Remove formatting symbols
        sentence = re.sub(r'[•▪▫◦‣⁃→←↑↓⚫⚪●○◆◇■□▲△▼▽]', '', sentence)
        sentence = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence)
        sentence = sentence.strip()
        
        # Remove leading numbers or bullets
        sentence = re.sub(r'^[\d\.\)\-\s•▪▫◦‣⁃]+', '', sentence)
        
        # Ensure proper capitalization
        if sentence and len(sentence) > 5:
            sentence = sentence[0].upper() + sentence[1:]
        
        return sentence

    def _is_valid_question(self, question_data: Dict[str, Any]) -> bool:
        """Validate if a question is appropriate and meaningful."""
        if not question_data:
            return False
        
        question = question_data.get("question", "")
        options = question_data.get("options", {})
        
        # Check if question is meaningful
        if len(question) < 20 or not question.endswith("?"):
            return False
        
        # Check if options are valid
        if len(options) != 4:
            return False
        
        # Check if options are not casual/inappropriate
        for option in options.values():
            if (len(option) < 10 or 
                any(word in option.lower() for word in ['main ready hun', 'help karne', 'kya', 'kar', 'ho']) or
                option.startswith('!') or
                not self._has_meaningful_content(option)):
                return False
        
        return True

    async def _create_main_topic_question_rag(self, doc_id: str, content: str) -> Dict[str, Any]:
        """Create main topic question using RAG."""
        try:
            # Use RAG to get main purpose
            rag_response = await self.rag_service.answer_question(
                "What is the main purpose or objective of this project?", doc_id
            )
            
            main_answer = rag_response["answer"]
            
            # Clean and validate answer
            if (len(main_answer) < 30 or 
                any(word in main_answer.lower() for word in ['main ready hun', 'help karne', 'document upload'])):
                # Fallback to content extraction
                main_answer = self._extract_purpose_from_content(content)
            
            question = "What is the main purpose or objective of this project?"
            
            # Generate realistic distractors
            distractors = [
                "Creating a mobile application for social media engagement",
                "Developing a game application for entertainment purposes", 
                "Building a simple website for personal blogging",
                "Designing a basic calculator for mathematical operations"
            ]
            
            # Ensure answer is different from distractors
            distractors = [d for d in distractors if not self._answers_similar(main_answer, d)]
            
            options = [main_answer] + distractors[:3]
            random.shuffle(options)
            
            letters = ["A", "B", "C", "D"]
            options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
            correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == main_answer)
            
            return {
                "question": question,
                "options": options_dict,
                "correct_letter": correct_letter,
                "justification": "Based on the document's main content and stated objectives",
                "explanation": "This represents the primary purpose described in the document"
            }
            
        except Exception as e:
            print(f"Error in main topic question: {e}")
            return await self._create_fallback_question(content, 0)

    async def _create_technical_question_rag(self, doc_id: str, content: str) -> Dict[str, Any]:
        """Create technical question using RAG."""
        try:
            # Use RAG to get technical details
            rag_response = await self.rag_service.answer_question(
                "What technologies, frameworks, or tools are used in this project?", doc_id
            )
            
            tech_answer = rag_response["answer"]
            
            # Validate answer
            if (len(tech_answer) < 20 or 
                any(word in tech_answer.lower() for word in ['main ready hun', 'help karne', 'document upload'])):
                # Fallback to content extraction
                tech_answer = self._extract_technologies_from_content(content)
            
            question = "What technologies or frameworks are primarily used in this project?"
            
            # Generate realistic technical distractors
            distractors = [
                "React.js with Node.js and MongoDB database",
                "Angular framework with .NET Core and SQL Server",
                "Vue.js with Express.js and PostgreSQL",
                "Django with Python and MySQL database",
                "Flutter with Firebase backend services",
                "Laravel PHP with MariaDB database"
            ]
            
            # Filter similar distractors
            distractors = [d for d in distractors if not self._answers_similar(tech_answer, d)]
            
            options = [tech_answer] + distractors[:3]
            random.shuffle(options)
            
            letters = ["A", "B", "C", "D"]
            options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
            correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == tech_answer)
            
            return {
                "question": question,
                "options": options_dict,
                "correct_letter": correct_letter,
                "justification": "Based on the technical specifications mentioned in the document",
                "explanation": "These technologies are specifically mentioned in the project documentation"
            }
            
        except Exception as e:
            print(f"Error in technical question: {e}")
            return await self._create_fallback_question(content, 1)

    async def _create_concept_question_rag(self, doc_id: str, content: str) -> Dict[str, Any]:
        """Create concept question using RAG."""
        try:
            # Use RAG to get methodology
            rag_response = await self.rag_service.answer_question(
                "What development methodology or approach is used in this project?", doc_id
            )
            
            method_answer = rag_response["answer"]
            
            # Validate answer
            if (len(method_answer) < 20 or 
                any(word in method_answer.lower() for word in ['main ready hun', 'help karne', 'document upload'])):
                # Fallback to content extraction
                method_answer = self._extract_methodology_from_content(content)
            
            question = "What development methodology or approach is described in this project?"
            
            # Generate realistic methodology distractors
            distractors = [
                "Agile development with iterative sprint cycles",
                "Waterfall methodology with sequential phases",
                "DevOps practices with continuous integration",
                "Scrum framework with daily standups",
                "Lean development with minimum viable product",
                "Kanban methodology with continuous flow"
            ]
            
            # Filter similar distractors
            distractors = [d for d in distractors if not self._answers_similar(method_answer, d)]
            
            options = [method_answer] + distractors[:3]
            random.shuffle(options)
            
            letters = ["A", "B", "C", "D"]
            options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
            correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == method_answer)
            
            return {
                "question": question,
                "options": options_dict,
                "correct_letter": correct_letter,
                "justification": "Based on the methodology described in the document",
                "explanation": "This approach is mentioned in the project documentation"
            }
            
        except Exception as e:
            print(f"Error in concept question: {e}")
            return await self._create_fallback_question(content, 2)

    def _extract_purpose_from_content(self, content: str) -> str:
        """Extract project purpose from content."""
        purpose_keywords = ['purpose', 'objective', 'goal', 'aim', 'project', 'system', 'application']
        sentences = content.split('.')
        
        for sentence in sentences:
            if (any(keyword in sentence.lower() for keyword in purpose_keywords) and 
                len(sentence.strip()) > 30 and 
                self._has_meaningful_content(sentence)):
                return self._clean_sentence(sentence)
        
        return "Comprehensive system development with modern technology implementation"

    def _extract_technologies_from_content(self, content: str) -> str:
        """Extract technologies from content."""
        tech_patterns = [
            r'\b(?:React|Vue|Angular|Node|Express|Django|Flask|Python|JavaScript|HTML|CSS|MongoDB|MySQL)\b'
        ]
        
        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            technologies.extend(matches)
        
        if technologies:
            unique_techs = list(set(technologies))
            if len(unique_techs) >= 2:
                return f"{unique_techs[0]} with {unique_techs[1]} implementation"
            else:
                return f"{unique_techs[0]} framework with modern development stack"
        
        return "Modern web development technologies with responsive design"

    def _extract_methodology_from_content(self, content: str) -> str:
        """Extract methodology from content."""
        method_keywords = ['agile', 'scrum', 'waterfall', 'methodology', 'approach', 'process', 'framework']
        sentences = content.split('.')
        
        for sentence in sentences:
            if (any(keyword in sentence.lower() for keyword in method_keywords) and 
                len(sentence.strip()) > 20):
                return self._clean_sentence(sentence)
        
        return "Systematic development approach with structured implementation"

    def _answers_similar(self, answer1: str, answer2: str) -> bool:
        """Check if two answers are too similar."""
        if not answer1 or not answer2:
            return False
        
        words1 = set(answer1.lower().split())
        words2 = set(answer2.lower().split())
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        similarity = overlap / total if total > 0 else 0
        return similarity > 0.4  # More than 40% similarity

    async def _create_fallback_question(self, content: str, question_index: int) -> Dict[str, Any]:
        """Create a professional fallback question."""
        
        fallback_questions = [
            "What is the primary focus of this project?",
            "What type of system is being developed?",
            "What is the main goal of this project?"
        ]
        
        question = fallback_questions[question_index % len(fallback_questions)]
        
        # Create generic but professional answers
        fallback_answers = [
            "Web application development with modern frameworks",
            "Mobile application with user-friendly interface",
            "Database management system with efficient queries",
            "Cloud-based solution for business operations"
        ]
        
        # Select one as correct based on content
        correct_answer = fallback_answers[0]  # Default
        
        # Try to make it more specific based on content
        if any(term in content.lower() for term in ['web', 'website', 'html', 'css', 'javascript']):
            correct_answer = "Web application development with modern frameworks"
        elif any(term in content.lower() for term in ['mobile', 'app', 'android', 'ios']):
            correct_answer = "Mobile application with user-friendly interface"
        elif any(term in content.lower() for term in ['database', 'sql', 'mongodb', 'mysql']):
            correct_answer = "Database management system with efficient queries"
        elif any(term in content.lower() for term in ['cloud', 'aws', 'azure', 'server']):
            correct_answer = "Cloud-based solution for business operations"
        
        # Remove correct answer from distractors
        distractors = [ans for ans in fallback_answers if ans != correct_answer]
        
        options = [correct_answer] + distractors[:3]
        random.shuffle(options)
        
        letters = ["A", "B", "C", "D"]
        options_dict = {ltr: opt for ltr, opt in zip(letters, options)}
        correct_letter = next(ltr for ltr, opt in options_dict.items() if opt == correct_answer)
        
        return {
            "question": question,
            "options": options_dict,
            "correct_letter": correct_letter,
            "justification": "Based on the overall project description and context",
            "explanation": "This information is derived from the document's main content"
        }

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