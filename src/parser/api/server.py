from __future__ import annotations

import uvicorn

from parser.api.main import app, mount_frontend
from parser.config import find_project_root


def main() -> None:
    mount_frontend()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
