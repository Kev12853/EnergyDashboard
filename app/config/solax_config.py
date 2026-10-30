"""SolaX inverter connection, polling, control and register configuration.

The poller and control service share these Modbus settings and register
mappings. ``DRY_RUN`` is the write interlock used by the Modbus service;
telemetry polling remains enabled when it is true.

Settings
--------
``COMMUNICATION_TIMEOUT`` is an integer number of seconds (default 1800)
before the poller reports a sustained local communication outage.
``SOLAX_HOST`` is the dongle hostname/IP (environment override, default
``192.168.1.67``); ``SOLAX_PORT`` is its TCP port (environment override,
default 502). ``POLL_INTERVAL_SECONDS`` is the control loop interval in
seconds (25); ``CONTROL_MAX_TELEMETRY_AGE_SECONDS`` is the maximum accepted
local sample age in seconds (90). ``DRY_RUN`` is a boolean, currently True,
that logs requested writes without sending Modbus write commands.

Read registers are the telemetry block offsets and work/manual mode holding
registers. ``WORK_MODE_WRITE_REGISTER`` (31) and
``MANUAL_MODE_WRITE_REGISTER`` (32) are the separate write addresses; keep
them distinct from the read addresses. Power values are watts, battery SOC
is percent, and ``SMART_FLEX_SOC_TARGET`` is a percentage point target.
"""
import os

COMMUNICATION_TIMEOUT = 1800  # seconds without local Modbus success before outage notification
SOLAX_HOST = os.getenv("SOLAX_HOST", "192.168.1.67")  # Modbus TCP dongle host; environment override
SOLAX_PORT = int(os.getenv("SOLAX_PORT", "502"))  # Modbus TCP port; environment override
POLL_INTERVAL_SECONDS = 25  # control-loop interval in seconds
CONTROL_MAX_TELEMETRY_AGE_SECONDS = 90  # maximum local sample age accepted for control
DRY_RUN = True  # when true, write_work_mode logs requests and sends no Modbus writes


# Inverter Read registers
# Register Data Locations
WORK_MODE_REGISTER = 0x008B  # holding-register read address
MANUAL_MODE_REGISTER = 0x008C  # adjacent holding-register read address

WORK_MODE_WRITE_REGISTER = 31  # write address; distinct from read register
MANUAL_MODE_WRITE_REGISTER = 32  # write address; distinct from read register

REGISTER_BLOCK_START = 0  # first input register in the telemetry block
REGISTER_BLOCK_SIZE = 80  # number of consecutive input registers read

INVERTER_POWER = 2  # signed 16-bit AC output power, watts

PV1_POWER = 10  # PV string 1 power, watts
PV2_POWER = 11  # PV string 2 power, watts

BATTERY_POWER = 22  # signed 16-bit battery power, watts
BATTERY_SOC = 28  # battery state of charge, percent

GRID_LSB = 70  # low word of signed 32-bit grid power, watts
GRID_MSB = 71  # high word of signed 32-bit grid power, watts

#FORCED_DISCHARE = 140

SMART_FLEX_SOC_TARGET = 80  # percent SOC at/above which Smart Flex will not start charging
