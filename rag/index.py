import json
import re
from pathlib import Path


class SimpleDocument:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


class SimpleVectorStore:
    def __init__(self, persist_directory):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_file = self.persist_directory / "index.json"
        self.documents = self._load_documents()

    def reset(self):
        self.documents = []
        self._save_documents()

    def _load_documents(self):
        if not self.index_file.exists():
            return []

        try:
            with self.index_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError:
            return []

        documents = []
        for item in payload:
            documents.append(SimpleDocument(item["content"], {"source": item.get("source", "unknown")}))
        return documents

    def _save_documents(self):
        payload = [
            {"source": doc.metadata.get("source", "unknown"), "content": doc.page_content}
            for doc in self.documents
        ]
        with self.index_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    def add_documents(self, doc_list):
        self.documents.extend(doc_list)
        self._save_documents()

    def similarity_search(self, query, k=3):
        normalized_query = normalize_text(query)
        query_terms = {term for term in normalized_query.split() if len(term) > 2}

        if not query_terms:
            return self.documents[:k]

        scored = []
        for doc in self.documents:
            document_text = normalize_text(doc.page_content)
            score = 0
            for term in query_terms:
                score += document_text.count(term)
            scored.append((score, doc))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top_matches = [doc for _, doc in scored[:k] if doc.page_content.strip()]
        return top_matches if top_matches else self.documents[:k]


def normalize_text(text):
    return re.sub(r"[^a-z0-9\s]", " ", str(text).lower())


def split_text(text, chunk_size=500, overlap=100):
    text = text.strip()
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n+", text)
    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if not current:
            current = paragraph
            continue

        if len(current) + 1 + len(paragraph) <= chunk_size:
            current = current + "\n\n" + paragraph
        else:
            chunks.append(current)
            current = paragraph[:chunk_size]

    if current:
        chunks.append(current)

    merged = []
    for index, chunk in enumerate(chunks):
        if index == 0:
            merged.append(chunk)
            continue
        previous = merged[-1]
        cutoff = max(0, len(chunk) - overlap)
        merged.append(previous[-overlap:] + chunk if overlap and len(previous) >= overlap else chunk)

    return merged


def load_settings():
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    with settings_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_documents(data_dir):
    documents = []
    for file_path in sorted(Path(data_dir).glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        documents.append({"source": str(file_path.name), "content": text})
    return documents


def index_documents():
    settings = load_settings()
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / settings["knowledge_base_dir"]
    db_path = base_dir / settings["db_path"]

    docs = load_documents(data_dir)
    if not docs:
        raise FileNotFoundError(f"No .txt knowledge files found in {data_dir}")

    store = SimpleVectorStore(db_path)
    store.reset()
    chunks = []
    for doc in docs:
        for chunk in split_text(doc["content"], chunk_size=500, overlap=100):
            chunks.append(SimpleDocument(chunk, {"source": doc["source"]}))

    store.add_documents(chunks)
    return store


def get_vector_store(db_path=None):
    settings = load_settings()
    if db_path is None:
        db_path = Path(__file__).resolve().parents[1] / settings["db_path"]
    else:
        db_path = Path(db_path)

    return SimpleVectorStore(db_path)


if __name__ == "__main__":
    index_documents()
    print("Knowledge base indexed successfully.")
