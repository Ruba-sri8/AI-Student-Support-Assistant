import json
from pathlib import Path


class MemoryStore:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = Path(__file__).resolve().parents[1] / "data" / memory_file
        self.memory_file.parent.mkdir(exist_ok=True)

    def load(self):
        if not self.memory_file.exists():
            return []
        try:
            with self.memory_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
        return []

    def save(self, history):
        with self.memory_file.open("w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)

    def add(self, question, answer):
        history = self.load()
        history.append({"question": question, "answer": answer})
        self.save(history)

    def recent(self, limit=5):
        history = self.load()
        return history[-limit:]
