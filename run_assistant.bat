@echo off
cd /d "%~dp0"
set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    echo Python 3.12 was not found at %PYTHON_EXE%
    echo Please install Python 3.12 first from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

echo Indexing knowledge base...
"%PYTHON_EXE%" -m rag.index

echo Starting student support assistant...
"%PYTHON_EXE%" -m assistant.main
