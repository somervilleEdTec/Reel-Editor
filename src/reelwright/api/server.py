"""Run local API: python -m reelwright.api.server"""

from __future__ import annotations

import uvicorn


def main():
    # Loopback only — never bind 0.0.0.0; API has no auth by design.
    uvicorn.run("reelwright.api.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
