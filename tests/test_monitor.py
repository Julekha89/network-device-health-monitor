import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.monitor import load_devices, ping_device, write_report


class MonitorTests(unittest.TestCase):
    def test_load_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'devices.json'
            path.write_text(json.dumps([{'name': 'Lab', 'host': '127.0.0.1'}]))
            self.assertEqual(load_devices(path)[0]['host'], '127.0.0.1')

    def test_reject_invalid_host(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'devices.json'
            path.write_text(json.dumps([{'name': 'Unsafe', 'host': '-bad'}]))
            with self.assertRaises(ValueError):
                load_devices(path)

    @patch('src.monitor.subprocess.run')
    def test_ping_success(self, run):
        run.return_value.returncode = 0
        result = ping_device({'name': 'Router', 'host': '127.0.0.1'})
        self.assertEqual(result['status'], 'UP')
        self.assertEqual(run.call_args.kwargs['check'], False)

    @patch('src.monitor.subprocess.run')
    def test_ping_failure(self, run):
        run.return_value.returncode = 1
        self.assertEqual(ping_device({'name': 'Router', 'host': '127.0.0.1'})['status'], 'DOWN')

    def test_csv_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.csv'
            row = {'timestamp_utc': '2026-01-01T00:00:00+00:00', 'device': 'Lab', 'host': '127.0.0.1', 'status': 'UP', 'latency_ms': 1.0, 'error': ''}
            write_report(path, [row])
            write_report(path, [row])
            self.assertEqual(len(path.read_text().splitlines()), 3)


if __name__ == '__main__':
    unittest.main()
