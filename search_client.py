# search_client.py
import os
from typing import List, Dict, Any

from dotenv import load_dotenv, find_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv(find_dotenv(), override=True)

ENDPOINT   = os.environ["AZURE_SEARCH_ENDPOINT"]
INDEX_NAME = os.environ["AZURE_SEARCH_INDEX"]
API_KEY    = os.environ["AZURE_SEARCH_KEY"]

_client = SearchClient(endpoint=ENDPOINT, index_name=INDEX_NAME,
                       credential=AzureKeyCredential(API_KEY))

def run_search(query: str, top: int = 5) -> List[Dict[str, Any]]:
    """
    Runs a simple full-text search against the index, returns a list of hits.
    Works with azure-search-documents 11.5.x (no query_language kwarg).
    """
    try:
        # Fall back to "*" if query is empty (avoid 400s)
        search_text = query.strip() or "*"

        results = _client.search(
            search_text=search_text,
            top=top,
            query_type="simple",        # supported on 11.5.x
            search_mode="any",
            include_total_count=False,
            highlight_fields="content",
            select=["metadata_storage_name", "metadata_storage_path", "content"],
        )

        hits: List[Dict[str, Any]] = []
        for r in results:
            # Prefer highlights if present
            highlights = None
            if "@search.highlights" in r and r["@search.highlights"]:
                highlights = r["@search.highlights"].get("content")

            snippet = " … ".join(highlights)[:2000] if highlights else (r.get("content") or "")[:2000]

            hits.append({
                "score":  r.get("@search.score"),
                "name":   r.get("metadata_storage_name"),
                "path":   r.get("metadata_storage_path"),
                "snippet": snippet,
            })
        return hits

    except Exception:
        # Never crash the chat if search hiccups
        return []
