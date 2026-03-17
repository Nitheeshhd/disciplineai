$env:PYTHONPATH = (Get-Location).Path
& ".\env\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
