"""
Unit tests for PollingService.

Validates: Requirements 3.1, 3.3
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import threading
import unittest
from unittest.mock import MagicMock, patch
import logging

from interface.polling_service import PollingService, PollingState


class TestPollingServiceInterval(unittest.TestCase):
    """Tests for Requirement 3.1: polling at correct interval."""

    def test_callback_called_after_start(self):
        """Callback must be called after service starts."""
        called = threading.Event()

        def callback():
            called.set()

        service = PollingService(fetch_callback=callback, interval_seconds=1)
        service.start()
        try:
            result = called.wait(timeout=3)
            self.assertTrue(result, "Callback was not called within 3 seconds")
        finally:
            service.stop()

    def test_callback_called_multiple_times(self):
        """Callback must be called multiple times during polling."""
        call_count = [0]
        enough_calls = threading.Event()

        def callback():
            call_count[0] += 1
            if call_count[0] >= 2:
                enough_calls.set()

        service = PollingService(fetch_callback=callback, interval_seconds=1)
        service.start()
        try:
            result = enough_calls.wait(timeout=5)
            self.assertTrue(result, f"Expected at least 2 calls, got {call_count[0]}")
            self.assertGreaterEqual(call_count[0], 2)
        finally:
            service.stop()

    def test_interval_is_respected(self):
        """Polling interval must be approximately correct."""
        timestamps = []

        def callback():
            timestamps.append(time.time())

        interval = 1
        service = PollingService(fetch_callback=callback, interval_seconds=interval)
        service.start()
        try:
            # Wait for at least 2 calls
            deadline = time.time() + 5
            while len(timestamps) < 2 and time.time() < deadline:
                time.sleep(0.1)
        finally:
            service.stop()

        self.assertGreaterEqual(len(timestamps), 2, "Expected at least 2 callback calls")

        # Check that the gap between calls is approximately the interval
        gap = timestamps[1] - timestamps[0]
        # Allow generous tolerance (0.5x to 3x interval) due to thread scheduling
        self.assertGreater(gap, interval * 0.5, f"Interval too short: {gap:.2f}s")
        self.assertLess(gap, interval * 3.0, f"Interval too long: {gap:.2f}s")


class TestPollingServiceStop(unittest.TestCase):
    """Tests for stopping polling when no matches are active."""

    def test_state_is_idle_before_start(self):
        """State must be IDLE before start() is called."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        self.assertEqual(service.get_state(), PollingState.IDLE)

    def test_state_is_active_after_start(self):
        """State must be ACTIVE after start() is called."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        try:
            self.assertEqual(service.get_state(), PollingState.ACTIVE)
        finally:
            service.stop()

    def test_state_is_stopped_after_stop(self):
        """State must be STOPPED after stop() is called."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        service.stop()
        self.assertEqual(service.get_state(), PollingState.STOPPED)

    def test_callback_not_called_after_stop(self):
        """Callback must not be called after stop() is invoked."""
        call_count = [0]
        first_call = threading.Event()

        def callback():
            call_count[0] += 1
            first_call.set()

        service = PollingService(fetch_callback=callback, interval_seconds=1)
        service.start()

        # Wait for first call
        first_call.wait(timeout=3)
        service.stop()

        count_at_stop = call_count[0]
        # Wait a bit to ensure no more calls happen
        time.sleep(1.5)
        count_after_wait = call_count[0]

        self.assertEqual(
            count_at_stop, count_after_wait,
            f"Callback was called {count_after_wait - count_at_stop} times after stop()"
        )

    def test_stop_when_not_started_is_safe(self):
        """Calling stop() on an IDLE service must not raise."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        try:
            service.stop()  # Should not raise
        except Exception as e:
            self.fail(f"stop() raised an exception on IDLE service: {e}")

    def test_double_stop_is_safe(self):
        """Calling stop() twice must not raise."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        service.stop()
        try:
            service.stop()  # Second stop should be safe
        except Exception as e:
            self.fail(f"Second stop() raised an exception: {e}")


class TestPollingServicePauseResume(unittest.TestCase):
    """Tests for pause and resume functionality."""

    def test_state_is_paused_after_pause(self):
        """State must be PAUSED after pause() is called."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        try:
            service.pause()
            self.assertEqual(service.get_state(), PollingState.PAUSED)
        finally:
            service.stop()

    def test_state_is_active_after_resume(self):
        """State must be ACTIVE after resume() is called."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        try:
            service.pause()
            service.resume()
            self.assertEqual(service.get_state(), PollingState.ACTIVE)
        finally:
            service.stop()

    def test_callback_not_called_while_paused(self):
        """Callback must not be called while service is paused."""
        first_call = threading.Event()
        call_count = [0]

        def callback():
            call_count[0] += 1
            first_call.set()

        service = PollingService(fetch_callback=callback, interval_seconds=1)
        service.start()

        # Wait for first call, then pause
        first_call.wait(timeout=3)
        service.pause()
        count_at_pause = call_count[0]

        # Wait to ensure no more calls happen while paused
        time.sleep(1.5)
        count_while_paused = call_count[0]

        try:
            self.assertEqual(
                count_at_pause, count_while_paused,
                f"Callback was called {count_while_paused - count_at_pause} times while paused"
            )
        finally:
            service.stop()

    def test_callback_resumes_after_resume(self):
        """Callback must be called again after resume()."""
        first_call = threading.Event()
        resumed_call = threading.Event()
        call_count = [0]

        def callback():
            call_count[0] += 1
            if call_count[0] == 1:
                first_call.set()
            elif call_count[0] >= 2:
                resumed_call.set()

        service = PollingService(fetch_callback=callback, interval_seconds=1)
        service.start()

        first_call.wait(timeout=3)
        service.pause()
        time.sleep(0.5)
        service.resume()

        try:
            result = resumed_call.wait(timeout=4)
            self.assertTrue(result, "Callback was not called after resume()")
        finally:
            service.stop()


class TestPollingServiceThreadSafety(unittest.TestCase):
    """Tests for thread safety of PollingService."""

    def test_get_state_is_thread_safe(self):
        """get_state() must be callable from multiple threads without errors."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()

        errors = []

        def read_state():
            try:
                for _ in range(20):
                    state = service.get_state()
                    assert state in PollingState, f"Invalid state: {state}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        service.stop()
        self.assertEqual(errors, [], f"Thread safety errors: {errors}")

    def test_start_is_idempotent(self):
        """Calling start() twice must not create two threads."""
        service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
        service.start()
        try:
            service.start()  # Second start should be a no-op
            self.assertEqual(service.get_state(), PollingState.ACTIVE)
        finally:
            service.stop()

    def test_callback_exception_does_not_stop_polling(self):
        """An exception in the callback must not stop the polling loop."""
        call_count = [0]
        second_call = threading.Event()

        def failing_callback():
            call_count[0] += 1
            if call_count[0] >= 2:
                second_call.set()
            raise RuntimeError("Simulated callback error")

        service = PollingService(fetch_callback=failing_callback, interval_seconds=1)
        service.start()
        try:
            result = second_call.wait(timeout=5)
            self.assertTrue(
                result,
                f"Expected polling to continue after callback exception, got {call_count[0]} calls"
            )
            self.assertEqual(service.get_state(), PollingState.ACTIVE)
        finally:
            service.stop()

    def test_concurrent_start_stop(self):
        """Concurrent start/stop calls must not corrupt state."""
        errors = []

        def run():
            try:
                service = PollingService(fetch_callback=lambda: None, interval_seconds=1)
                service.start()
                time.sleep(0.1)
                service.stop()
                final_state = service.get_state()
                assert final_state == PollingState.STOPPED, f"Expected STOPPED, got {final_state}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Concurrent start/stop errors: {errors}")


class TestPollingServiceLogging(unittest.TestCase):
    """Tests for logging behavior of PollingService."""

    def test_start_logs_info(self):
        """start() must log an INFO message."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.debug = MagicMock()

        service = PollingService(
            fetch_callback=lambda: None,
            interval_seconds=1,
            logger=mock_logger,
        )
        service.start()
        service.stop()

        mock_logger.info.assert_called()

    def test_stop_logs_info(self):
        """stop() must log an INFO message."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.debug = MagicMock()

        service = PollingService(
            fetch_callback=lambda: None,
            interval_seconds=1,
            logger=mock_logger,
        )
        service.start()
        service.stop()

        # Check that stop was logged
        stop_messages = [
            str(c) for c in mock_logger.info.call_args_list
            if "parado" in str(c).lower() or "finalizado" in str(c).lower() or "stop" in str(c).lower()
        ]
        self.assertGreater(len(stop_messages), 0, "Expected INFO log for stop")

    def test_callback_exception_logs_error(self):
        """An exception in the callback must be logged as ERROR."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.debug = MagicMock()

        error_logged = threading.Event()
        original_error = mock_logger.error

        def error_side_effect(*args, **kwargs):
            error_logged.set()

        mock_logger.error.side_effect = error_side_effect

        def failing_callback():
            raise RuntimeError("Test error")

        service = PollingService(
            fetch_callback=failing_callback,
            interval_seconds=1,
            logger=mock_logger,
        )
        service.start()
        try:
            result = error_logged.wait(timeout=3)
            self.assertTrue(result, "Expected ERROR log for callback exception")
        finally:
            service.stop()


if __name__ == "__main__":
    unittest.main()
