import os
from dotenv import load_dotenv, find_dotenv
from openai import AzureOpenAI
from search_client import run_search

load_dotenv(find_dotenv(), override=True)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01"),
)
DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

def answer_question(query: str, top: int = 5):
    hits = run_search(query, top)

    lines = []
    for i, h in enumerate(hits, start=1):
        snippet = (h.get("snippet") or "").replace("\n", " ")
        lines.append(f"[{i}] {h.get('name')}: {snippet}")
    context = "\n".join(lines) if lines else "No results."

    # Enhanced system prompt for more conversational and intelligent responses
    system = (
        "You are a friendly and helpful Qatar University admissions assistant. "
        "Your primary role is to help students with Qatar University admissions, programs, and general information. "
        
        "For Qatar University-related questions (admissions, programs, requirements, deadlines, fees, etc.): "
        "- Use the provided context from the indexed documents to give accurate, detailed answers "
        "- Include source references like [1], [2] when citing specific information "
        "- If the context doesn't contain the answer, say: 'I don't have specific information about that in the current documents. Please contact Qatar University admissions directly for the most up-to-date information.' "
        
        "For general conversation (greetings, casual questions, etc.): "
        "- Be warm, friendly, and conversational "
        "- Briefly introduce yourself as the QU admissions assistant "
        "- Gently steer the conversation toward how you can help with Qatar University questions "
        "- Keep responses natural and engaging "
        
        "Always maintain a helpful, professional, and encouraging tone. "
        "Be concise but informative. Make the user feel welcome and supported."
    )
    user = f"Question: {query}\n\nContext:\n{context}"

    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        temperature=0.7,  # Slightly higher temperature for more natural responses
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    answer = resp.choices[0].message.content
    sources = [{"id": i, "name": h["name"], "path": h["path"]} for i, h in enumerate(hits, 1)]
    return {"answer": answer, "sources": sources}
