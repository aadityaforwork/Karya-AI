"""Run the Karya API server.

    python run.py            # serve on http://127.0.0.1:8000

On a host that sets $PORT (Render, Railway, etc.) we bind 0.0.0.0:$PORT so the
platform can route to us; locally we keep the loopback default.
"""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    uvicorn.run("karya.planes.interface.app:app", host=host, port=port, reload=False)
