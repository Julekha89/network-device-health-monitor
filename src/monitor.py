"""Concurrent ICMP availability monitor using the operating system ping utility."""
from __future__ import annotations
import argparse
import csv
import json
import platform
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HOST_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,252}$')
FIELDS = ['timestamp_utc', 'device', 'host', 'status', 'latency_ms', 'error']


def load_devices(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list) or not data:
        raise ValueError('Configuration must contain a nonempty JSON list')
    devices = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not isinstance(item.get('host'), str):
            raise ValueError('Every device needs string name and host fields')
        if not HOST_RE.fullmatch(item['host']) or item['host'].startswith('-'):
            raise ValueError(f"Invalid host: {item['host']!r}")
        devices.append({'name': item['name'], 'host': item['host']})
    return devices


def ping_device(device: dict[str, str], timeout: float = 2.0) -> dict[str, str | float | None]:
    windows = platform.system().lower() == 'windows'
    command = ['ping', '-n' if windows else '-c', '1', device['host']]
    start = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        elapsed = round((time.monotonic() - start) * 1000, 2)
        status = 'UP' if result.returncode == 0 else 'DOWN'
        error = '' if status == 'UP' else 'Ping returned nonzero exit status'
    except subprocess.TimeoutExpired:
        status, elapsed, error = 'DOWN', None, 'Ping timed out'
    except OSError as exc:
        status, elapsed, error = 'ERROR', None, str(exc)
    return {'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'device': device['name'], 'host': device['host'], 'status': status,
            'latency_ms': elapsed, 'error': error}


def write_report(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open('a', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def run_once(devices: list[dict[str, str]], report: Path, timeout: float, workers: int) -> list[dict]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda device: ping_device(device, timeout), devices))
    write_report(report, rows)
    for row in rows:
        print(f"{row['timestamp_utc']} | {row['device']:<18} | {row['host']:<18} | {row['status']}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description='Monitor device availability using ICMP ping')
    parser.add_argument('--config', type=Path, default=Path('config/devices.json'))
    parser.add_argument('--output', type=Path, default=Path('reports/availability.csv'))
    parser.add_argument('--interval', type=int, default=300, help='Seconds between checks; 0 = one check')
    parser.add_argument('--timeout', type=float, default=2.0)
    parser.add_argument('--workers', type=int, default=10)
    args = parser.parse_args()
    if args.interval < 0 or args.timeout <= 0 or args.workers < 1:
        parser.error('interval must be >= 0, timeout > 0, and workers >= 1')
    devices = load_devices(args.config)
    try:
        while True:
            run_once(devices, args.output, args.timeout, args.workers)
            if args.interval == 0:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nMonitoring stopped.')


if __name__ == '__main__':
    main()
