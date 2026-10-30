"""Hold settings for the standalone Modbus register scanner, including connection target, device identifier, scan range, request delay, interval and output filename. These scanner values are separate from the main poller configuration."""

HOST = "192.168.1.67"  # scanner target Modbus host

PORT = 502  # scanner target TCP port

DEVICE_ID = 1  # Modbus unit/device identifier

START_REGISTER = 0  # first register address included in scan
END_REGISTER = 800  # exclusive upper bound used by scanner

BLOCK_SIZE = 1  # registers requested per scan operation

REQUEST_DELAY = 0.50  # delay between requests, seconds

SCAN_INTERVAL = 30  # interval between complete scans, seconds

OUTPUT = "scan.csv"  # scanner output filename
