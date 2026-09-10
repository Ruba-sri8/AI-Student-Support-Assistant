# AI Student Support Assistant

A small RAG-based student support assistant that answers questions using a local knowledge base and Ollama.

## Requirements

- Python 3.12
- Ollama installed locally
- A model such as `qwen:7b`

## Setup

1. Install Python 3.12.
2. Open PowerShell in this project folder.
3. Run:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```

4. Index the knowledge base:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m rag.index
```

5. Start the assistant:

```powershell
.\run_assistant.bat
```

## Notes

- If Ollama is not running or the model is missing, the app falls back to returning the retrieved context instead of crashing.
- The project is designed to be extended with more documents, more rules, and better retrieval logic.
