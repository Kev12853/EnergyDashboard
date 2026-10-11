import platform
from pathlib import Path


if platform.system() == "Windows":
    DATA_DIR = (
        Path.home()
        / "OffLine Documents"
        / "EnergyDashboard"
        / "data"
    )

    LOG_DIR = (
        Path.home()
        / "OffLine Documents"
        / "EnergyDashboard"
        / "logs"
    )

elif platform.system() == "Linux":
    DATA_DIR = Path("/home/kevin/EnergyDashboard/app/data")
    LOG_DIR = Path("/home/kevin/EnergyDashboard/logs")

else:
    raise RuntimeError(
        f"Unsupported operating system: {platform.system()}"
    )


DB_PATH = DATA_DIR / "energy_dashboard.db"