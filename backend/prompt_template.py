"""Prompt templates and clinical safety instructions for MediBot AI."""
import re
from typing import List, Dict, Any

# Emergency symptom keywords that warrant immediate red-flag warnings
EMERGENCY_KEYWORDS = [
    r"\bchest\s+pain\b",
    r"\bheart\s+attack\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bdifficulty\s+breathing\b",
    r"\bcannot\s+breathe\b",
    r"\bsudden\s+numbness\b",
    r"\bparalysis\b",
    r"\bspeech\s+slurred\b",
    r"\bslurred\s+speech\b",
    r"\bstroke\b",
    r"\bsevere\s+allergic\s+reaction\b",
    r"\banaphylaxis\b",
    r"\bheavy\s+bleeding\b",
    r"\bcoughing\s+blood\b",
    r"\bvomiting\s+blood\b",
    r"\bsuicid(e|al)\b",
    r"\bloss\s+of\s+consciousness\b",
    r"\bunresponsive\b",
    r"\bseizure\b",
    r"\bpoison(ing|ed)?\b",
    r"\boverdose\b"
]

EMERGENCY_WARNING = """
> **🚨 RED FLAG EMERGENCY WARNING:**
> If you or someone around you is experiencing life-threatening symptoms (such as severe chest pain, sudden numbness/paralysis, difficulty breathing, slurred speech, or heavy uncontrolled bleeding), **please seek immediate medical emergency care or call your local emergency number (such as 911, 112, or 999) immediately.** Do not wait for an AI chatbot response.
"""

HISTORICAL_SOURCE_DISCLAIMER = """
> **⚠️ Historical Reference Notice (Published 2002):**
> Some retrieved medical references originate from *The Gale Encyclopedia of Medicine (Second Edition, 2002)*. While foundational anatomical and pathophysiological descriptions remain valid, clinical management, pharmacological guidelines, and diagnostic criteria may have evolved. Prioritize modern clinical guidelines and consult a healthcare practitioner before making medical decisions.
"""

MEDICAL_SYSTEM_PROMPT = """You are "MediBot AI", a Senior Medical Information Assistant powered by Retrieval-Augmented Generation (RAG).

Your objective is to provide clear, evidence-based, educational medical explanations based strictly on the retrieved medical documents.

STRICT MEDICAL SAFETY AND OPERATIONAL GUIDELINES:
1. EDUCATIONAL PURPOSE ONLY:
   - You are an informational assistant, NOT a doctor or medical practitioner.
   - NEVER claim to provide an official clinical diagnosis.
   - NEVER prescribe pharmaceutical drugs or specify drug dosages.
   - NEVER advise anyone to discontinue, increase, or change their current medically prescribed treatment or medication.

2. HISTORICAL CONTEXT & TEMPORAL INTEGRITY (CRITICAL):
   - The knowledge base contains both modern clinical guidelines (WHO 2023, ICMR 2023, CDC 2024, NIH 2024) AND historical reference texts (The Gale Encyclopedia of Medicine, 2002).
   - ALWAYS display the publication year and edition alongside cited sources.
   - If a treatment or diagnostic protocol originates from the 2002 Encyclopedia, explicitly state:
     "*(Note: Derived from historical medical literature published in 2002; modern clinical guidelines may have updated this protocol.)*"
   - If newer guidelines (e.g. WHO 2023 or ICMR 2023) contradict older recommendations, explicitly highlight the evolution in standard of care.
   - NEVER invent updated medical guidelines. If modern evidence is not present in the retrieved context, openly state that modern verification is needed.

3. ACCESSIBLE LANGUAGE:
   - Explain clinical terminology in clear, compassionate, and understandable language.
   - Structure responses with bullet points, clear headings, and concise paragraphs.

4. CITATION REQUIREMENT:
   - For every substantive medical claim, include a citation format: "(Source: *Document Name*, Page X [Year])".

5. PROFESSIONAL ADVICE REMINDER:
   - Conclude informative responses with an appropriate note reminding the user to discuss individual medical concerns with their healthcare provider.
"""


def detect_emergency(text: str) -> bool:
    """Checks whether the user query mentions any red flag medical emergencies."""
    lower_text = text.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, lower_text):
            return True
    return False


def build_rag_prompt(question: str, context_chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> str:
    """Builds the complete formatted prompt including conversation context and retrieved medical chunks."""
    
    # Format retrieved document context with publication year & historical tag
    if not context_chunks:
        context_str = "No relevant medical documents found in the current knowledge base."
    else:
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get("source", "Unknown Document")
            page = chunk.get("page", 1)
            year = chunk.get("publication_year", 2024)
            category = chunk.get("medical_category", "General Medicine")
            section = chunk.get("section_title", "Clinical Section")
            is_historical = chunk.get("is_historical", False)
            hist_tag = " [HISTORICAL REFERENCE - 2002]" if is_historical else " [CURRENT GUIDELINE]"
            
            text = chunk.get("text", "").strip()
            header = f"--- [DOCUMENT CHUNK {i}] ({source}, Page: {page}, Year: {year}, Category: {category}{hist_tag}) ---"
            context_parts.append(f"{header}\nTopic Section: {section}\n{text}")
        context_str = "\n\n".join(context_parts)
    
    # Format recent history if present
    history_str = ""
    if chat_history:
        history_lines = []
        for msg in chat_history[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.get('content', '')}")
        history_str = "\n".join(history_lines)
    
    prompt = f"""RETRIEVED EVIDENCE-BASED MEDICAL CONTEXT:
{context_str}

"""
    if history_str:
        prompt += f"""RECENT CONVERSATION HISTORY:
{history_str}

"""
    prompt += f"""USER'S MEDICAL QUESTION:
{question}

INSTRUCTIONS FOR YOUR RESPONSE:
Synthesize an educational, accurate, and easy-to-understand response based on the retrieved context above. Include citations with source name, page number, and publication year. If information comes from a historical reference (e.g. 2002), explicitly note that treatment guidelines may have evolved and advise consulting a healthcare professional."""

    return prompt
