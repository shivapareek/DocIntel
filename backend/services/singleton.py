from services.rag import RAGService
from services.quiz import QuizService

rag_service = RAGService()
quiz_service = QuizService(rag_service=rag_service) 
