# db_service.py
import os
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

from azure.cosmos import CosmosClient, exceptions

# ENV you should already have:
# COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB, COSMOS_CONTAINER
COSMOS_ENDPOINT   = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY        = os.environ["COSMOS_KEY"]
COSMOS_DB         = os.environ["COSMOS_DB"]
COSMOS_CONTAINER  = os.environ["COSMOS_CONTAINER"]

# Partition key path for the container
# (must match how your container was created)
PARTITION_KEY_FIELD = "/sessionId"

# How many (user,assistant) pairs to keep in the doc (rolling window)
MAX_HISTORY_PAIRS = int(os.getenv("MAX_HISTORY_PAIRS", "50"))

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
            "sessionId": session_id,       # <- partition key (must match container config)
            "session": session_id,
            "session_id": session_id,
            "history": [],
            "created_at": _utcnow_iso(),
            "last_updated": _utcnow_iso(),
        }
        # Use upsert to handle potential conflicts
        try:
            result = container.upsert_item(body=doc)
            logging.info(f"Created new session document: {session_id}")
            return result
        except exceptions.CosmosResourceExistsError:
            # Document was created by another process, try to read it
            try:
                return container.read_item(item=session_id, partition_key=session_id)
            except Exception as e:
                logging.warning(f"Failed to read existing document after conflict: {e}")
                # Return the document we tried to create
                return doc

def save_turn(session_id: str, user_msg: str, bot_msg: str) -> None:
    """
    Append user/bot turns to the single doc for this session.
    This method properly accumulates chat history without overwriting.
    """

    try:
        # Get or create the document
        doc = _ensure_session_doc(session_id)
        hist = doc.get("history", [])
        
        # Create simplified message objects with only role and content
        user_message = {
            "role": "user",
            "content": user_msg
        }
        
        assistant_message = {
            "role": "assistant", 
            "content": bot_msg
        }
        
        # Append the new messages to history
        hist.append(user_message)
        hist.append(assistant_message)
        
        # Trim if needed to prevent document size issues
        if MAX_HISTORY_PAIRS and len(hist) > 2 * MAX_HISTORY_PAIRS:
            hist = hist[-2 * MAX_HISTORY_PAIRS :]
        
        # Update the document
        doc["history"] = hist
        doc["last_updated"] = _utcnow_iso()
        
        # Use upsert for reliable operation
        container.upsert_item(body=doc)
        logging.info(f"✅ Accumulated turn to session {session_id}: {len(hist)} total messages")
        
    except Exception as e:
        logging.exception(f"Failed to save turn to session {session_id}: {e}")

def get_history(session_id: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Return the last `limit` (user,assistant) pairs as a flat list of messages.
    If limit is None, return full history.
    """
    # Try direct read first
    try:
        doc = container.read_item(item=session_id, partition_key=session_id)
        hist = doc.get("history", [])
        if limit:
            return hist[-2 * int(limit) :]
        return hist
    except exceptions.CosmosResourceNotFoundError:
        # If direct read fails, try query-based approach
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
        # Try direct read first
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
        # Try query-based approach
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
