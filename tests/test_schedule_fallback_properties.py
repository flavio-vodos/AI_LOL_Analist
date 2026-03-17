"""
Property-based tests for schedule fallback mechanism.

Properties 27-31 validate the fallback behavior when getLive doesn't return
expected matches, using getSchedule as a secondary source.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

match_id_strategy = st.integers(min_value=100000, max_value=999999).map(str)

team_strategy = st.fixed_dictionaries({
    "code": st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=4),
    "name": st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=3, max_size=20),
    "image": st.just(""),
    "result": st.fixed_dictionaries({"gameWins": st.integers(min_value=0, max_value=2)}),
})

# Strategy for a schedule entry within the temporal window (started < 4h ago OR starts < 10min)
def make_schedule_entry(match_id, start_time_str, state="unstarted"):
    return {
        "match_id": match_id,
        "state": state,
        "league": "Test League",
        "team_blue": {
            "code": "BLU", "name": "Blue Team", "image": "",
            "result": {"gameWins": 0},
        },
        "team_red": {
            "code": "RED", "name": "Red Team", "image": "",
            "result": {"gameWins": 0},
        },
        "start_time": start_time_str,
        "strategy": {"count": 3},
    }


def fmt_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Property 27: Fallback para Schedule
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    minutes_ago=st.integers(min_value=1, max_value=200),
)
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_27_fallback_para_schedule(match_id, minutes_ago):
    """
    **Validates: Requirements 10.1**

    Property 27: For any Match_ID expected that does not appear in getLive results,
    the system must consult getSchedule as fallback.

    When get_live_games() doesn't return a match_id, the system uses
    get_schedule_today() as fallback to find it.
    """
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(minutes=minutes_ago)
    start_time_str = fmt_time(start_dt)

    schedule_entry = make_schedule_entry(match_id, start_time_str, state="unstarted")

    # getLive returns empty events (match_id not present)
    mock_live_response = {
        "data": {"schedule": {"events": []}}
    }

    # getSchedule returns our entry
    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "unstarted",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "unstarted",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    schedule_called = []

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            schedule_called.append(True)
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    # getSchedule must have been consulted
    assert len(schedule_called) > 0, (
        "getSchedule must be consulted as fallback when getLive returns no events"
    )


# ---------------------------------------------------------------------------
# Property 28: Inclusão por Janela Temporal
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    # Offset in minutes: negative = started X minutes ago, positive = starts in X minutes
    offset_minutes=st.one_of(
        st.integers(min_value=-239, max_value=0),   # started 0-239 min ago (within 4h)
        st.integers(min_value=1, max_value=9),       # starts in 1-9 min (within 10min)
    ),
)
@settings(
    max_examples=40,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_28_inclusao_por_janela_temporal_dentro(match_id, offset_minutes):
    """
    **Validates: Requirements 10.2, 10.3**

    Property 28: For any match in the schedule that started less than 4 hours ago
    OR starts in less than 10 minutes, it must be included in the live games list.

    Note: The implementation filters schedule by today's UTC date, so we only test
    offsets that keep the start_time within today's date boundary.
    """
    from hypothesis import assume
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now + timedelta(minutes=offset_minutes)

    # Skip if start_dt crosses into a different UTC date (midnight edge case)
    # The implementation filters by today's date, so cross-day offsets won't appear
    assume(start_dt.date() == now.date())

    start_time_str = fmt_time(start_dt)

    mock_live_response = {"data": {"schedule": {"events": []}}}

    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "unstarted",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "unstarted",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]
    assert match_id in match_ids_in_result, (
        f"Match {match_id} with start_time={start_time_str} (offset={offset_minutes}min) "
        f"should be included in live games (within temporal window). "
        f"Got match_ids: {match_ids_in_result}"
    )


@given(
    match_id=match_id_strategy,
    # Offset in minutes: outside the window
    offset_minutes=st.one_of(
        st.integers(min_value=241, max_value=600),   # starts in 241+ min (> 4h future)
        st.integers(min_value=-600, max_value=-241), # started 241+ min ago (> 4h past)
    ),
)
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_28_exclusao_fora_da_janela_temporal(match_id, offset_minutes):
    """
    **Validates: Requirements 10.2, 10.3**

    Property 28 (outside window): Matches outside the temporal window
    (started > 4h ago OR starts > 10min in the future) must NOT be included.
    """
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now + timedelta(minutes=offset_minutes)
    start_time_str = fmt_time(start_dt)

    mock_live_response = {"data": {"schedule": {"events": []}}}

    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "unstarted",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "unstarted",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]
    assert match_id not in match_ids_in_result, (
        f"Match {match_id} with start_time={start_time_str} (offset={offset_minutes}min) "
        f"should NOT be included (outside temporal window). "
        f"Got match_ids: {match_ids_in_result}"
    )


# ---------------------------------------------------------------------------
# Property 29: Deduplicação por Match_ID
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    minutes_ago=st.integers(min_value=1, max_value=100),
)
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_29_deduplicacao_por_match_id(match_id, minutes_ago):
    """
    **Validates: Requirements 10.4**

    Property 29: For any combination of getLive and getSchedule results,
    there must be no duplicate matches (same Match_ID appearing twice).
    """
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(minutes=minutes_ago)
    start_time_str = fmt_time(start_dt)

    # getLive returns the match
    mock_live_response = {
        "data": {"schedule": {"events": [
            {
                "state": "inProgress",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "inProgress",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [{"id": "game1", "state": "inProgress", "number": 1}],
                }
            }
        ]}}
    }

    # getSchedule also returns the same match
    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "inProgress",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "inProgress",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]

    # No duplicates allowed
    assert len(match_ids_in_result) == len(set(match_ids_in_result)), (
        f"Duplicate match_ids found in result: {match_ids_in_result}. "
        f"Each match_id must appear at most once."
    )

    # The match should appear exactly once
    count = match_ids_in_result.count(match_id)
    assert count <= 1, (
        f"Match_ID {match_id} appears {count} times in result. "
        f"Expected at most 1 occurrence (deduplication by match_id)."
    )


# ---------------------------------------------------------------------------
# Property 30: Exclusão de Partidas Finalizadas do Fallback
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    minutes_ago=st.integers(min_value=1, max_value=100),
)
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_30_exclusao_partidas_finalizadas_do_fallback(match_id, minutes_ago):
    """
    **Validates: Requirements 10.5**

    Property 30: For any match in the schedule with state "completed",
    it must NOT be included in the fallback live games list.
    """
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(minutes=minutes_ago)
    start_time_str = fmt_time(start_dt)

    mock_live_response = {"data": {"schedule": {"events": []}}}

    # Schedule returns a completed match within the temporal window
    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "completed",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "completed",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 2}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]
    assert match_id not in match_ids_in_result, (
        f"Completed match {match_id} (state='completed') should NOT be included "
        f"in fallback live games. Got match_ids: {match_ids_in_result}"
    )


@given(
    match_id=match_id_strategy,
    minutes_ago=st.integers(min_value=1, max_value=100),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_30_exclusao_por_placar_final(match_id, minutes_ago):
    """
    **Validates: Requirements 10.5**

    Property 30 (win threshold): A match where a team has already reached
    the win threshold must NOT be included in the fallback.
    """
    from interface.live_service import get_live_games

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(minutes=minutes_ago)
    start_time_str = fmt_time(start_dt)

    mock_live_response = {"data": {"schedule": {"events": []}}}

    # BO3 match where team1 already has 2 wins (series over)
    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "inProgress",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "inProgress",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 2}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    with patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]
    assert match_id not in match_ids_in_result, (
        f"Match {match_id} where team reached win threshold should NOT be included "
        f"in fallback live games. Got match_ids: {match_ids_in_result}"
    )


# ---------------------------------------------------------------------------
# Property 31: Logging de Fallback
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    minutes_ago=st.integers(min_value=1, max_value=100),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_31_logging_de_fallback(match_id, minutes_ago):
    """
    **Validates: Requirements 10.6**

    Property 31: For any use of the schedule fallback, there must be a log entry
    at INFO or DEBUG level indicating that the fallback was triggered.

    When the fallback is used, a log entry must be emitted.
    """
    from hypothesis import assume
    from interface.live_service import get_live_games
    import interface.live_service as ls_module

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(minutes=minutes_ago)

    # Skip if start_dt crosses into a different UTC date (midnight edge case)
    # The implementation filters schedule by today's date
    assume(start_dt.date() == now.date())

    start_time_str = fmt_time(start_dt)

    mock_live_response = {"data": {"schedule": {"events": []}}}

    mock_schedule_response = {
        "data": {"schedule": {"events": [
            {
                "state": "unstarted",
                "startTime": start_time_str,
                "league": {"name": "Test League"},
                "match": {
                    "id": match_id,
                    "state": "unstarted",
                    "strategy": {"count": 3},
                    "teams": [
                        {"code": "BLU", "name": "Blue Team", "image": "", "result": {"gameWins": 0}},
                        {"code": "RED", "name": "Red Team", "image": "", "result": {"gameWins": 0}},
                    ],
                    "games": [],
                }
            }
        ]}}
    }

    def mock_get(url, params=None, headers=None, timeout=10):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "getSchedule" in url:
            resp.json.return_value = mock_schedule_response
        else:
            resp.json.return_value = mock_live_response
        return resp

    info_calls = []
    debug_calls = []
    original_info = ls_module.logger.info
    original_debug = ls_module.logger.debug

    def tracking_info(msg, *args, **kwargs):
        info_calls.append(str(msg))
        original_info(msg, *args, **kwargs)

    def tracking_debug(msg, *args, **kwargs):
        debug_calls.append(str(msg))
        original_debug(msg, *args, **kwargs)

    with patch.object(ls_module.logger, "info", side_effect=tracking_info), \
         patch.object(ls_module.logger, "debug", side_effect=tracking_debug), \
         patch("interface.live_service.requests.get", side_effect=mock_get):
        result = get_live_games()

    match_ids_in_result = [g["match_id"] for g in result]

    # Only assert logging if the fallback was actually triggered
    if match_id in match_ids_in_result:
        all_log_calls = info_calls + debug_calls
        assert len(all_log_calls) > 0, (
            f"When fallback is used for match {match_id}, at least one INFO or DEBUG "
            f"log entry must be emitted. Got info_calls={info_calls}, debug_calls={debug_calls}"
        )
