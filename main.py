import os
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

from search_client import run_search, HAVE_SEARCH

load_dotenv(find_dotenv(), override=True)
logging.basicConfig(level=logging.INFO)

AOAI_ENDPOINT    = os.environ["AZURE_OPENAI_ENDPOINT"]
AOAI_KEY         = os.environ["AZURE_OPENAI_KEY"]
AOAI_DEPLOYMENT  = os.environ["AZURE_OPENAI_DEPLOYMENT"]
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

HISTORY_PAIRS = int(os.getenv("HISTORY_PAIRS", "3") or "3")

ABOUT_QU_PATH = os.getenv("ABOUT_QU_PATH", os.path.join("kb", "about_qu.md"))
try:
    with open(ABOUT_QU_PATH, "r", encoding="utf-8") as f:
        ABOUT_QU_TEXT = f.read()
except FileNotFoundError:
    ABOUT_QU_TEXT = ""

# ---------- Azure OpenAI client ----------
from openai import AzureOpenAI
aoai = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
    api_version=AOAI_API_VERSION,
)

try:
    from chat_history_manager import QUChatHistoryManager
    HAVE_CHAT_HISTORY = True
    logging.info("QU Chat History Manager available")
except Exception as e:
    HAVE_CHAT_HISTORY = False
    logging.warning(f"QU Chat History Manager not available: {e}")

# Global chat history manager (will be initialized per session)
chat_history_managers = {}

def get_chat_history_manager(session_id: Optional[str] = None) -> QUChatHistoryManager:
    """Get or create a chat history manager for the given session."""
    if not HAVE_CHAT_HISTORY:
        return None
    
    if session_id not in chat_history_managers:
        chat_history_managers[session_id] = QUChatHistoryManager(
            session_id=session_id,
            max_messages=20
        )
        logging.info(f"Created new chat history manager for session: {session_id}")
    
    return chat_history_managers[session_id]

# ---------- Semantic Kernel setup ----------
USE_SK = True  # Enable SK with proper modern setup
try:
    import semantic_kernel as sk
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
    from semantic_kernel.contents import ChatHistory

    kernel = sk.Kernel()
    
    # Add Azure OpenAI chat service using modern approach
    kernel.add_service(
        AzureChatCompletion(
            deployment_name=AOAI_DEPLOYMENT,
            endpoint=AOAI_ENDPOINT,
            api_key=AOAI_KEY,
        )
    )
    logging.info("Semantic Kernel initialized successfully")

    # Enhanced conversation-aware answer prompt
    qa_prompt = """
You are the Qatar University Assistant with full conversation awareness.

IMPORTANT: You have access to the complete conversation history. Use this to:
- Remember what the user has asked before
- Provide consistent answers based on previous interactions
- Acknowledge when the user is referring to previous questions
- Correctly answer questions about what was discussed earlier

Guidelines:
- CHITCHAT: 1-2 friendly sentences, acknowledging conversation context when relevant
- ADMISSIONS: Answer from CONTEXT when available, but you can also answer general Qatar University questions using your knowledge
- ABOUT_QU: answer ONLY from ABOUT_QU context provided
- If info is missing in CONTEXT, say: "I don't know from the available information"
- Limit to max ~6 short sentences. Cite sources as [1], [2] using SOURCES order when helpful
- ALWAYS check the conversation history before answering questions about what was discussed

MODE: {{$mode}}

CONVERSATION HISTORY (oldest→newest, use this for context awareness):
{{$history}}

CONTEXT:
{{$context}}

SOURCES (index → name; may be empty):
{{$sources}}

User question: {{$question}}

Assistant:
""".strip()

except Exception as e:
    USE_SK = False
    kernel = None
    logging.warning(f"Semantic Kernel unavailable; falling back to direct AOAI only. Error: {e}")

# ---------- FastAPI ----------
app = FastAPI(title="QU Admissions Chatbot")

# Static UI (optional)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "web")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/chat-ui", include_in_schema=False)
def chat_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# ---------- Models ----------
class Query(BaseModel):
    q: str
    top: int = 5

class ChatReq(BaseModel):
    message: str
    top: int = 5
    session_id: Optional[str] = None

class SessionReq(BaseModel):
    session_id: Optional[str] = None

# ---------- Helpers ----------
def _format_context(hits: List[Dict]) -> str:
    return "\n---\n".join([(h.get("snippet") or "").replace("\n", " ") for h in hits]) if hits else ""

def _format_sources(hits: List[Dict]) -> str:
    return "\n".join([f"[{i}] {h.get('name')}" for i, h in enumerate(hits, start=1)])

def _format_history(turns: List[Dict]) -> str:
    if not turns:
        return ""
    lines = []
    for t in turns:
        um = (t.get("user") or "").replace("\n", " ")
        bm = (t.get("bot") or "").replace("\n", " ")
        lines.append(f"User: {um}\nAssistant: {bm}")
    return "\n".join(lines)

def _safe_aoai_chat(messages, temperature=0):
    try:
        resp = aoai.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            temperature=temperature,
            messages=messages,
            max_tokens=220,  # keep responses tight
        )
        return resp.choices[0].message.content
    except Exception:
        logging.exception("AOAI call failed")
        return "Sorry—something went wrong while generating a reply."

def _aoai_answer_direct(mode: str, question: str, context: str, sources: str, history_text: str) -> str:
    """Direct Azure OpenAI chat with enhanced conversation awareness."""
    try:
        logging.info(f"Starting _aoai_answer_direct with mode: {mode}, question: {question}")
        
        system = (
            "You are the Qatar University Assistant with full conversation awareness. "
            "IMPORTANT: You have access to the complete conversation history. Use this to: "
            "- Remember what the user has asked before "
            "- Provide consistent answers based on previous interactions "
            "- Acknowledge when the user is referring to previous questions "
            "- Correctly answer questions about what was discussed earlier "
            "Keep answers concise and helpful (2-4 sentences). "
            "CHITCHAT: 1-2 friendly sentences, acknowledging conversation context when relevant. "
            "ADMISSIONS: Answer from the provided context about Qatar University admissions, requirements, programs, fees, deadlines, and procedures. "
            "ABOUT_QU: Answer from the provided context about Qatar University general information, campus, programs, and contact details. "
            "ALWAYS check the conversation history before answering questions about what was discussed. "
            "If the specific information is not in the provided context, say 'I don't have that specific information in my current knowledge base, but I can help you with general Qatar University information.' "
            "Always be helpful and guide users to contact the admissions office for detailed information."
        )
        
        user = (
            f"MODE: {mode}\n\n"
            f"CONVERSATION HISTORY (oldest→newest, use this for context awareness):\n{history_text or '(empty)'}\n\n"
            f"User question: {question}\n\n"
            f"CONTEXT:\n{context or '(empty)'}\n\n"
            f"SOURCES:\n{sources or '(none)'}"
        )
        
        logging.info(f"Making AOAI call with deployment: {AOAI_DEPLOYMENT}")
        
        response = aoai.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=300,
            temperature=0
        )
        
        answer = response.choices[0].message.content
        logging.info(f"AOAI call successful, answer: {answer[:50]}...")
        return answer
        
    except Exception as e:
        logging.error(f"Direct AOAI call failed: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

# ---------- Endpoints ----------
@app.get("/")
def root():
    return {
        "status": "ok",
        "chat_history_manager": HAVE_CHAT_HISTORY,
        "sk": USE_SK,
        "about_qu_loaded": bool(ABOUT_QU_TEXT),
        "active_sessions": len(chat_history_managers),
        "azure_search_available": HAVE_SEARCH,
        "azure_openai_configured": bool(AOAI_ENDPOINT and AOAI_KEY and AOAI_DEPLOYMENT),
    }

@app.get("/test-aoai")
def test_aoai():
    """Test Azure OpenAI connection directly."""
    try:
        logging.info("Testing Azure OpenAI connection...")
        
        response = aoai.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=50
        )
        
        answer = response.choices[0].message.content
        logging.info(f"AOAI test successful: {answer}")
        
        return {
            "status": "success",
            "answer": answer,
            "deployment": AOAI_DEPLOYMENT
        }
        
    except Exception as e:
        logging.error(f"AOAI test failed: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": str(e),
            "deployment": AOAI_DEPLOYMENT
        }

@app.get("/debug-env")
def debug_env():
    """Debug environment variables."""
    import os
    return {
        "working_dir": os.getcwd(),
        "aoai_endpoint": AOAI_ENDPOINT[:20] + "..." if AOAI_ENDPOINT else None,
        "aoai_deployment": AOAI_DEPLOYMENT,
        "aoai_key_length": len(AOAI_KEY) if AOAI_KEY else 0,
        "env_vars": {
            "AZURE_OPENAI_ENDPOINT": bool(os.environ.get("AZURE_OPENAI_ENDPOINT")),
            "AZURE_OPENAI_KEY": bool(os.environ.get("AZURE_OPENAI_KEY")),
            "AZURE_OPENAI_DEPLOYMENT": bool(os.environ.get("AZURE_OPENAI_DEPLOYMENT")),
            "AZURE_SEARCH_ENDPOINT": bool(os.environ.get("AZURE_SEARCH_ENDPOINT")),
            "AZURE_SEARCH_INDEX": bool(os.environ.get("AZURE_SEARCH_INDEX")),
            "AZURE_SEARCH_KEY": bool(os.environ.get("AZURE_SEARCH_KEY")),
            "COSMOS_ENDPOINT": bool(os.environ.get("COSMOS_ENDPOINT")),
            "COSMOS_KEY": bool(os.environ.get("COSMOS_KEY")),
        }
    }

@app.post("/search")
def search(body: Query):
    return {"results": run_search(body.q, body.top)}

@app.post("/chat")
async def chat(body: ChatReq, request: Request):
    try:
        # Get or create session ID
        session_id = body.session_id
        if not session_id:
            # Try to get from headers (for web UI)
            session_id = request.headers.get("X-Session-ID")
        
        if not session_id:
            # Create new session
            session_id = f"qu-session-{os.urandom(4).hex()}"
            logging.info(f"Created new session: {session_id}")

        # Get chat history manager for this session
        chat_history_manager = get_chat_history_manager(session_id)
        
        # Get conversation history
        if chat_history_manager:
            history_text = chat_history_manager.get_formatted_history(HISTORY_PAIRS)
        else:
            history_text = ""

        # Enhanced routing logic for better responses without Azure Search
        question_lower = body.message.lower()
        
        # Define keywords for different categories
        admissions_keywords = [
            'admission', 'apply', 'application', 'requirements', 'deadline', 'fee', 'tuition',
            'scholarship', 'financial aid', 'documents', 'certificate', 'ielts', 'toefl',
            'entrance exam', 'interview', 'acceptance', 'registration', 'enrollment',
            'engineering', 'business', 'medicine', 'pharmacy', 'nursing', 'computer science',
            'civil engineering', 'mechanical', 'electrical', 'accounting', 'finance', 'marketing'
        ]
        
        about_qu_keywords = [
            'qu', 'qatar university', 'university', 'college', 'campus', 'location',
            'established', 'history', 'overview', 'about', 'information', 'contact',
            'phone', 'email', 'website', 'address', 'facilities', 'library', 'research'
        ]
        
        chitchat_keywords = [
            'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
            'how are you', 'what can you do', 'help', 'assistance'
        ]
        
        # Determine mode based on keyword matching
        if any(word in question_lower for word in chitchat_keywords):
            mode = "CHITCHAT"
        elif any(word in question_lower for word in admissions_keywords):
            mode = "ADMISSIONS"
        elif any(word in question_lower for word in about_qu_keywords):
            mode = "ABOUT_QU"
        else:
            # Default to ADMISSIONS for general queries
            mode = "ADMISSIONS"

        # Build context & sources per mode
        hits: List[Dict] = []
        context = ""
        sources = ""
        effective_query = body.message

        if mode == "CHITCHAT":
            pass  # no search/context needed
        elif mode == "ABOUT_QU":
            context = ABOUT_QU_TEXT or ""
            sources = "[1] Qatar University Information Guide"
        else:  # ADMISSIONS
            # Use local knowledge base for admissions since Azure Search is not available
            context = ABOUT_QU_TEXT or ""
            sources = "[1] Qatar University Admissions Guide"
            
            # Try Azure Search if available (for future use)
            if HAVE_SEARCH:
                try:
                    hits = run_search(effective_query, body.top)
                    if hits:  # If search returns results, use them
                        context = _format_context(hits)
                        sources = _format_sources(hits)
                    else:  # Fallback to local knowledge
                        context = ABOUT_QU_TEXT or ""
                        sources = "[1] Qatar University Admissions Guide"
                except Exception as e:
                    logging.warning(f"Search failed, using local knowledge: {e}")
                    context = ABOUT_QU_TEXT or ""
                    sources = "[1] Qatar University Admissions Guide"

        # Generate answer using direct AOAI (simplified approach)
        answer = ""
        logging.info(f"Using direct AOAI approach for chat response")
        
        # For now, use direct AOAI to ensure reliability
        enhanced_history = ""
        if chat_history_manager:
            enhanced_history = chat_history_manager.get_formatted_history(10)  # Get more history
        
        # Check if we have any context to work with
        if not context and mode != "CHITCHAT":
            if mode == "ADMISSIONS":
                answer = "I apologize, but I'm currently unable to access the admissions documents. Please check that the Azure Search service is properly configured and indexed with PDF documents."
            elif mode == "ABOUT_QU":
                answer = "I apologize, but I'm currently unable to access the Qatar University information. Please check the local knowledge base configuration."
            else:
                answer = "I apologize, but I'm having trouble accessing the information you requested. Please try again later."
        else:
            answer = _aoai_answer_direct(mode, body.message, context, sources, enhanced_history)

        # Ensure we have a valid answer
        if not answer or answer.strip() == "":
            answer = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

        # Save the conversation turn using chat history manager
        if chat_history_manager:
            try:
                # Add user message to history
                chat_history_manager.add_user_message(body.message)
                # Add assistant response to history (this also saves to Cosmos DB)
                chat_history_manager.add_assistant_message(answer)
            except Exception as e:
                logging.warning(f"Failed to save turn using chat history manager (non-fatal): {e}")

        # Calculate history_used based on available data
        history_used = 0
        if chat_history_manager:
            try:
                stats = chat_history_manager.get_history_stats()
                history_used = stats.get('user_messages', 0)
            except Exception as e:
                logging.warning(f"Failed to get history stats: {e}")
        
        return {
            "session_id": session_id,
            "mode": mode,
            "query_used": effective_query,
            "from_index": len(hits),
            "answer": answer,
            "sources": (
                [{"id": i + 1, "name": h["name"], "path": h["path"]} for i, h in enumerate(hits)]
                if hits else ([{"id": 1, "name": "About QU (local knowledge)", "path": "local"}] if mode == "ABOUT_QU" else [])
            ),
            "history_used": history_used,
        }
    except Exception as e:
        logging.exception(f"Unhandled error in /chat: {e}")
        return JSONResponse(
            status_code=500, 
            content={
                "error": f"An error occurred while processing your request: {str(e)}",
                "session_id": session_id if 'session_id' in locals() else None
            }
        )

# ---------- Session Management Endpoints ----------

@app.post("/session/new")
def create_new_session(body: SessionReq = None):
    """Create a new chat session."""
    try:
        session_id = body.session_id if body else None
        chat_history_manager = get_chat_history_manager(session_id)
        
        if chat_history_manager:
            new_session_id = chat_history_manager.create_new_session()
            # Update the manager in our dictionary
            chat_history_managers[new_session_id] = chat_history_manager
            if session_id and session_id in chat_history_managers:
                del chat_history_managers[session_id]
            
            return {
                "status": "success",
                "session_id": new_session_id,
                "message": "New session created"
            }
        else:
            return JSONResponse(status_code=503, content={"error": "Chat history manager not available"})
    except Exception as e:
        logging.exception("Failed to create new session")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/session/{session_id}/info")
def get_session_info(session_id: str):
    """Get information about a specific session."""
    try:
        chat_history_manager = get_chat_history_manager(session_id)
        if not chat_history_manager:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        return {
            "session_id": session_id,
            "history_stats": chat_history_manager.get_history_stats(),
            "session_info": chat_history_manager.get_session_info()
        }
    except Exception as e:
        logging.exception("Failed to get session info")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/chat/history/stats")
def get_chat_history_stats(session_id: Optional[str] = None):
    """Get statistics about the current chat history."""
    try:
        if not session_id:
            # Return stats for all sessions
            all_stats = {}
            for sid, manager in chat_history_managers.items():
                all_stats[sid] = manager.get_history_stats()
            return {"sessions": all_stats, "total_sessions": len(all_stats)}
        
        chat_history_manager = get_chat_history_manager(session_id)
        if not chat_history_manager:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        return chat_history_manager.get_history_stats()
    except Exception as e:
        logging.exception("Failed to get chat history stats")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/chat/history/clear")
def clear_chat_history(body: SessionReq):
    """Clear the chat history for a specific session."""
    try:
        chat_history_manager = get_chat_history_manager(body.session_id)
        if not chat_history_manager:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        chat_history_manager.clear_history()
        return {
            "status": "success", 
            "session_id": body.session_id,
            "message": "Chat history cleared"
        }
    except Exception as e:
        logging.exception("Failed to clear chat history")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/chat/history/recent")
def get_recent_history(session_id: str, limit: int = 10):
    """Get recent chat history for a specific session."""
    try:
        chat_history_manager = get_chat_history_manager(session_id)
        if not chat_history_manager:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        messages = chat_history_manager.get_recent_messages(limit)
        return {
            "session_id": session_id,
            "messages": messages, 
            "count": len(messages)
        }
    except Exception as e:
        logging.exception("Failed to get recent history")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/sessions/list")
def list_all_sessions():
    """List all active sessions."""
    try:
        sessions = []
        for session_id, manager in chat_history_managers.items():
            stats = manager.get_history_stats()
            sessions.append({
                "session_id": session_id,
                "total_messages": stats.get("total_messages", 0),
                "user_messages": stats.get("user_messages", 0),
                "assistant_messages": stats.get("assistant_messages", 0),
                "last_updated": stats.get("last_updated", "unknown")
            })
        
        return {
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
    except Exception as e:
        logging.exception("Failed to list sessions")
        return JSONResponse(status_code=500, content={"error": str(e)})
