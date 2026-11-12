"""RAG Chatbot engine and Groq LLM integration for MediBot AI."""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)
from backend.prompt_template import (
    MEDICAL_SYSTEM_PROMPT,
    EMERGENCY_WARNING,
    detect_emergency,
    build_rag_prompt
)
from backend.vectorstore import get_vector_store
from backend.schemas import SourceCitation, ChatResponse

logger = logging.getLogger("medibot.chatbot")

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "4"))


class SessionMemoryManager:
    """Manages independent conversation histories keyed by session_id."""
    def __init__(self, max_history_turns: int = 20):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_turns = max_history_turns

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_user_message(self, session_id: str, content: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._trim_history(session_id)

    def add_ai_message(self, session_id: str, content: str, sources: List[Dict[str, Any]] = None):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": "assistant",
            "content": content,
            "sources": sources or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._trim_history(session_id)

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def _trim_history(self, session_id: str):
        if len(self._sessions[session_id]) > self.max_history_turns * 2:
            self._sessions[session_id] = self._sessions[session_id][-self.max_history_turns * 2:]


class MediBotRAG:
    """Orchestrates RAG retrieval, medical prompt construction, and Groq inference."""
    def __init__(self):
        self.vector_store = get_vector_store()
        self.memory = SessionMemoryManager()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self.client: Optional[Groq] = None
        self._init_client()

    def _init_client(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        if self.groq_api_key and not self.groq_api_key.startswith("gsk_your_groq_api_key"):
            try:
                self.client = Groq(api_key=self.groq_api_key)
                logger.info(f"Groq client initialized with model '{self.model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.warning("GROQ_API_KEY is not configured. Assistant will run in fallback simulation mode.")
            self.client = None

    def query(self, question: str, session_id: Optional[str] = None, category_filter: Optional[str] = None) -> ChatResponse:
        """Processes a medical query through the full RAG pipeline using hybrid retrieval and historical citation tracking."""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        question_cleaned = question.strip()
        is_emergency = detect_emergency(question_cleaned)
        
        # 1. Retrieve relevant context using Advanced Hybrid Search (FAISS + BM25 + RRF)
        context_chunks = self.vector_store.hybrid_search(
            question_cleaned, 
            top_k=TOP_K_RETRIEVAL,
            category_filter=category_filter
        )
        
        # 2. Extract rich citations with publication year and historical flag
        citations: List[SourceCitation] = []
        seen_citations = set()
        matched_categories = set()
        has_historical = False

        for chunk in context_chunks:
            source = chunk.get("source") or chunk.get("document_name") or "Medical Reference"
            page = chunk.get("page")
            citation_key = (source, page)
            
            is_hist = bool(chunk.get("is_historical", False))
            if is_hist:
                has_historical = True
                
            cat = chunk.get("medical_category")
            if cat:
                matched_categories.add(cat)

            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                excerpt = chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
                citations.append(SourceCitation(
                    source=source,
                    page=page,
                    excerpt=excerpt,
                    edition=chunk.get("edition", "Standard Reference"),
                    publication_year=chunk.get("publication_year"),
                    medical_category=cat or "General Medicine",
                    section_title=chunk.get("section_title", ""),
                    source_type=chunk.get("source_type", "medical_reference"),
                    is_historical=is_hist
                ))

        # 3. Retrieve session conversation history
        history = self.memory.get_history(session_id)
        
        # 4. Generate answer via Groq LLM (or structured medical fallback if API key is not yet set)
        answer = self._generate_answer(question_cleaned, context_chunks, history, is_emergency)
        
        # If emergency detected, prepend emergency guidance banner
        if is_emergency:
            answer = f"{EMERGENCY_WARNING.strip()}\n\n{answer}"
        
        # 5. Record turn in session memory
        self.memory.add_user_message(session_id, question_cleaned)
        self.memory.add_ai_message(session_id, answer, [c.model_dump() for c in citations])
        
        return ChatResponse(
            answer=answer,
            sources=citations,
            session_id=session_id,
            is_emergency=is_emergency,
            has_historical_sources=has_historical,
            medical_categories=list(matched_categories)
        )

    def _generate_answer(self, question: str, context_chunks: List[Dict[str, Any]], history: List[Dict[str, Any]], is_emergency: bool) -> str:
        """Calls Groq LLM with prompt or returns graceful fallback."""
        load_dotenv(override=True)
        if self.client is None or not self.groq_api_key:
            self._init_client()

        if self.client is not None:
            try:
                user_prompt = build_rag_prompt(question, context_chunks, history)
                messages = [
                    {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
                
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.2,  # Low temperature for factual medical grounding
                    max_tokens=1024,
                    top_p=0.9,
                )
                
                return completion.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Groq API call error: {e}")
                return self._generate_fallback_response(question, context_chunks, str(e))
        else:
            return self._generate_fallback_response(question, context_chunks, "GROQ_API_KEY is not set.")

    def _generate_fallback_response(self, question: str, context_chunks: List[Dict[str, Any]], reason: str) -> str:
        """Provides an intelligent grounded response when Groq API key is not yet configured."""
        if not context_chunks:
            return (
                f"**Welcome to MediBot AI.**\n\n"
                f"I received your question: *\"{question}\"*.\n\n"
                f"Currently, there are no medical documents indexed in the vector database, or your Groq API key is pending configuration.\n\n"
                f"**To get full AI responses:**\n"
                f"1. Please configure your `GROQ_API_KEY` in the `.env` file (get a free key at [Groq Console](https://console.groq.com/keys)).\n"
                f"2. Upload reference medical PDF documents in the left sidebar or upload panel.\n\n"
                f"*Medical Disclaimer: MediBot AI provides information for educational purposes only. Always consult a licensed medical provider for diagnostic or treatment decisions.*"
            )
        
        # If we have retrieved chunks, present the retrieved evidence clearly!
        best_chunk = context_chunks[0]
        snippet = best_chunk.get("text", "")
        source = best_chunk.get("source", "Document")
        page = best_chunk.get("page", 1)
        
        return (
            f"**Information retrieved from medical documents:**\n\n"
            f"Based on **{source}** (Page {page}), the following relevant excerpt was retrieved regarding your inquiry on *\"{question}\"*:\n\n"
            f"> \"{snippet}\"\n\n"
            f"---\n"
            f"*Note: Running with local FAISS document retrieval. To enable LLM natural language synthesis, add your `GROQ_API_KEY` to the `.env` configuration file.*"
        )


_rag_instance: Optional[MediBotRAG] = None

def get_rag_engine() -> MediBotRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = MediBotRAG()
    return _rag_instance

