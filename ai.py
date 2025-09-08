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

    # Build short, grounded context from search
    lines = []
    for i, h in enumerate(hits, start=1):
        snippet = (h.get("snippet") or "").replace("\n", " ")
        lines.append(f"[{i}] {h.get('name')}: {snippet}")
    context = "\n".join(lines) if lines else "No results."

    system = (
        "You are a Qatar University admissions assistant. "
        "Answer STRICTLY from the provided context. "
        "If the answer is not present, say: "
        "'I don't know from the indexed admissions documents yet.' "
        "Be concise and include sources like [1], [2] when possible."
    )
    user = f"Question: {query}\n\nContext:\n{context}"

    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    answer = resp.choices[0].message.content
    sources = [{"id": i, "name": h["name"], "path": h["path"]} for i, h in enumerate(hits, 1)]
    return {"answer": answer, "sources": sources}
