import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import scrolledtext, ttk

import ollama

from assistant.memory import MemoryStore
from rag.query import get_context


def load_settings():
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    with settings_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_question(text):
    cleaned = text.lower()
    cleaned = cleaned.replace("?", " ")
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch.isspace())
    return set(cleaned.split())


def extract_focused_answer(question, context):
    q_tokens = normalize_question(question)
    blocks = context.split("\n\n---\n\n")

    for block in blocks:
        if "Q:" in block and "A:" in block:
            q_part, a_part = block.split("A:", 1)
            q_text = q_part.lower().replace("q:", "").strip()
            q_text_tokens = normalize_question(q_text)
            overlap = q_tokens & q_text_tokens
            if overlap or q_tokens.issubset(q_text_tokens) or q_text_tokens.issubset(q_tokens):
                return a_part.strip().replace("\n", " ")

    for block in blocks:
        if any(word in block.lower() for word in question.lower().split() if len(word) > 3):
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            answer_lines = [line for line in lines if line.startswith("A:")]
            if answer_lines:
                return answer_lines[0].replace("A:", "").strip()

    if context.strip():
        sentences = [line.strip() for line in context.splitlines() if line.strip()]
        for sentence in sentences:
            if any(word in sentence.lower() for word in question.lower().split() if len(word) > 2):
                return sentence

    return "I couldn’t find a direct answer in the knowledge base for that question."


def ask_student_bot(question):
    settings = load_settings()
    context = get_context(question)
    memory = MemoryStore()

    user_message = (
        f"Question: {question}\n\n"
        f"Context from knowledge base:\n{context}\n\n"
        "Answer clearly and helpfully."
    )

    try:
        response = ollama.chat(
            model=settings["model_name"],
            messages=[
                {"role": "system", "content": settings["system_prompt"]},
                {"role": "user", "content": user_message},
            ],
        )
        answer = response["message"]["content"]
    except Exception:
        answer = extract_focused_answer(question, context)

    memory.add(question, answer)
    return answer


def ask_student_bot_with_fallback(question):
    try:
        return ask_student_bot(question)
    except Exception:
        context = get_context(question)
        return extract_focused_answer(question, context)


class StudentSupportApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Student Support Assistant")
        self.geometry("900x620")
        self.minsize(780, 500)
        self.configure(bg="#edf2f7")

        self.memory = MemoryStore()
        self.history = self.memory.load()

        self.left_panel = tk.Frame(self, bg="#dfeaf5", width=240)
        self.left_panel.pack(side="left", fill="y", padx=(18, 10), pady=18)

        title = tk.Label(
            self.left_panel,
            text="Recent Questions",
            font=("Segoe UI", 13, "bold"),
            bg="#dfeaf5",
            fg="#0f172a",
        )
        title.pack(pady=(12, 6))

        self.history_list = tk.Listbox(
            self.left_panel,
            font=("Segoe UI", 10),
            bg="#f8fbff",
            fg="#0f172a",
            relief="flat",
            height=24,
            activestyle="none",
        )
        self.history_list.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.history_list.bind("<<ListboxSelect>>", self.load_selected_question)

        self.populate_history()

        self.main_panel = tk.Frame(self, bg="#edf2f7")
        self.main_panel.pack(side="right", fill="both", expand=True, padx=(0, 18), pady=18)

        header = tk.Label(
            self.main_panel,
            text="Student Support Assistant",
            font=("Segoe UI", 22, "bold"),
            bg="#edf2f7",
            fg="#111827",
            anchor="w",
        )
        header.pack(fill="x", pady=(0, 10))

        subtitle = tk.Label(
            self.main_panel,
            text="Ask about syllabus, regulations, FAQs, notices, and exam policies.",
            font=("Segoe UI", 10),
            bg="#edf2f7",
            fg="#475569",
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(0, 12))

        input_row = tk.Frame(self.main_panel, bg="#edf2f7")
        input_row.pack(fill="x", pady=(0, 12))

        self.question_var = tk.StringVar()
        self.question_entry = tk.Entry(
            input_row,
            textvariable=self.question_var,
            font=("Segoe UI", 12),
            bd=1,
            relief="solid",
            width=60,
        )
        self.question_entry.pack(side="left", fill="x", expand=True)
        self.question_entry.bind("<Return>", self.ask_current_question)

        ask_btn = ttk.Button(input_row, text="Ask", command=self.ask_current_question)
        ask_btn.pack(side="left", padx=(8, 0))

        self.response_area = scrolledtext.ScrolledText(
            self.main_panel,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#1f2937",
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
            height=20,
        )
        self.response_area.pack(fill="both", expand=True)
        self.response_area.configure(state="disabled")
        self.response_area.insert(tk.END, "Welcome! Ask a question to get help with student support information.\n")
        self.response_area.configure(state="disabled")

        self.question_entry.focus_set()

    def populate_history(self):
        self.history_list.delete(0, tk.END)
        for item in self.history[-10:][::-1]:
            question = item.get("question", "")
            if question:
                self.history_list.insert(tk.END, question)

    def load_selected_question(self, event=None):
        selection = self.history_list.curselection()
        if not selection:
            return
        question = self.history_list.get(selection[0])
        self.question_var.set(question)

    def ask_current_question(self, event=None):
        question = self.question_var.get().strip()
        if not question:
            self.show_message("Please enter a question first.")
            return

        self.show_message(f"You: {question}\n")
        answer = ask_student_bot_with_fallback(question)
        self.show_message(f"Assistant: {answer}\n")
        self.question_var.set("")
        self.refresh_history()

    def show_message(self, message):
        self.response_area.configure(state="normal")
        self.response_area.insert(tk.END, message)
        self.response_area.see(tk.END)
        self.response_area.configure(state="disabled")

    def refresh_history(self):
        self.history = self.memory.load()
        self.populate_history()


def interactive_session():
    print("Student Support Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Ask a question: ").strip()
        if not question:
            print("Please enter a question.\n")
            continue
        if question.lower() in {"exit", "quit", "bye"}:
            print("Goodbye!")
            break

        answer = ask_student_bot_with_fallback(question)
        print("\nAnswer:\n")
        print(answer)
        print("\n")


def launch_gui():
    app = StudentSupportApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        launch_gui()
    except Exception:
        print("Desktop GUI not available in this environment. Starting terminal mode...\n")
        interactive_session()
