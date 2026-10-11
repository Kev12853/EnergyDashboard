from app.solax.backend.storage.service_heartbeat_repository import (
    ServiceHeartbeatRepository,
)


class SystemRepository(ServiceHeartbeatRepository):
    """Compatibility alias for the former NiceGUI-local repository."""
