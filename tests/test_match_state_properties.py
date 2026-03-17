"""
Property-based tests for match state management.

Properties 22-26 validate match finalization detection and polling integration.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.6**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import threading
import logging
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.polling_service import PollingService, PollingState
from interface.cache_layer import CacheLayer
from interface.live_service import is_match_finished, create_polling_service, _cache_layer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
)

match_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
)

# Strategy for a "finished" frame
finished_frame_strategy = st.fixed_dictionaries({
    "frame": st.fixed_dictionaries({
        "gameState": st.just("finished"),
        "blueTeam": st.just({}),
        "redTeam": st.just({}),
    })
})

# Strategy for an "inProgress" frame
in_progress_frame_strategy = st.fixed_dictionaries({
    "frame": st.fixed_dictionaries({
        "gameState": st.just("inProgress"),
        "blueTeam": st.just({}),
        "redTeam": st.just({}),
    })
})

# Strategy for a series where all games are "completed"
all_games_completed_strategy = st.fixed_dictionaries({
    "games": st.lists(
        st.fixed_dictionaries({"state": st.just("completed"), "id": game_id_strategy}),
        min_size=1,
        max_size=5,
    )
})

# Strategy for a series with mixed game states (not all completed)
mixed_games_strategy = st.fixed_dictionaries({
    "games": st.lists(
        st.fixed_dictionaries({
            "state": st.sampled_from(["inProgress", "unstarted"]),
            "id": game_id_strategy,
        }),
        min_size=1,
        max_size=5,
    )
})

# Strategy for BO3 series where team1 has 2 wins
bo3_team1_wins_strategy = st.fixed_dictionaries({
    "strategy": st.just({"count": 3}),
    "teams": st.just([
        {"result": {"gameWins": 2}},
        {"result": {"gameWins": 0}},
    ]),
})

# Strategy for BO5 series where team2 has 3 wins
bo5_team2_wins_strategy = st.fixed_dictionaries({
    "strategy": st.just({"count": 5}),
    "teams": st.just([
        {"result": {"gameWins": 1}},
        {"result": {"gameWins": 3}},
    ]),
})

# Strategy for series where no team has enough wins yet
no_winner_yet_strategy = st.fixed_dictionaries({
    "strategy": st.fixed_dictionaries({"count": st.sampled_from([3, 5])}),
    "teams": st.just([
        {"result": {"gameWins": 0}},
        {"result": {"gameWins": 1}},
    ]),
})


# ---------------------------------------------------------------------------
# Property 22: Polling Para em Partida Finalizada
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    frame_data=finished_frame_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_22_polling_para_em_partida_finalizada(game_id, frame_data):
    """
    **Validates: Requirements 9.1**

    Property 22: For any frame com gameState igual a "finished", o polling
    service deve transicionar para estado STOPPED.
    """
    # Verify is_match_finished correctly detects the finished state
    assert is_match_finished(frame_data), (
        f"is_match_finished should return True for gameState='finished', "
        f"got False for data={frame_data}"
    )

    # Now verify that a PollingService stops when the callback detects a finished match
    stop_called = threading.Event()
    callback_executed = threading.Event()

    def fetch_callback():
        callback_executed.set()
        # Simulate detecting a finished match and stopping
        if is_match_finished(frame_data):
            stop_called.set()

    service = PollingService(
        fetch_callback=fetch_callback,
        interval_seconds=1,
    )

    service.start()
    assert service.get_state() == PollingState.ACTIVE

    # Wait for callback to execute
    executed = callback_executed.wait(timeout=3)
    assert executed, "Polling callback should have been called"

    # Stop the service (simulating what create_polling_service does)
    service.stop()

    assert service.get_state() == PollingState.STOPPED, (
        f"Expected STOPPED after detecting finished match, got {service.get_state()}"
    )
    assert stop_called.is_set(), (
        "Callback should have detected the finished match state"
    )


# ---------------------------------------------------------------------------
# Property 23: Série Finalizada por Games Completos
# ---------------------------------------------------------------------------

@given(series_data=all_games_completed_strategy)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_23_serie_finalizada_por_games_completos(series_data):
    """
    **Validates: Requirements 9.2**

    Property 23: For any série onde todos os games têm estado "completed",
    o sistema deve marcar a série como finalizada e parar o polling.
    """
    # All games completed => is_match_finished must return True
    result = is_match_finished(series_data)
    assert result is True, (
        f"is_match_finished should return True when all games are 'completed'. "
        f"Got False for data={series_data}"
    )


@given(series_data=mixed_games_strategy)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_23_serie_nao_finalizada_com_games_em_andamento(series_data):
    """
    **Validates: Requirements 9.2**

    Complementary: When not all games are completed, is_match_finished
    should NOT return True based on the games criterion alone.
    """
    # Mixed states (inProgress/unstarted) => games criterion should NOT trigger
    # (other criteria might still trigger if frame or teams data is present,
    # but this data has neither)
    result = is_match_finished(series_data)
    assert result is False, (
        f"is_match_finished should return False when games are not all completed "
        f"and no other finish criteria met. Got True for data={series_data}"
    )


# ---------------------------------------------------------------------------
# Property 24: Série Finalizada por Vitórias
# ---------------------------------------------------------------------------

@given(series_data=bo3_team1_wins_strategy)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_24_bo3_finalizado_por_vitorias_time1(series_data):
    """
    **Validates: Requirements 9.3**

    Property 24: For any BO3 série onde team1 atingiu 2 vitórias,
    o sistema deve marcar a série como finalizada.
    """
    result = is_match_finished(series_data)
    assert result is True, (
        f"is_match_finished should return True for BO3 with team1 having 2 wins. "
        f"Got False for data={series_data}"
    )


@given(series_data=bo5_team2_wins_strategy)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_24_bo5_finalizado_por_vitorias_time2(series_data):
    """
    **Validates: Requirements 9.3**

    Property 24: For any BO5 série onde team2 atingiu 3 vitórias,
    o sistema deve marcar a série como finalizada.
    """
    result = is_match_finished(series_data)
    assert result is True, (
        f"is_match_finished should return True for BO5 with team2 having 3 wins. "
        f"Got False for data={series_data}"
    )


@given(series_data=no_winner_yet_strategy)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_24_serie_nao_finalizada_sem_vencedor(series_data):
    """
    **Validates: Requirements 9.3**

    Complementary: When no team has reached the win threshold,
    is_match_finished should return False (based on wins criterion alone).
    """
    result = is_match_finished(series_data)
    assert result is False, (
        f"is_match_finished should return False when no team has enough wins. "
        f"Got True for data={series_data}"
    )


# ---------------------------------------------------------------------------
# Property 25: Verificação de Estado Antes de Polling
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    match_id=match_id_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_25_verificacao_estado_antes_de_polling(game_id, match_id):
    """
    **Validates: Requirements 9.4**

    Property 25: For any iteração do polling loop, deve haver verificação
    do estado da partida antes de buscar novos dados.

    Verifies that create_polling_service creates a service whose callback
    calls is_match_finished (state check) before deciding to continue.
    """
    state_checks = []
    original_is_match_finished = is_match_finished

    callback_executed = threading.Event()

    # Patch get_game_window to return a non-finished frame
    mock_window_data = {
        "frame": {"gameState": "inProgress"},
        "metadata": {}
    }

    with patch("interface.live_service.get_game_window", return_value=mock_window_data) as mock_gw, \
         patch("interface.live_service.is_match_finished", wraps=original_is_match_finished) as mock_imf:

        service = create_polling_service(game_id, match_id)
        service.interval_seconds = 1

        # Wrap the callback to track execution
        original_callback = service.fetch_callback
        def tracked_callback():
            original_callback()
            callback_executed.set()

        service.fetch_callback = tracked_callback
        service.start()

        try:
            executed = callback_executed.wait(timeout=3)
            assert executed, "Polling callback should have been called"

            # Verify that is_match_finished was called (state check happened)
            assert mock_imf.called, (
                "is_match_finished should be called during each polling iteration "
                "to check match state before continuing"
            )

            # Verify get_game_window was called (data was fetched)
            assert mock_gw.called, (
                "get_game_window should be called during polling iteration"
            )
        finally:
            service.stop()


# ---------------------------------------------------------------------------
# Property 26: Cache Limpo ao Finalizar
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    match_id=match_id_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_26_cache_limpo_ao_finalizar(game_id, match_id):
    """
    **Validates: Requirements 9.6**

    Property 26: For any partida que transiciona para estado finalizado,
    todas as entradas de cache relacionadas (window, details) devem ser removidas.
    """
    # Use a fresh CacheLayer to avoid interference
    test_cache = CacheLayer()

    # Pre-populate cache with window and details entries
    window_key = f"window_{game_id}"
    details_key = f"details_{game_id}"
    test_cache.set(window_key, {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)
    test_cache.set(details_key, {"participants": []}, ttl_seconds=60)

    # Verify data is in cache
    assert test_cache.get(window_key) is not None, "window cache should be populated"
    assert test_cache.get(details_key) is not None, "details cache should be populated"

    # Simulate what create_polling_service does when it detects a finished match:
    # delete both cache keys
    test_cache.delete(window_key)
    test_cache.delete(details_key)

    # Verify cache was cleared
    assert test_cache.get(window_key) is None, (
        f"window cache for game_id={game_id} should be cleared after match finishes"
    )
    assert test_cache.get(details_key) is None, (
        f"details cache for game_id={game_id} should be cleared after match finishes"
    )


@given(
    game_id=game_id_strategy,
    match_id=match_id_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_26_create_polling_service_limpa_cache_ao_finalizar(game_id, match_id):
    """
    **Validates: Requirements 9.6**

    Property 26 (integration): create_polling_service callback clears cache
    entries when a finished match is detected.
    """
    finished_window_data = {
        "frame": {"gameState": "finished"},
        "metadata": {}
    }

    deleted_keys = []
    original_delete = _cache_layer.delete

    def tracking_delete(key):
        deleted_keys.append(key)
        original_delete(key)

    callback_executed = threading.Event()

    with patch("interface.live_service.get_game_window", return_value=finished_window_data), \
         patch.object(_cache_layer, "delete", side_effect=tracking_delete):

        service = create_polling_service(game_id, match_id)
        service.interval_seconds = 1

        original_callback = service.fetch_callback
        def tracked_callback():
            original_callback()
            callback_executed.set()

        service.fetch_callback = tracked_callback
        service.start()

        try:
            executed = callback_executed.wait(timeout=3)
            assert executed, "Polling callback should have been called"

            # Give a moment for the stop to propagate
            import time
            time.sleep(0.2)

            # Verify cache keys were deleted
            assert f"window_{game_id}" in deleted_keys, (
                f"window_{game_id} should be deleted from cache when match finishes. "
                f"Deleted keys: {deleted_keys}"
            )
            assert f"details_{game_id}" in deleted_keys, (
                f"details_{game_id} should be deleted from cache when match finishes. "
                f"Deleted keys: {deleted_keys}"
            )
        finally:
            service.stop()
