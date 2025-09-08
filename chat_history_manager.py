# chat_history_manager.py
import os
import logging
import time
import uuid
from typing import List, Dict, Optional

try:
    from semantic_kernel.contents import ChatHistory
    from semantic_kernel.contents.chat_history import ChatHistoryTruncationReducer
    from semantic_kernel.contents.utils.author_role import AuthorRole
    HAVE_SK = True
except ImportError:
    HAVE_SK = False
    logging.warning("Semantic Kernel not available")

try:
    from db_service import save_turn, get_history, clear_session, get_session_info
    HAVE_DB = True
except ImportError:
    HAVE_DB = False
    logging.warning("Database service not available")

class QUChatHistoryManager:
    def __init__(self, session_id: str = None, max_messages: int = 20):
        self.session_id = session_id or self._generate_session_id()
        self.max_messages = max_messages
        
        if HAVE_SK:
            self.chat_history = ChatHistoryTruncationReducer(
                target_count=max_messages,
                auto_reduce=True
            )
        else:
            self.chat_history = None
            self.messages = []
            
        self._load_existing_history()
        
        # Add system message if no history exists
        if not self._has_messages():
            self.add_system_message("You are the Qatar University Assistant. Keep answers concise and helpful.")

    def _has_messages(self) -> bool:
        """Check if there are any messages."""
        if HAVE_SK and self.chat_history:
            return len(self.chat_history.messages) > 0
        else:
            return len(self.messages) > 0

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"qu-session-{uuid.uuid4().hex[:8]}"

    def _load_existing_history(self):
        """Load existing history from Cosmos DB into the ChatHistory object."""
        if not HAVE_DB:
            return

        try:
            # Add a longer delay for Cosmos DB consistency
            time.sleep(1.0)
            
            # Try multiple times to read history due to Cosmos DB eventual consistency
            max_retries = 3
            history_data = None
            
            for attempt in range(max_retries):
                try:
                    history_data = get_history(self.session_id)
                    if history_data:
                        break
                    else:
                        logging.info(f"No history found on attempt {attempt + 1} for session {self.session_id}")
                        if attempt < max_retries - 1:
                            time.sleep(2.0)  # Wait longer between retries
                except Exception as e:
                    logging.warning(f"Failed to load history on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2.0)
            
            if history_data:
                if HAVE_SK and self.chat_history:
                    # Clear existing messages
                    self.chat_history.messages.clear()
                    
                    # Add messages to ChatHistory using official methods
                    for msg in history_data:
                        role = msg.get("role")
                        content = msg.get("content")
                        
                        if role == "system":
                            self.chat_history.add_system_message(content)
                        elif role == "user":
                            self.chat_history.add_user_message(content)
                        elif role == "assistant":
                            # Content is now a simple string
                            self.chat_history.add_assistant_message(content)
                else:
                    # Use simple message storage for fallback
                    self.messages.clear()
                    for msg in history_data:
                        role = msg.get("role")
                        content = msg.get("content")
                        
                        # Content is now a simple string, no need to extract from dict
                        self.messages.append({"role": role, "content": content})
                
                logging.info(f"Successfully loaded {len(history_data)} messages from session {self.session_id}")
            else:
                logging.info(f"No existing history found for session {self.session_id} after {max_retries} attempts")
                
        except Exception as e:
            logging.warning(f"Failed to load existing history: {e}")

    def add_system_message(self, content: str):
        """Add a system message to the chat history."""
        if HAVE_SK and self.chat_history:
            self.chat_history.add_system_message(content)
        else:
            self.messages.append({"role": "system", "content": content})

    def add_user_message(self, content: str):
        """Add a user message to the chat history."""
        if HAVE_SK and self.chat_history:
            self.chat_history.add_user_message(content)
        else:
            self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        """Add an assistant message to the chat history and save to Cosmos DB."""
        if HAVE_SK and self.chat_history:
            self.chat_history.add_assistant_message(content)
        else:
            self.messages.append({"role": "assistant", "content": content})
            
        if HAVE_DB:
            try:
                user_messages = self._get_user_messages()
                if user_messages:
                    last_user_message = user_messages[-1]["content"] if isinstance(user_messages[-1], dict) else user_messages[-1].content
                    save_turn(self.session_id, last_user_message, content)
                    logging.info(f"Saved conversation turn to Cosmos DB for session: {self.session_id}")
            except Exception as e:
                logging.warning(f"Failed to save turn to Cosmos DB: {e}")

    def _get_user_messages(self):
        """Get all user messages."""
        if HAVE_SK and self.chat_history:
            return [msg for msg in self.chat_history.messages if msg.role == AuthorRole.USER]
        else:
            return [msg for msg in self.messages if msg["role"] == "user"]

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages as a list of dictionaries."""
        if HAVE_SK and self.chat_history:
            messages = self.chat_history.messages[-count:] if count > 0 else self.chat_history.messages
            return [
                {
                    "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                    "content": msg.content
                }
                for msg in messages
            ]
        else:
            messages = self.messages[-count:] if count > 0 else self.messages
            return messages

    def get_formatted_history(self, max_pairs: int = 3) -> str:
        """Get formatted history for use in prompts."""
        if HAVE_SK and self.chat_history:
            messages = self.chat_history.messages
            if max_pairs > 0:
                messages = messages[-max_pairs * 2:]
            
            formatted = []
            for msg in messages:
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                formatted.append(f"{role.upper()}: {msg.content}")
            
            return "\n".join(formatted)
        else:
            messages = self.messages
            if max_pairs > 0:
                messages = messages[-max_pairs * 2:]
            
            formatted = []
            for msg in messages:
                formatted.append(f"{msg['role'].upper()}: {msg['content']}")
            
            return "\n".join(formatted)

    def clear_history(self):
        """Clear the chat history."""
        if HAVE_SK and self.chat_history:
            self.chat_history.messages.clear()
        else:
            self.messages.clear()
        
        if HAVE_DB:
            try:
                clear_session(self.session_id)
                logging.info(f"Cleared history for session: {self.session_id}")
            except Exception as e:
                logging.warning(f"Failed to clear session in Cosmos DB: {e}")

    def get_history_stats(self) -> Dict:
        """Get statistics about the chat history."""
        if HAVE_SK and self.chat_history:
            messages = self.chat_history.messages
            user_messages = [msg for msg in messages if msg.role == AuthorRole.USER]
            assistant_messages = [msg for msg in messages if msg.role == AuthorRole.ASSISTANT]
            system_messages = [msg for msg in messages if msg.role == AuthorRole.SYSTEM]
        else:
            messages = self.messages
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
            system_messages = [msg for msg in messages if msg["role"] == "system"]
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "system_messages": len(system_messages),
            "max_messages": self.max_messages,
            "needs_reduction": len(messages) > self.max_messages,
            "session_id": self.session_id,
            "cosmos_db_available": HAVE_DB,
            "semantic_kernel_available": HAVE_SK
        }

    def create_new_session(self) -> str:
        """Create a new session and return the new session ID."""
        new_session_id = self._generate_session_id()
        self.session_id = new_session_id
        
        if HAVE_SK:
            self.chat_history = ChatHistoryTruncationReducer(
                target_count=self.max_messages,
                auto_reduce=True
            )
        else:
            self.messages = []
        
        self.add_system_message("You are the Qatar University Assistant. Keep answers concise and helpful.")
        
        logging.info(f"Created new session: {new_session_id}")
        return new_session_id

    def get_chat_history_object(self):
        """Get the underlying Semantic Kernel ChatHistory object."""
        return self.chat_history

    async def reduce_history(self) -> bool:
        """Reduce history using Semantic Kernel's built-in reduction."""
        if HAVE_SK and self.chat_history:
            try:
                return await self.chat_history.reduce()
            except Exception as e:
                logging.warning(f"Failed to reduce history: {e}")
                return False
        return False
