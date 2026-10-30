# SolaX background services

Run the monitoring poller and inverter control loop as separate processes from
the repository root, using the same Python environment and database:

```sh
python -m app.solax.backend.polling.solax_service
python -m app.solax.backend.services.control_service
```

Both services use `app.connections.connection.get_connection()`, which resolves
the shared database through `app.config.project_paths.DB_PATH`, enables SQLite
WAL and uses a 30 second busy timeout. Configure the same path for both
processes:

- `ENERGY_DASHBOARD_DB` selects the complete database filename and takes
  precedence over the data directory setting.
- `ENERGY_DASHBOARD_DATA_DIR` selects the directory; the database filename is
  `energy_dashboard.db`.
- `ENERGY_DASHBOARD_LOG_DIR` selects the log directory.

For example, on Linux set absolute paths in the environment shared by both
processes:

```sh
export ENERGY_DASHBOARD_DB=/srv/energy-dashboard/data/energy_dashboard.db
export ENERGY_DASHBOARD_DATA_DIR=/srv/energy-dashboard/data
export ENERGY_DASHBOARD_LOG_DIR=/var/log/energy-dashboard
```

When `ENERGY_DASHBOARD_DB` is set, it is the authoritative SQLite file path;
use the same value for both processes. Prefer absolute paths so service
working-directory differences cannot select another file.

Without overrides, the repository root's `data/` and `logs/` directories are
used. On Windows, the previous data path was
`%USERPROFILE%/OffLine Documents/EnergyDashboard/data/energy_dashboard.db`; the
new default resolves to the repository root's `data/energy_dashboard.db`.
These are the same path when the checkout is in that conventional location.
On Linux, the previous path was `/home/kevin/EnergyDashboard/app/data/` and the
new default is `/home/kevin/EnergyDashboard/data/` when the repository root is
`/home/kevin/EnergyDashboard`. If only the old database exists, startup keeps
using it. If both old and new databases exist, startup raises an error and
requires `ENERGY_DASHBOARD_DB` to select the intended file; it will not silently
create or switch to a second database.

The inverter defaults remain configured locally; override the host and port
with `SOLAX_HOST` and `SOLAX_PORT` if required.

`Poller` records local Modbus snapshots and cloud monitoring samples, its own
heartbeat and outage notifications. It never evaluates automation or invokes a
write method. `SolaX Control` independently reads fresh local Modbus telemetry,
evaluates schedules and reconciles `inverter_state`; its heartbeat is stored
under the distinct `SolaX Control` identity. Cloud samples are not read by the
control loop. Keep `DRY_RUN = True` in `app/config/solax_config.py` until a
separate, deliberate commissioning change is made.

Octopus dispatch records and vehicle state are read from the shared SQLite
database. A successful dispatch query, including a valid empty result, records
its own timestamp in `octopus_data_status`; control also checks the Octopus
service heartbeat. Missing tables, query failures, or stale timestamps make
dispatch data unavailable. Unavailable dispatch data cannot start Smart Flex
or unwind an existing Smart Flex request. Vehicle status must also be current
to start Force Charge. A persisted active request remains latched through a
control-service restart while the current dispatch is still active.

No systemd unit is included because this repository does not establish the
deployment user's installation path, virtualenv path, or service account. A
deployment can use the two module commands above as separate `ExecStart`
commands with the same working directory and environment file.
