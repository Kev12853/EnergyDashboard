"""Compatibility entrypoint for the canonical SolaX polling service."""

from app.solax.backend.services import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
