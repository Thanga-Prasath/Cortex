@echo off
REM Check if .venv exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

REM Keep the window open with the environment activated
echo Virtual Environment Activated.
cmd /k
