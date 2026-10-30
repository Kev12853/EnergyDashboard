"""Resolve shared application data and log paths without hiding old databases.

``ENERGY_DASHBOARD_DB`` selects an explicit SQLite file;
``ENERGY_DASHBOARD_DATA_DIR`` selects the data directory and, unless the DB
file is explicitly configured, its ``energy_dashboard.db`` child;
``ENERGY_DASHBOARD_LOG_DIR`` selects the log directory. Defaults are rooted
under the project checkout, with known legacy database locations considered
before selecting the new data-directory default. Values are filesystem paths,
not credentials.
"""
import os
import platform
from pathlib import Path


def resolve_paths(project_root, platform_name=None, environ=None, home=None):
    """Return (data_dir, log_dir, db_path), preserving known legacy DBs.

    Explicit DB configuration wins. Without it, an existing legacy database
    is retained. If both legacy and new default databases exist, fail loudly
    instead of silently choosing one and splitting application state.

    Args:
        project_root: Checkout root used to form the new ``data`` default.
        platform_name: Optional OS name, useful for selecting/testing legacy
            candidates; defaults to the current platform.
        environ: Environment mapping containing the three path overrides.
        home: Home directory used to locate the legacy Windows database.

    Returns:
        ``(data_dir, log_dir, db_path)`` as expanded ``Path`` objects. The
        function does not create directories or a database.

    Raises:
        RuntimeError: If both a new and known legacy database already exist
            and no explicit database path resolves the ambiguity.
    """
    root = Path(project_root).expanduser()
    platform_name = platform_name or platform.system()
    env = os.environ if environ is None else environ
    home = Path(home or Path.home()).expanduser()
    data_override = env.get("ENERGY_DASHBOARD_DATA_DIR")
    db_override = env.get("ENERGY_DASHBOARD_DB")
    log_dir = Path(env.get("ENERGY_DASHBOARD_LOG_DIR", root / "logs")).expanduser()

    if db_override:
        db_path = Path(db_override).expanduser()
        data_dir = Path(data_override).expanduser() if data_override else db_path.parent
        return data_dir, log_dir, db_path

    if data_override:
        data_dir = Path(data_override).expanduser()
        return data_dir, log_dir, data_dir / "energy_dashboard.db"

    new_data_dir = root / "data"
    new_db = new_data_dir / "energy_dashboard.db"
    legacy_candidates = []
    if platform_name == "Windows":
        legacy_candidates.append(home / "OffLine Documents" / "EnergyDashboard" / "data" / "energy_dashboard.db")
    elif platform_name == "Linux":
        legacy_candidates.append(root / "app" / "data" / "energy_dashboard.db")

    candidates = []
    for candidate in [new_db, *legacy_candidates]:
        resolved = candidate.resolve(strict=False)
        if resolved not in candidates and resolved.is_file():
            candidates.append(resolved)
    if len(candidates) > 1:
        raise RuntimeError(
            "Multiple EnergyDashboard databases exist. Set ENERGY_DASHBOARD_DB "
            "to the intended existing database explicitly: "
            + ", ".join(str(path) for path in candidates)
        )
    if candidates:
        db_path = candidates[0]
        data_dir = db_path.parent
    else:
        data_dir = new_data_dir
        db_path = new_db
    return data_dir, log_dir, db_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR, LOG_DIR, DB_PATH = resolve_paths(PROJECT_ROOT)

if platform.system() not in {"Windows", "Linux", "Darwin"}:
    raise RuntimeError(f"Unsupported operating system: {platform.system()}")
