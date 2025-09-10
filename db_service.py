# db_service.py
import os
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

from azure.cosmos import CosmosClient, exceptions


COSMOS_ENDPOINT   = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY        = os.environ["COSMOS_KEY"]
COSMOS_DB         = os.environ["COSMOS_DB"]
COSMOS_CONTAINER  = os.environ["COSMOS_CONTAINER"]


PARTITION_KEY_FIELD = "/sessionId"

MAX_HISTORY_PAIRS = int(os.getenv("MAX_HISTORY_PAIRS", "50") or "50")

client    = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database  = client.get_database_client(COSMOS_DB)
container = database.get_container_client(COSMOS_CONTAINER)

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def _ensure_session_doc(session_id: str) -> Dict:
    """Read or create the session document."""
    try:
        return container.read_item(item=session_id, partition_key=session_id)
    except exceptions.CosmosResourceNotFoundError:
        doc = {
            "id": session_id,
            "sessionId": session_id,       
            "session": session_id,
            "session_id": session_id,
            "history": [],
            "created_at": _utcnow_iso(),
            "last_updated": _utcnow_iso(),
        }
        try:
            result = container.upsert_item(body=doc)
            logging.info(f"Created new session document: {session_id}")
            return result
        except exceptions.CosmosResourceExistsError:
            try:
                return container.read_item(item=session_id, partition_key=session_id)
            except Exception as e:
                logging.warning(f"Failed to read existing document after conflict: {e}")
                return doc

def save_turn(session_id: str, user_msg: str, bot_msg: str) -> None:
    """
    Append user/bot turns to the single doc for this session.
    This method properly accumulates chat history without overwriting.
    """

    try:
        doc = _ensure_session_doc(session_id)
        hist = doc.get("history", [])
        
        user_message = {
            "role": "user",
            "content": user_msg
        }
        
        assistant_message = {
            "role": "assistant", 
            "content": bot_msg
        }
        
        hist.append(user_message)
        hist.append(assistant_message)
        
        if MAX_HISTORY_PAIRS and len(hist) > 2 * MAX_HISTORY_PAIRS:
            hist = hist[-2 * MAX_HISTORY_PAIRS :]
        
        doc["history"] = hist
        doc["last_updated"] = _utcnow_iso()
        
        container.upsert_item(body=doc)
        logging.info(f"✅ Accumulated turn to session {session_id}: {len(hist)} total messages")
        
    except Exception as e:
        logging.exception(f"Failed to save turn to session {session_id}: {e}")

def get_history(session_id: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Return the last `limit` (user,assistant) pairs as a flat list of messages.
    If limit is None, return full history.
    """
    try:
        doc = container.read_item(item=session_id, partition_key=session_id)
        hist = doc.get("history", [])
        if limit:
            return hist[-2 * int(limit) :]
        return hist
    except exceptions.CosmosResourceNotFoundError:
        try:
            query = f"SELECT c.history FROM c WHERE c.id = '{session_id}'"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            if items:
                hist = items[0].get("history", [])
                if limit:
                    return hist[-2 * int(limit) :]
                return hist
            return []
        except Exception as e:
            logging.warning(f"Query-based history retrieval also failed for session {session_id}: {e}")
            return []
    except Exception as e:
        logging.exception(f"Cosmos get_history failed: {e}")
        return []

def clear_session(session_id: str) -> None:
    """Clear the history for a session."""
    try:
        doc = _ensure_session_doc(session_id)
        doc["history"] = []
        doc["last_updated"] = _utcnow_iso()
        container.replace_item(item=doc, body=doc)
        logging.info(f"Cleared history for session: {session_id}")
    except Exception as e:
        logging.exception(f"Failed to clear session {session_id}: {e}")

def get_session_info(session_id: str) -> Optional[Dict]:
    """Get session information including message counts."""
    try:
        doc = container.read_item(item=session_id, partition_key=session_id)
        hist = doc.get("history", [])
        
        user_messages = [msg for msg in hist if msg.get("role") == "user"]
        assistant_messages = [msg for msg in hist if msg.get("role") == "assistant"]
        
        return {
            "session_id": session_id,
            "total_messages": len(hist),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "created_at": doc.get("created_at"),
            "last_updated": doc.get("last_updated"),
            "max_history_pairs": MAX_HISTORY_PAIRS
        }
    except exceptions.CosmosResourceNotFoundError:
        try:
            query = f"SELECT c.history, c.created_at, c.last_updated FROM c WHERE c.id = '{session_id}'"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            if items:
                doc = items[0]
                hist = doc.get("history", [])
                user_messages = [msg for msg in hist if msg.get("role") == "user"]
                assistant_messages = [msg for msg in hist if msg.get("role") == "assistant"]
                
                return {
                    "session_id": session_id,
                    "total_messages": len(hist),
                    "user_messages": len(user_messages),
                    "assistant_messages": len(assistant_messages),
                    "created_at": doc.get("created_at"),
                    "last_updated": doc.get("last_updated"),
                    "max_history_pairs": MAX_HISTORY_PAIRS
                }
        except Exception as e:
            logging.warning(f"Query-based session info retrieval failed for {session_id}: {e}")
        return None
    except Exception as e:
        logging.exception(f"Failed to get session info for {session_id}: {e}")
        return None

def list_sessions() -> List[Dict]:
    """List all sessions with basic info."""
    try:
        query = "SELECT c.id, c.session_id, c.created_at, c.last_updated, ARRAY_LENGTH(c.history) as message_count FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return items
    except Exception as e:
        logging.exception(f"Failed to list sessions: {e}")
        return []
