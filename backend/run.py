"""Run the Karya API server.

    python run.py            # serve on http://127.0.0.1:8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("karya.planes.interface.app:app", host="127.0.0.1", port=8000, reload=False)
