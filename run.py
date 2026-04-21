import os

import uvicorn


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    reload_enabled = os.environ.get("RELOAD", "true").lower() in {"1", "true", "yes"}
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
