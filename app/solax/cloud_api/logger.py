"""Compatibility entrypoint for the canonical SolaX polling service."""

from app.backend.services.solax_service import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
