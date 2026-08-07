"""Compatibility entrypoint for the canonical Octopus service."""

from app.backend.services.octopus_service import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
