import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.index import get_vector_store


def load_settings():
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    with settings_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_context(question, top_k=3):
    """Retrieve relevant text chunks based on the student's question."""
    settings = load_settings()
    store = get_vector_store(settings["db_path"])

    if not store.documents:
        return "No indexed context is available yet. Please run the indexing script first."

    results = store.similarity_search(question, k=top_k)
    context_chunks = [doc.page_content for doc in results]

    if not context_chunks:
        return "No relevant context found in the knowledge base."

    return "\n\n---\n\n".join(context_chunks)


if __name__ == "__main__":
    question = input("Ask a question: ")
    print(get_context(question))
