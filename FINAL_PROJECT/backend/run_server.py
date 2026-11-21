import os
import sys
import uvicorn

if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_dir)
    print("Starting uvicorn server on http://127.0.0.1:8000 ...", flush=True)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
