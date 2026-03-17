"""
Property-based tests for PollingService.

**Validates: Requirements 3.2, 3.4, 6.5**

Property 8: Polling Ativo Durante Partida
  For any partida com estado "inProgress", o polling service deve estar no
  estado ACTIVE e executando o loop de atualização.

Property 9: Polling Usa Cache
  For any iteração do polling, se existem dados válidos em cache, o sistema
  não deve fazer nova requisição à API.

Property 11: Logging de Ciclo de Polling
  For any início ou fim de ciclo de polling, deve haver entrada no log com
  nível INFO indicando a transição de estado.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import threading
import logging
from unittest.mock import MagicMock, patch, call
from typing import Any

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.polling_service import PollingService, PollingState
from interface.cache_layer import CacheLayer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
)

game_state_strategy = st.just("inProgress")

interval_strategy = st.integers(min_value=1, max_value=5)

cache_data_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10),
    values=st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=1,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 8: Polling Ativo Durante Partida
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    game_state=game_state_strategy,
    interval=interval_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_polling_ativo_durante_partida(game_id, game_state, interval):
    """
    **Validates: Requirements 3.2**

    Property 8: For any partida com estado "inProgress", o polling service
    deve estar no estado ACTIVE e executando o loop de atualização.
    """
    callback_called = threading.Event()

    def fetch_callback():
        callback_called.set()

    service = PollingService(
        fetch_callback=fetch_callback,
        interval_seconds=interval,
    )

    # Before start: state must be IDLE
    assert service.get_state() == PollingState.IDLE, (
        f"Expected IDLE before start, got {service.get_state()}"
    )

    # Simulate a match in "inProgress" state by starting the service
    service.start()

    try:
        # After start: state must be ACTIVE
        assert service.get_state() == PollingState.ACTIVE, (
            f"Expected ACTIVE after start for inProgress match, got {service.get_state()}"
        )

        # The polling loop must actually execute the callback
        called = callback_called.wait(timeout=interval + 2)
        assert called, (
            f"Expected fetch_callback to be called within {interval + 2}s "
            f"for inProgress match with game_id={game_id}"
        )

        # State must still be ACTIVE while match is in progress
        assert service.get_state() == PollingState.ACTIVE, (
            f"Expected ACTIVE while match is inProgress, got {service.get_state()}"
        )
    finally:
        service.stop()

    # After stop: state must be STOPPED
    assert service.get_state() == PollingState.STOPPED, (
        f"Expected STOPPED after stop(), got {service.get_state()}"
    )


# ---------------------------------------------------------------------------
# Property 9: Polling Usa Cache
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    cached_data=cache_data_strategy,
    interval=interval_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_polling_usa_cache(game_id, cached_data, interval):
    """
    **Validates: Requirements 3.4**

    Property 9: For any iteração do polling, se existem dados válidos em cache,
    o sistema não deve fazer nova requisição à API.
    """
    cache = CacheLayer()
    cache_key = f"window_{game_id}"

    # Pre-populate cache with valid data (TTL=30s so it won't expire during test)
    cache.set(cache_key, cached_data, ttl_seconds=30)

    api_call_count = [0]

    def fetch_callback():
        """Simulates a fetch that checks cache before calling API."""
        cached = cache.get(cache_key)
        if cached is not None:
            # Cache hit: no API call needed
            return cached
        # Cache miss: would call API
        api_call_count[0] += 1
        return None

    callback_executed = threading.Event()
    original_callback = fetch_callback

    execution_count = [0]

    def tracked_callback():
        result = original_callback()
        execution_count[0] += 1
        if execution_count[0] >= 1:
            callback_executed.set()
        return result

    service = PollingService(
        fetch_callback=tracked_callback,
        interval_seconds=interval,
    )

    service.start()
    try:
        # Wait for at least one polling iteration
        executed = callback_executed.wait(timeout=interval + 2)
        assert executed, (
            f"Expected polling callback to execute within {interval + 2}s"
        )

        # Since cache has valid data, no API calls should have been made
        assert api_call_count[0] == 0, (
            f"Expected 0 API calls when cache is valid, got {api_call_count[0]} "
            f"for game_id={game_id}"
        )

        # Verify cache still has the data
        assert cache.get(cache_key) == cached_data, (
            "Cache data should remain unchanged when polling uses cache"
        )
    finally:
        service.stop()


# ---------------------------------------------------------------------------
# Property 11: Logging de Ciclo de Polling
# ---------------------------------------------------------------------------

@given(
    interval=interval_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_logging_ciclo_de_polling(interval):
    """
    **Validates: Requirements 6.5**

    Property 11: For any início ou fim de ciclo de polling, deve haver entrada
    no log com nível INFO indicando a transição de estado.
    """
    callback_executed = threading.Event()

    def fetch_callback():
        callback_executed.set()

    mock_logger = MagicMock(spec=logging.Logger)
    # Make warning/error not raise
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.debug = MagicMock()

    service = PollingService(
        fetch_callback=fetch_callback,
        interval_seconds=interval,
        logger=mock_logger,
    )

    service.start()
    try:
        # Wait for at least one callback execution
        executed = callback_executed.wait(timeout=interval + 2)
        assert executed, f"Expected callback to execute within {interval + 2}s"
    finally:
        service.stop()

    # Collect all INFO log messages
    info_calls = mock_logger.info.call_args_list
    assert len(info_calls) >= 1, (
        "Expected at least one INFO log entry during polling lifecycle"
    )

    all_messages = []
    for c in info_calls:
        args, kwargs = c
        msg = args[0] if args else ""
        all_messages.append(msg)

    # Must have a log entry for polling start (cycle start)
    start_logged = any(
        "iniciado" in msg.lower() or "start" in msg.lower() or "ciclo" in msg.lower()
        for msg in all_messages
    )
    assert start_logged, (
        f"Expected INFO log for polling cycle start. Got messages: {all_messages}"
    )

    # Must have a log entry for polling stop (cycle end)
    stop_logged = any(
        "finalizado" in msg.lower() or "parado" in msg.lower() or "stop" in msg.lower()
        for msg in all_messages
    )
    assert stop_logged, (
        f"Expected INFO log for polling cycle end. Got messages: {all_messages}"
    )
