"""
Unit tests for HealthMonitor.

Validates: Requirements 7.4
WHEN the API fails 3 consecutive times, Health_Monitor SHALL mark status as "unhealthy"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import threading
import unittest
from unittest.mock import patch, MagicMock, call
import requests

from interface.health_monitor import HealthMonitor, HealthStatus


class TestHealthMonitorUnhealthyAfterThreeFailures(unittest.TestCase):
    """Tests for Requirement 7.4: mark unhealthy after 3 consecutive failures."""

    def _make_failing_response(self, status_code=500):
        mock = MagicMock()
        mock.status_code = status_code
        return mock

    def test_not_unhealthy_after_one_failure(self):
        """One failure should not mark the monitor as unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 1)

    def test_not_unhealthy_after_two_failures(self):
        """Two consecutive failures should not yet mark the monitor as unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 2)

    def test_unhealthy_after_three_consecutive_failures(self):
        """Three consecutive failures must mark the monitor as unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertFalse(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 3)

    def test_unhealthy_after_three_timeout_failures(self):
        """Three consecutive Timeout exceptions must also mark the monitor as unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch(
            "interface.health_monitor.requests.get",
            side_effect=requests.exceptions.Timeout,
        ):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertFalse(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 3)

    def test_unhealthy_after_three_connection_errors(self):
        """Three consecutive ConnectionError exceptions must mark the monitor as unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch(
            "interface.health_monitor.requests.get",
            side_effect=requests.exceptions.ConnectionError("refused"),
        ):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertFalse(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 3)

    def test_still_unhealthy_after_more_than_three_failures(self):
        """More than three failures should keep the monitor unhealthy."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            for _ in range(5):
                monitor._check_health()

        status = monitor.get_status()
        self.assertFalse(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 5)


class TestHealthMonitorFailureCounterReset(unittest.TestCase):
    """Tests that the failure counter resets to 0 on a successful response."""

    def _make_success_response(self):
        mock = MagicMock()
        mock.status_code = 200
        return mock

    def _make_failing_response(self):
        mock = MagicMock()
        mock.status_code = 500
        return mock

    def test_counter_resets_after_success_following_failures(self):
        """After some failures, a successful check must reset the counter to 0."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            monitor._check_health()
            monitor._check_health()

        self.assertEqual(monitor.get_status().consecutive_failures, 2)

        with patch("interface.health_monitor.requests.get", return_value=self._make_success_response()):
            monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 0)

    def test_counter_resets_after_recovery_from_unhealthy(self):
        """A success after being unhealthy must reset the counter and restore healthy status."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_failing_response()):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        self.assertFalse(monitor.get_status().is_healthy)

        with patch("interface.health_monitor.requests.get", return_value=self._make_success_response()):
            monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 0)

    def test_counter_stays_zero_on_repeated_successes(self):
        """Repeated successes should keep the counter at 0."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        with patch("interface.health_monitor.requests.get", return_value=self._make_success_response()):
            for _ in range(5):
                monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 0)


class TestHealthMonitorThreadSafety(unittest.TestCase):
    """Tests that _status is accessed under _lock."""

    def test_get_status_acquires_lock(self):
        """get_status() must acquire _lock before reading _status."""
        monitor = HealthMonitor(check_url="https://example.com/getLive")

        lock_acquired_during_read = []
        original_enter = monitor._lock.__class__.__enter__

        # Track whether the lock is held when _status is accessed inside get_status
        real_lock = monitor._lock

        acquired_events = []

        class TrackingLock:
            def __enter__(self_inner):
                acquired_events.append("acquired")
                return real_lock.__enter__()

            def __exit__(self_inner, *args):
                return real_lock.__exit__(*args)

        monitor._lock = TrackingLock()
        monitor.get_status()

        self.assertIn("acquired", acquired_events, "Lock was not acquired during get_status()")

    def test_check_health_acquires_lock_on_success(self):
        """_check_health() must acquire _lock when updating status on success."""
        monitor = HealthMonitor(check_url="https://example.com/getLive")

        real_lock = monitor._lock
        acquired_events = []

        class TrackingLock:
            def __enter__(self_inner):
                acquired_events.append("acquired")
                return real_lock.__enter__()

            def __exit__(self_inner, *args):
                return real_lock.__exit__(*args)

        monitor._lock = TrackingLock()

        success_response = MagicMock()
        success_response.status_code = 200

        with patch("interface.health_monitor.requests.get", return_value=success_response):
            monitor._check_health()

        self.assertGreater(len(acquired_events), 0, "Lock was not acquired during _check_health() on success")

    def test_check_health_acquires_lock_on_failure(self):
        """_check_health() must acquire _lock when updating status on failure."""
        monitor = HealthMonitor(check_url="https://example.com/getLive")

        real_lock = monitor._lock
        acquired_events = []

        class TrackingLock:
            def __enter__(self_inner):
                acquired_events.append("acquired")
                return real_lock.__enter__()

            def __exit__(self_inner, *args):
                return real_lock.__exit__(*args)

        monitor._lock = TrackingLock()

        fail_response = MagicMock()
        fail_response.status_code = 500

        with patch("interface.health_monitor.requests.get", return_value=fail_response):
            monitor._check_health()

        self.assertGreater(len(acquired_events), 0, "Lock was not acquired during _check_health() on failure")

    def test_concurrent_checks_do_not_corrupt_state(self):
        """Concurrent calls to _check_health() must not corrupt the failure counter."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=100)

        fail_response = MagicMock()
        fail_response.status_code = 500

        num_threads = 10
        calls_per_thread = 5

        def run_checks():
            with patch("interface.health_monitor.requests.get", return_value=fail_response):
                for _ in range(calls_per_thread):
                    monitor._check_health()

        threads = [threading.Thread(target=run_checks) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        status = monitor.get_status()
        expected = num_threads * calls_per_thread
        self.assertEqual(
            status.consecutive_failures,
            expected,
            f"Expected {expected} failures, got {status.consecutive_failures} (possible race condition)",
        )


class TestHealthMonitorGetStatusSnapshot(unittest.TestCase):
    """Tests that get_status() returns a copy/snapshot of the current status."""

    def test_get_status_returns_health_status_instance(self):
        """get_status() must return a HealthStatus object."""
        monitor = HealthMonitor(check_url="https://example.com/getLive")
        status = monitor.get_status()
        self.assertIsInstance(status, HealthStatus)

    def test_get_status_returns_copy_not_reference(self):
        """Mutating the returned HealthStatus must not affect the internal state."""
        monitor = HealthMonitor(check_url="https://example.com/getLive")

        status = monitor.get_status()
        # Mutate the returned snapshot
        status.is_healthy = False
        status.consecutive_failures = 99

        # Internal state must be unchanged
        internal = monitor.get_status()
        self.assertTrue(internal.is_healthy)
        self.assertEqual(internal.consecutive_failures, 0)

    def test_get_status_snapshot_reflects_current_state(self):
        """get_status() must reflect the latest internal state."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        fail_response = MagicMock()
        fail_response.status_code = 500

        with patch("interface.health_monitor.requests.get", return_value=fail_response):
            monitor._check_health()

        status = monitor.get_status()
        self.assertEqual(status.consecutive_failures, 1)

    def test_get_status_includes_last_error_on_failure(self):
        """get_status() must include the last error message after a failure."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        fail_response = MagicMock()
        fail_response.status_code = 503

        with patch("interface.health_monitor.requests.get", return_value=fail_response):
            monitor._check_health()

        status = monitor.get_status()
        self.assertIsNotNone(status.last_error)
        self.assertIn("503", status.last_error)

    def test_get_status_last_error_is_none_after_success(self):
        """get_status() must have last_error=None after a successful check."""
        monitor = HealthMonitor(check_url="https://example.com/getLive", failure_threshold=3)

        # First cause a failure to set last_error
        fail_response = MagicMock()
        fail_response.status_code = 500
        with patch("interface.health_monitor.requests.get", return_value=fail_response):
            monitor._check_health()

        # Then succeed
        success_response = MagicMock()
        success_response.status_code = 200
        with patch("interface.health_monitor.requests.get", return_value=success_response):
            monitor._check_health()

        status = monitor.get_status()
        self.assertIsNone(status.last_error)


if __name__ == "__main__":
    unittest.main()
