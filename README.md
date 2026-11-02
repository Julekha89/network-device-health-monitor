# Network Device Health Monitor

A lightweight, cross-platform Python network availability monitor for infrastructure operations and NOC workflows. It checks configured devices using ICMP ping, displays availability, and records timestamped results in CSV for incident review.

> **Portfolio project:** Built as a demonstration of network monitoring automation. It does not contain proprietary network data or represent a production deployment.

## Features
- Configurable device inventory in JSON
- Concurrent device checks using Python's thread pool
- `UP`, `DOWN`, and `ERROR` status reporting
- UTC timestamps and append-only CSV reporting
- Configurable interval, timeout, and concurrency
- Windows and Linux/macOS ping support
- Unit tests and GitHub Actions CI
- No third-party Python dependencies

## Architecture

```text
config/devices.json
       |
       v
  Python scheduler --> Concurrent ICMP checks --> Terminal status
                                               --> CSV availability log
```

## Quick start

Requires **Python 3.10+** and an available system `ping` command.

```bash
python -m src.monitor --config config/devices.json --interval 0
```

For continuous monitoring every five minutes:

```bash
python -m src.monitor --interval 300 --timeout 2 --workers 10
```

Edit `config/devices.json` to add hosts you own or are authorized to monitor. By default, the sample inventory contains localhost and a public DNS resolver; replace the latter for isolated labs.

Results are appended to `reports/availability.csv`:

```csv
timestamp_utc,device,host,status,latency_ms,error
2026-01-01T10:00:00+00:00,Localhost,127.0.0.1,UP,2.3,
```

The CSV line above is **illustrative**, not a captured measurement.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Repository structure

```text
src/monitor.py             CLI and monitoring implementation
config/devices.json        Example inventory
tests/test_monitor.py       Unit tests
.github/workflows/ci.yml   CI checks
.gitignore                 Excludes generated reports and local files
```

## Operational considerations

- ICMP reachability does not establish application health; some healthy devices block ICMP.
- Latency is local command execution time, **not** the packet RTT reported by ping.
- Device checks can time out and may require OS-specific ICMP permissions.
- The monitor runs in the foreground; for unattended operation, use a service manager or scheduled task.
- No alerting, persistence database, or dashboard is included in this version.

## Roadmap
- Parse ICMP round-trip time from ping output
- Add state-change alerts and outage duration metrics
- Add SNMP interface monitoring and optional dashboard
- Containerization and structured logging

## Skills demonstrated
Python, network operations, ICMP, monitoring automation, concurrent execution, CSV reporting, testing, and CI.

## License
MIT License. See `LICENSE`.
