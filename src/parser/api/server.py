from __future__ import annotations

import os

import uvicorn

from parser.api.main import app, mount_frontend


def main() -> None:
    mount_frontend()
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
