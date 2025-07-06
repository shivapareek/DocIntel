import os, uuid, json, re
from typing import Dict, Any, List, Optional
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from services.summary import generate_summary as _gen_sum
from pathlib import Path
import requests
import random

load_dotenv()

class RAGService:
    _SPECIAL_FIELD_PATTERNS: Dict[str, List[str]] = {
        "project name": [r"project\\s*(?:name|title)\\s*[:\\-–]?\\s*([\\w\\s\\-:]+)"],
        "project title": [r"project\\s*(?:name|title)\\s*[:\\-–]?\\s*([\\w\\s\\-:]+)"],
        "deadline": [r"(?:deadline|due\\s*date|submission\\s*date)\\s*[:\\-–]?\\s*([\\w\\s,]+)"],
        "submission date": [r"submission\\s*date\\s*[:\\-–]?\\s*([\\w\\s,]+)"],
        "author": [r"(?:author|written\\s*by)\\s*[:\\-–]?\\s*([\\w\\s\\.]+)"],
        "guide name": [r"(?:guide|supervisor|mentor|advisor)\\s*[:\\-–]?\\s*([\\w\\s\\.]+)"]
    }

    def __init__(self):
        self.persist_directory = "./store"
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100, length_function=len
        )

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.documents: Dict[str, Any] = {}
        self._load_documents()

        # Enhanced basic responses
        self.basic_responses: Dict[str, List[str]] = {
            "hello": [
                "Hello! Main aapka document assistant hun. Kya help chahiye?",
                "Hi there! Document analysis ya general questions, dono kar sakta hun!",
                "Namaste! PDF upload karo ya fir general chat karte hain!"
            ],
            "hi": [
                "Hi! Kya puchna chahte ho?",
                "Hello! Main ready hun help karne ke liye.",
                "Hey! Document ke bare mein kuch bhi pucho!"
            ],
            "namaste": [
                "Namaste! Main aapka AI assistant hun. Document analysis kar sakta hun!",
                "Namaste ji! PDF upload karo ya general questions pucho.",
                "Namaste! Kya help chahiye aaj?"
            ],
            "how are you": [
                "Main bilkul theek hun! Ready hun documents analyze karne ke liye!",
                "Great! Aap kaise ho? Kya kaam hai aaj?",
                "Awesome! Document upload karo ya general chat karte hain!"
            ],
            "what can you do": [
                "Main PDFs analyze kar sakta hun, technologies extract kar sakta hun, summaries bana sakta hun!",
                "Document analysis, Q&A, technology extraction, project details - sab kuch!",
                "PDF upload karo to main detailed analysis karunga - technologies, methodologies, key points sab!"
            ],
            "thanks": [
                "Welcome! Aur kuch help chahiye?",
                "No problem! Koi aur question?",
                "Khushi hui help karke! Document analysis ke liye ready hun!"
            ],
            "bye": [
                "Bye! Wapas aana jab document analyze karna ho!",
                "Goodbye! Take care!",
                "Alvida! Documents ke saath wapas aana!"
            ]
        }

    def _load_documents(self):
        try:
            for fn in os.listdir(self.persist_directory):
                if fn.endswith(".json"):
                    with open(os.path.join(self.persist_directory, fn), encoding="utf-8") as f:
                        self.documents[fn[:-5]] = json.load(f)
                    print(f"📂 Loaded {fn}")
        except Exception as exc:
            print(f"Error loading documents: {exc}")

    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology names from text using patterns"""
        # Common technology patterns
        tech_patterns = [
            r'\b(?:React(?:\.js)?|Vue(?:\.js)?|Angular|Node(?:\.js)?|Express(?:\.js)?)\b',
            r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+|C#|PHP|Ruby|Go|Rust)\b',
            r'\b(?:HTML|CSS|SCSS|SASS|Bootstrap|Tailwind)\b',
            r'\b(?:MongoDB|MySQL|PostgreSQL|Redis|SQLite|Firebase)\b',
            r'\b(?:Docker|Kubernetes|AWS|Azure|GCP|Heroku|Vercel)\b',
            r'\b(?:Git|GitHub|GitLab|Jenkins|CI/CD)\b',
            r'\b(?:FastAPI|Django|Flask|Spring|Laravel|Rails)\b',
            r'\b(?:TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy)\b'
        ]
        
        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.extend(matches)
        
        return list(set(technologies))  # Remove duplicates

    def _extract_key_info_from_text(self, text: str, question: str) -> str:
        """Extract key information based on question type"""
        question_lower = question.lower()
        
        # Technology-related questions
        if any(word in question_lower for word in ['technology', 'technologies', 'tech', 'stack', 'tools']):
            technologies = self._extract_technologies_from_text(text)
            if technologies:
                return f"Document mein ye technologies mention hain: {', '.join(technologies)}"
        
        # Methodology questions
        if any(word in question_lower for word in ['methodology', 'approach', 'method', 'process']):
            method_keywords = ['agile', 'scrum', 'waterfall', 'methodology', 'approach', 'process', 'framework']
            sentences = text.split('.')
            relevant_sentences = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in method_keywords):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return ". ".join(relevant_sentences[:3])
        
        # Objective/Purpose questions
        if any(word in question_lower for word in ['objective', 'purpose', 'goal', 'aim']):
            obj_keywords = ['objective', 'purpose', 'goal', 'aim', 'target', 'intention']
            sentences = text.split('.')
            relevant_sentences = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in obj_keywords):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return ". ".join(relevant_sentences[:2])
        
        return ""

    def _generate_smart_response(self, question: str, context: str) -> str:
        """Generate intelligent response based on context and question"""
        question_lower = question.lower()
        
        # Extract key information first
        key_info = self._extract_key_info_from_text(context, question)
        if key_info:
            return key_info
        
        # Keyword-based intelligent matching
        context_sentences = [s.strip() for s in context.split('.') if s.strip()]
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        
        # Score sentences based on keyword overlap
        scored_sentences = []
        for sentence in context_sentences:
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            score = len(question_words.intersection(sentence_words))
            
            # Boost score for important keywords
            important_keywords = ['technology', 'project', 'system', 'development', 'implementation', 'result', 'conclusion']
            for keyword in important_keywords:
                if keyword in sentence.lower():
                    score += 2
            
            if score > 0:
                scored_sentences.append((sentence, score))
        
        # Sort by score and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if scored_sentences:
            top_sentences = [s[0] for s in scored_sentences[:3]]
            return ". ".join(top_sentences)
        
        return "Is question ka specific answer document mein nahi mil raha. Koi aur question try karo!"
    
    # ...existing code...

    def _get_smart_ai_response(self, prompt: str, context: str = "", question: str = "") -> str:
        token = os.getenv("HUGGINGFACE_API_KEY", "")
        if not token:
            return self._generate_smart_response(question, context)

        # Use a QA-specific model
        model = "deepset/roberta-base-squad2"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            payload = {
                "inputs": {
                    "question": question,
                    "context": context
                }
            }
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json=payload,
                timeout=20,
            )
            if r.status_code == 200:
                result = r.json()
                answer = result.get("answer", "")
                # Sometimes model returns empty string if not found
                if answer and answer.strip() and answer.strip().lower() != "empty":
                    return answer.strip()
        except Exception as e:
            print(f"HF QA model error: {e}")

        # Fallback to local
        return self._generate_smart_response(question, context)


   


    def _is_basic_chat(self, question: str) -> bool:
        """Check if the question is basic conversation"""
        basic_patterns = [
            "hello", "hi", "namaste", "how are you", "what's up", "hey",
            "thanks", "thank you", "bye", "goodbye", "what can you do",
            "who are you", "what are you", "how do you work", "kya haal hai",
            "kaise ho", "dhanyawad", "shukriya"
        ]
        question_lower = question.lower().strip()
        return any(pattern in question_lower for pattern in basic_patterns)

    def _generate_local_response(self, question: str) -> str:
        """Enhanced local response generation"""
        question_lower = question.lower()
        
        # Check for basic greetings and responses
        for pattern, responses in self.basic_responses.items():
            if pattern in question_lower:
                return random.choice(responses)
        
        # Hindi greetings
        if any(word in question_lower for word in ['kaise ho', 'kya haal', 'kaise hain']):
            return random.choice([
                "Main bilkul theek hun! Aap kaise ho? Document analysis ya general chat?",
                "Sab badhiya! Kya help chahiye aaj?",
                "Great! Ready hun help karne ke liye!"
            ])
        
        # Question patterns
        if any(word in question_lower for word in ['what', 'how', 'why', 'when', 'where', 'who', 'kya', 'kaise', 'kyun', 'kab', 'kahan', 'kaun']):
            return random.choice([
                "Interesting question! Document upload karo to main detailed analysis kar sakta hun!",
                "Good question! PDF upload karo to specific answers de sakta hun!",
                "Main help kar sakta hun! Document analysis ke liye file upload karo!"
            ])
        
        # Default response
        return random.choice([
            "Main samjha nahi. Document upload karo ya basic questions pucho!",
            "Kya chahiye? PDF analysis ya general chat?",
            "Document upload karo ya simple questions pucho - main ready hun!"
        ])

    async def process_document(self, content: str, filename: str) -> str:
        doc_id = str(uuid.uuid4())
        chunks = self.text_splitter.split_text(content)
        collection_name = f"doc_{doc_id.replace('-', '_')}"

        try:
            col = self.client.create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )

            # Batch embed (fast)
            embeddings = self.embeddings.embed_documents(chunks)
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            metas = [{"chunk_id": i, "doc_id": doc_id} for i in range(len(chunks))]

            col.add(embeddings=embeddings, documents=chunks, metadatas=metas, ids=ids)

            self.documents[doc_id] = {
                "filename": filename,
                "content": content,
                "chunks": len(chunks),
                "collection_name": collection_name,
            }
            with open(
                os.path.join(self.persist_directory, f"{doc_id}.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(self.documents[doc_id], f)
            return doc_id
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    async def generate_summary(self, doc_id: str) -> str:
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            raise Exception("Document not found")
        return _gen_sum(self.documents[doc_id]["content"])

    async def answer_question(
        self,
        question: str,
        doc_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        try:
            if self._is_basic_chat(question):
                answer = self._generate_local_response(question)
                return {
                    "answer": answer,
                    "justification": "Basic conversation response",
                    "source_snippets": [],
                    "confidence": 0.9,
                }

            doc_id = doc_id.strip()
            if doc_id and doc_id not in self.documents:
                return {
                    "answer": "Document nahi mila! Pehle upload karo phir questions pucho.",
                    "justification": "Document not found",
                    "source_snippets": [],
                    "confidence": 0.1,
                }

            if not doc_id or doc_id not in self.documents:
                doc_related_keywords = ['document', 'pdf', 'file', 'content', 'text', 'project', 'internship', 'technologies', 'methodology']
                if any(word in question.lower() for word in doc_related_keywords):
                    return {
                        "answer": "Pehle document upload karo, phir main detailed analysis kar sakta hun!",
                        "justification": "No document available for analysis",
                        "source_snippets": [],
                        "confidence": 0.1,
                    }
                else:
                    answer = self._generate_local_response(question)
                    return {
                        "answer": answer,
                        "justification": "General conversation response",
                        "source_snippets": [],
                        "confidence": 0.7,
                    }

            col = self.client.get_collection(self.documents[doc_id]["collection_name"])
            results = col.query(
                query_embeddings=[self.embeddings.embed_query(question)],
                n_results=8,
            )

            if not results["documents"][0]:
                return {
                    "answer": "Document mein is question ka answer nahi mil raha. Koi aur question try karo!",
                    "justification": "No relevant passages found",
                    "source_snippets": [],
                    "confidence": 0.1,
                }

            context = "\n".join(results["documents"][0])
            answer = self._get_smart_ai_response(
                prompt="",  # not needed for QA model
                context=context,
                question=question
            )

            # ✅ Add fallback to HuggingFace if local answer weak
            if not answer or len(answer.strip()) < 30:
                prompt = (
                    "Context:\n" + context + "\n\n"
                    "Question: " + question + "\n"
                    "Answer:"
                )
                from_path = Path(__file__).resolve().parent.parent / ".env"
                load_dotenv(dotenv_path=from_path)
                hf_key = os.getenv("HUGGINGFACE_API_KEY", "")
                if hf_key:
                    try:
                        hf_headers = {"Authorization": f"Bearer {hf_key}"}
                        hf_response = requests.post(
                            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                            headers=hf_headers,
                            json={"inputs": prompt, "parameters": {"max_new_tokens": 200}},
                            timeout=15
                        )
                        if hf_response.status_code == 200:
                            data = hf_response.json()
                            generated = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
                            if generated and len(generated.strip()) > 20:
                                answer = generated.replace(prompt, "").strip()
                    except Exception as e:
                        print("HF fallback error:", e)

            if not answer or len(answer.strip()) < 20:
                answer = "Document mein ye information hai lekin specific answer extract nahi kar paya. Manual check karo!"

            return {
                "answer": answer,
                "justification": f"Document analysis se {len(results['documents'][0])} relevant sections mile",
                "source_snippets": results["documents"][0][:3],
                "confidence": 0.85,
            }

        except Exception as e:
            print(f"Error in answer_question: {e}")
            return {
                "answer": "Sorry, kuch technical issue hai. Phir try karo!",
                "justification": "System error occurred",
                "source_snippets": [],
                "confidence": 0.0,
            }


    async def search_document(self, query: str, doc_id: str, top_k: int = 5):
        try:
            doc_id = doc_id.strip()
            if doc_id not in self.documents:
                return []
            
            col = self.client.get_collection(self.documents[doc_id]["collection_name"])
            res = col.query(
                query_embeddings=[self.embeddings.embed_query(query)], n_results=top_k
            )
            
            return [
                {
                    "chunk_id": m["chunk_id"],
                    "content": d,
                    "relevance_score": 1.0 - (i * 0.1),
                }
                for i, (d, m) in enumerate(zip(res["documents"][0], res["metadatas"][0]))
            ]
        except Exception as e:
            print(f"Error in search_document: {e}")
            return []

    async def document_exists(self, doc_id: str) -> bool:
        if not doc_id:
            return False
        return doc_id.strip() in self.documents

    async def delete_document(self, doc_id: str) -> bool:
        try:
            doc_id = doc_id.strip()
            if doc_id not in self.documents:
                return False
            
            self.client.delete_collection(self.documents[doc_id]["collection_name"])
            del self.documents[doc_id]
            json_path = os.path.join(self.persist_directory, f"{doc_id}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    async def list_documents(self):
        return [
            {"id": did, "filename": m["filename"], "chunks": m["chunks"]}
            for did, m in self.documents.items()
        ]

    async def get_document_context(self, doc_id: str):
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            raise Exception("Document not found")
        
        meta = self.documents[doc_id]
        c = meta["content"]
        
        # Extract technologies from document
        technologies = self._extract_technologies_from_text(c)
        
        return {
            "filename": meta["filename"],
            "word_count": len(c.split()),
            "character_count": len(c),
            "chunks": meta["chunks"],
            "technologies": technologies,
            "preview": c[:500] + "..." if len(c) > 500 else c,
        }

    async def suggest_clarifications(self, question: str, doc_id: str):
        if doc_id.strip() not in self.documents:
            return [
                "Document upload karo pehle analysis ke liye!",
                "Kya specific information chahiye?",
                "Try: 'Document ka summary do' ya 'Technologies kya hain?'"
            ]
        
        # Get document context for better suggestions
        doc_meta = self.documents[doc_id.strip()]
        technologies = self._extract_technologies_from_text(doc_meta["content"])
        
        suggestions = [
            f"'{question}' ke bare mein aur detail chahiye?",
            f"Document mein '{question}' ke alawa kya aur hai?",
            "Main technologies kya hain is document mein?",
        ]
        
        if technologies:
            suggestions.append(f"Ye technologies mention hain: {', '.join(technologies[:3])}. Inke bare mein pucho!")
        
        return suggestions

    async def register_document(self, doc_id: str, content: str):
        if doc_id not in self.documents:
            chunks = self.text_splitter.split_text(content)
            self.documents[doc_id] = {
                "filename": f"{doc_id}.pdf",
                "content": content,
                "chunks": len(chunks),
                "collection_name": f"doc_{doc_id.replace('-', '_')}",
            }

            