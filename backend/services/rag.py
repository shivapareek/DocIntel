import os
import uuid
import json
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        self.persist_directory = "./store"
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.llm = self._initialize_llm()
        self.documents = {}
        self._load_documents()

        self.qa_prompt = PromptTemplate(
            template="""Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Always provide a justification for your answer based on the context.

Context: {context}

Question: {question}

Please provide:
1. A clear answer
2. Justification with specific reference to the context
3. Confidence level (0-1)

Answer:""",
            input_variables=["context", "question"]
        )

    def _initialize_llm(self):
        try:
            if os.getenv("OPENAI_API_KEY"):
                return ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature=0.1,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
        except Exception:
            pass
        try:
            if os.getenv("GROQ_API_KEY"):
                from groq import Groq
                return Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception:
            pass
        return None

    def _load_documents(self):
        for file in os.listdir(self.persist_directory):
            if file.endswith(".json"):
                with open(os.path.join(self.persist_directory, file), "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                    doc_id = file.replace(".json", "")
                    self.documents[doc_id] = doc_data
                    print(f"📂 Loaded document metadata: {doc_id}")

    async def document_exists(self, doc_id: str) -> bool:
        doc_id = doc_id.strip()  # ✅ Clean input
        print(f"🔍 Checking doc_id: {doc_id}")
        print(f"📄 Available docs: {list(self.documents.keys())}")

        if doc_id in self.documents:
            return True

        # ✅ Optional fallback: try matching collection_name
        for meta in self.documents.values():
            if meta.get("collection_name", "").endswith(doc_id.replace("-", "_")):
                return True

        return False

    async def process_document(self, content: str, filename: str) -> str:
        try:
            doc_id = str(uuid.uuid4())
            chunks = self.text_splitter.split_text(content)
            collection_name = f"doc_{doc_id.replace('-', '_')}"
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            for i, chunk in enumerate(chunks):
                embedding = self.embeddings.embed_query(chunk)
                collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{"chunk_id": i, "doc_id": doc_id}],
                    ids=[f"{doc_id}_{i}"]
                )

            self.documents[doc_id] = {
                "filename": filename,
                "content": content,
                "chunks": len(chunks),
                "collection_name": collection_name
            }

            with open(os.path.join(self.persist_directory, f"{doc_id}.json"), "w", encoding="utf-8") as f:
                json.dump(self.documents[doc_id], f)

            return doc_id

        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    async def answer_question(self, question: str, doc_id: str,
                              conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            doc_id = doc_id.strip()  # ✅ Consistency
            if doc_id not in self.documents:
                raise Exception("Document not found")

            collection_name = self.documents[doc_id]["collection_name"]
            collection = self.client.get_collection(collection_name)

            query_embedding = self.embeddings.embed_query(question)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )

            context = "\n\n".join(results["documents"][0])

            if self.llm:
                conv_context = ""
                if conversation_history:
                    for turn in conversation_history[-3:]:
                        conv_context += f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}\n\n"

                full_prompt = f"""Based on the following document context, answer the question.

Previous conversation:
{conv_context}

Document context:
{context}

Current question: {question}

Please provide a clear answer with justification."""

                if hasattr(self.llm, 'predict'):
                    answer = self.llm.predict(full_prompt)
                else:
                    answer = self._generate_basic_answer(question, context)
            else:
                answer = self._generate_basic_answer(question, context)

            return {
                "answer": answer,
                "justification": f"Based on {len(results['documents'][0])} relevant passages from the document",
                "source_snippets": results["documents"][0][:3],
                "confidence": 0.8
            }

        except Exception as e:
            return {
                "answer": f"Error answering question: {str(e)}",
                "justification": "System error occurred",
                "source_snippets": [],
                "confidence": 0.0
            }

    def _generate_basic_answer(self, question: str, context: str) -> str:
        question_lower = question.lower()
        context_lower = context.lower()

        sentences = context.split('.')
        relevant_sentences = []

        question_words = set(question_lower.split())

        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if len(question_words.intersection(sentence_words)) > 0:
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            return '. '.join(relevant_sentences[:3]) + '.'
        else:
            return "I couldn't find a specific answer to your question in the document."

    async def generate_summary(self, doc_id: str, max_words: int = 150) -> str:
        try:
            doc_id = doc_id.strip()
            if doc_id not in self.documents:
                raise Exception("Document not found")

            content = self.documents[doc_id]["content"]

            if self.llm:
                prompt = f"""Summarize the following document in exactly {max_words} words or less. 
Focus on the main points and key information:

{content[:3000]}

Summary:"""

                if hasattr(self.llm, 'predict'):
                    summary = self.llm.predict(prompt)
                else:
                    summary = self._generate_basic_summary(content, max_words)
            else:
                summary = self._generate_basic_summary(content, max_words)

            return summary.strip()

        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def _generate_basic_summary(self, content: str, max_words: int) -> str:
        sentences = content.split('. ')
        summary_sentences = []
        word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_words:
                summary_sentences.append(sentence)
                word_count += sentence_words
            else:
                break

        return '. '.join(summary_sentences) + '.'

    async def delete_document(self, doc_id: str) -> bool:
        try:
            doc_id = doc_id.strip()
            if doc_id not in self.documents:
                return False

            collection_name = self.documents[doc_id]["collection_name"]
            self.client.delete_collection(collection_name)
            del self.documents[doc_id]

            json_path = os.path.join(self.persist_directory, f"{doc_id}.json")
            if os.path.exists(json_path):
                os.remove(json_path)

            return True
        except Exception:
            return False

    async def list_documents(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": doc_id,
                "filename": doc_data["filename"],
                "chunks": doc_data["chunks"]
            }
            for doc_id, doc_data in self.documents.items()
        ]

    async def suggest_clarifications(self, question: str, doc_id: str) -> List[str]:
        if doc_id.strip() not in self.documents:
            return []

        clarifications = [
            f"Could you be more specific about '{question}'?",
            f"Are you asking about a particular aspect of '{question}'?",
            f"Would you like me to explain '{question}' in more detail?"
        ]
        return clarifications[:3]

    async def get_document_context(self, doc_id: str) -> Dict[str, Any]:
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            raise Exception("Document not found")

        doc_data = self.documents[doc_id]
        content = doc_data["content"]

        return {
            "filename": doc_data["filename"],
            "word_count": len(content.split()),
            "character_count": len(content),
            "chunks": doc_data["chunks"],
            "preview": content[:500] + "..." if len(content) > 500 else content
        }

    async def search_document(self, query: str, doc_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            return []

        try:
            collection_name = self.documents[doc_id]["collection_name"]
            collection = self.client.get_collection(collection_name)

            query_embedding = self.embeddings.embed_query(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            search_results = []
            for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                search_results.append({
                    "chunk_id": metadata["chunk_id"],
                    "content": doc,
                    "relevance_score": 1.0 - (i * 0.1)
                })

            return search_results

        except Exception as e:
            return []
