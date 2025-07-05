import os, uuid, json
from typing import Dict, Any, List, Optional


import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from services.summary import generate_summary as _gen_sum

load_dotenv()


class RAGService:
    def __init__(self):
        # ── paths & helpers
        self.persist_directory = "./store"
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.llm = self._initialize_llm()

        self.documents: Dict[str, Any] = {}
        self._load_documents()

        # QA prompt (अस‑is)
        self.qa_prompt = PromptTemplate(
            template="""Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say you don't know.
Always justify from the context.

Context:
{context}

Question: {question}

Return:
1. Answer
2. Justification (cite context)
3. Confidence (0‑1)

Answer:""",
            input_variables=["context", "question"],
        )

    # ───────────────────────── internal helpers
    def _initialize_llm(self):
        key = os.getenv("OPENAI_API_KEY")
        if key:
            return ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=key,
            )
        return None

    def _load_documents(self):
        for fn in os.listdir(self.persist_directory):
            if fn.endswith(".json"):
                with open(os.path.join(self.persist_directory, fn), encoding="utf-8") as f:
                    self.documents[fn[:-5]] = json.load(f)
                print(f"📂 Loaded {fn}")

    # ───────────────────────── core: upload / index
    async def process_document(self, content: str, filename: str) -> str:
        doc_id = str(uuid.uuid4())
        chunks = self.text_splitter.split_text(content)
        collection_name = f"doc_{doc_id.replace('-', '_')}"

        col = self.client.create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        # 🚀 Batch embed (fast)
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

    # ───────────────────────── summary
    async def generate_summary(self, doc_id: str) -> str:
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            raise Exception("Document not found")
        return _gen_sum(self.documents[doc_id]["content"])

    # ───────────────────────── QA
    async def answer_question(
        self,
        question: str,
        doc_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        try:
            doc_id = doc_id.strip()
            if doc_id not in self.documents:
                raise Exception("Document not found")

            col = self.client.get_collection(self.documents[doc_id]["collection_name"])
            results = col.query(
                query_embeddings=[self.embeddings.embed_query(question)],
                n_results=5,
            )
            context = "\n\n".join(results["documents"][0])

            if self.llm and hasattr(self.llm, "predict"):
                prev = ""
                if conversation_history:
                    for turn in conversation_history[-3:]:
                        prev += f"Q: {turn['question']}\nA: {turn['answer']}\n\n"
                prompt = self.qa_prompt.format(context=context, question=question)
                answer = self.llm.predict(prev + prompt)
            else:
                answer = self._generate_basic_answer(question, context)

            return {
                "answer": answer,
                "justification": f"Citing {len(results['documents'][0])} passages",
                "source_snippets": results["documents"][0][:3],
                "confidence": 0.8,
            }
        except Exception as e:
            return {
                "answer": f"Error: {e}",
                "justification": "System error",
                "source_snippets": [],
                "confidence": 0.0,
            }

    def _generate_basic_answer(self, question: str, context: str) -> str:
        q_words = set(question.lower().split())
        sents = [s.strip() for s in context.split(".") if s.strip()]
        hits = [
            s for s in sents if len(q_words.intersection(set(s.lower().split()))) > 0
        ]
        return ". ".join(hits[:3]) + "." if hits else "No exact answer found."

    # ───────────────────────── search
    async def search_document(self, query: str, doc_id: str, top_k: int = 5):
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

    # ───────────────────────── misc helpers
    async def delete_document(self, doc_id: str) -> bool:
        doc_id = doc_id.strip()
        if doc_id not in self.documents:
            return False
        self.client.delete_collection(self.documents[doc_id]["collection_name"])
        del self.documents[doc_id]
        json_path = os.path.join(self.persist_directory, f"{doc_id}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
        return True

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
        return {
            "filename": meta["filename"],
            "word_count": len(c.split()),
            "character_count": len(c),
            "chunks": meta["chunks"],
            "preview": c[:500] + "..." if len(c) > 500 else c,
        }

    async def suggest_clarifications(self, question: str, doc_id: str):
        if doc_id.strip() not in self.documents:
            return []
        return [
            f"Could you clarify '{question}'?",
            f"Which aspect of '{question}' interests you?",
            f"Need more detail on '{question}'?",
        ]

    async def register_document(self, doc_id: str, content: str):
        if doc_id not in self.documents:
            self.documents[doc_id] = {
                "filename": f"{doc_id}.pdf",
                "content": content,
                "chunks": len(self.text_splitter.split_text(content)),
                "collection_name": f"doc_{doc_id.replace('-', '_')}",
            }
