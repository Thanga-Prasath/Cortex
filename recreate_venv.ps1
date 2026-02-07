# Remove old virtual environments if they exist
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force ".venv"
}
if (Test-Path ".venv_old") {
    Remove-Item -Recurse -Force ".venv_old"
}
# Create new virtual environment
python -m venv .venv
