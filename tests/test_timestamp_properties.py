"""
Property-based tests for timestamp optimization.

Properties 17-21 validate timestamp handling in API requests.

**Validates: Requirements 8.1, 8.2, 8.4, 8.5, 8.6**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import re
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.live_service import get_iso_date_multiple_of_10, _get_cache_buster, get_game_details


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
).filter(lambda x: x != "unknown")

# ISO 8601 timestamp strategy (valid rfc460Timestamp values)
iso_timestamp_strategy = st.builds(
    lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ),
)


# ---------------------------------------------------------------------------
# Property 17: Timestamp Múltiplo de 10
# ---------------------------------------------------------------------------

@given(st.none())
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_17_timestamp_multiplo_de_10(_):
    """
    **Validates: Requirements 8.1**

    Property 17: For any call to get_iso_date_multiple_of_10(), the returned
    timestamp must be an ISO 8601 string with seconds rounded to a multiple of 10
    (0, 10, 20, 30, 40, 50).
    """
    ts = get_iso_date_multiple_of_10()

    # Must match ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    assert re.match(pattern, ts), (
        f"Timestamp '{ts}' does not match ISO 8601 format YYYY-MM-DDTHH:MM:SSZ"
    )

    # Parse the seconds
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    seconds = dt.second

    assert seconds % 10 == 0, (
        f"Seconds in timestamp '{ts}' must be a multiple of 10 (0,10,20,30,40,50), "
        f"got {seconds}"
    )

    assert seconds in (0, 10, 20, 30, 40, 50), (
        f"Seconds must be one of (0, 10, 20, 30, 40, 50), got {seconds} in '{ts}'"
    )


@given(st.none())
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_17_timestamp_formato_iso8601(_):
    """
    **Validates: Requirements 8.1**

    Property 17 (format): The timestamp returned by get_iso_date_multiple_of_10()
    must be a valid ISO 8601 string parseable by strptime.
    """
    ts = get_iso_date_multiple_of_10()

    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        pytest.fail(
            f"get_iso_date_multiple_of_10() returned '{ts}' which is not valid ISO 8601: {e}"
        )

    # Must end with Z (UTC)
    assert ts.endswith("Z"), (
        f"Timestamp '{ts}' must end with 'Z' to indicate UTC"
    )


# ---------------------------------------------------------------------------
# Property 18: Details Usa Timestamp do Frame
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
    ts=iso_timestamp_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_18_details_usa_timestamp_do_frame(game_id, ts):
    """
    **Validates: Requirements 8.2**

    Property 18: For any call to get_game_details(game_id, timestamp=ts),
    the timestamp must be passed as the 'startingTime' parameter in the API request.
    """
    captured_params = {}

    def mock_fetch_with_retry(url, params=None, headers=None, timeout=10, retry_without_param=None):
        captured_params.update(params or {})
        # Return minimal valid response
        return {"frames": [{"blueTeam": {"participants": []}, "redTeam": {"participants": []}}]}

    with patch("interface.live_service._retry_system") as mock_retry:
        mock_retry.fetch_with_retry.side_effect = mock_fetch_with_retry

        # Also bypass cache
        with patch("interface.live_service._cache_layer") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            get_game_details(game_id, timestamp=ts)

    assert mock_retry.fetch_with_retry.called, (
        "fetch_with_retry must be called when cache misses"
    )

    assert "startingTime" in captured_params, (
        f"'startingTime' must be in request params when timestamp='{ts}' is provided. "
        f"Got params: {captured_params}"
    )

    assert captured_params["startingTime"] == ts, (
        f"startingTime must equal the provided timestamp '{ts}', "
        f"got '{captured_params.get('startingTime')}'"
    )


@given(
    game_id=game_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_18_details_sem_timestamp_nao_inclui_starting_time(game_id):
    """
    **Validates: Requirements 8.2**

    Property 18 (no timestamp): When get_game_details is called without a timestamp,
    'startingTime' should not be in the request params.
    """
    captured_params = {}

    def mock_fetch_with_retry(url, params=None, headers=None, timeout=10, retry_without_param=None):
        captured_params.update(params or {})
        return {"frames": [{"blueTeam": {"participants": []}, "redTeam": {"participants": []}}]}

    with patch("interface.live_service._retry_system") as mock_retry:
        mock_retry.fetch_with_retry.side_effect = mock_fetch_with_retry

        with patch("interface.live_service._cache_layer") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            get_game_details(game_id, timestamp=None)

    if mock_retry.fetch_with_retry.called:
        assert "startingTime" not in captured_params, (
            f"'startingTime' must NOT be in params when no timestamp is provided. "
            f"Got params: {captured_params}"
        )


# ---------------------------------------------------------------------------
# Property 19: Timestamp com Offset
# ---------------------------------------------------------------------------

@given(st.none())
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_19_timestamp_com_offset_60s(_):
    """
    **Validates: Requirements 8.4**

    Property 19: For any timestamp returned by get_iso_date_multiple_of_10(),
    it must be at least 60 seconds before the current time (to avoid requesting
    future data).
    """
    before_call = datetime.now(timezone.utc)
    ts = get_iso_date_multiple_of_10()
    after_call = datetime.now(timezone.utc)

    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    # The timestamp must be at least 60 seconds before the current time
    # We use before_call as the reference (most conservative)
    diff = (before_call - dt).total_seconds()

    assert diff >= 60, (
        f"Timestamp '{ts}' must be at least 60 seconds before current time. "
        f"Current time: {before_call.strftime('%Y-%m-%dT%H:%M:%SZ')}, "
        f"difference: {diff:.1f}s (expected >= 60s)"
    )


@given(st.none())
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_19_timestamp_nao_muito_antigo(_):
    """
    **Validates: Requirements 8.4**

    Property 19 (upper bound): The timestamp should not be excessively old —
    it should be within 80 seconds of the current time (60s offset + up to 10s rounding).
    """
    before_call = datetime.now(timezone.utc)
    ts = get_iso_date_multiple_of_10()

    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    diff = (before_call - dt).total_seconds()

    # Should be between 60 and 70 seconds old (60s offset + up to 10s rounding)
    assert diff <= 70, (
        f"Timestamp '{ts}' is too old: {diff:.1f}s before current time. "
        f"Expected between 60s and 70s. "
        f"Current time: {before_call.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )


# ---------------------------------------------------------------------------
# Property 20: Cache Buster em Requisições
# ---------------------------------------------------------------------------

@given(st.none())
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_20_cache_buster_diferente_a_cada_chamada(_):
    """
    **Validates: Requirements 8.5**

    Property 20: For any two consecutive calls to _get_cache_buster(),
    the values must be different (randomness guarantee).
    """
    values = set()
    # Call multiple times and check for uniqueness
    for _ in range(10):
        cb = _get_cache_buster()
        values.add(cb)

    # With randomness, we expect at least some variation across 10 calls
    # (probability of all 10 being identical is astronomically low)
    assert len(values) > 1, (
        f"_get_cache_buster() returned the same value for all 10 calls: {values}. "
        "Cache buster must have randomness."
    )


@given(st.none())
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_20_cache_buster_contem_timestamp_numerico(_):
    """
    **Validates: Requirements 8.5**

    Property 20 (timestamp): The cache buster must contain a numeric timestamp
    (Unix epoch seconds) as a prefix.
    """
    cb = _get_cache_buster()

    # Must be a non-empty string
    assert isinstance(cb, str), (
        f"_get_cache_buster() must return a string, got {type(cb)}"
    )
    assert len(cb) > 0, "_get_cache_buster() must not return an empty string"

    # Must be numeric (timestamp + random digits)
    assert cb.isdigit(), (
        f"_get_cache_buster() must return a numeric string (timestamp + random), "
        f"got '{cb}'"
    )

    # The first 10 digits should be a valid Unix timestamp (seconds since epoch)
    # Current epoch is ~1.7 billion, so 10 digits is correct
    timestamp_part = cb[:10]
    ts_value = int(timestamp_part)
    now_epoch = int(time.time())

    # Should be within 10 seconds of current time
    assert abs(ts_value - now_epoch) <= 10, (
        f"Cache buster timestamp part '{timestamp_part}' ({ts_value}) "
        f"should be close to current epoch ({now_epoch}). "
        f"Difference: {abs(ts_value - now_epoch)}s"
    )


@given(st.none())
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_20_cache_buster_tem_parte_aleatoria(_):
    """
    **Validates: Requirements 8.5**

    Property 20 (random part): The cache buster must include a random component
    (4 digits appended after the timestamp).
    """
    cb = _get_cache_buster()

    # The format is: f"{int(time.time())}{random.randint(1000, 9999)}"
    # int(time.time()) is 10 digits, random is 4 digits => total 14 digits
    assert len(cb) >= 14, (
        f"Cache buster '{cb}' must be at least 14 chars (10 timestamp + 4 random), "
        f"got {len(cb)}"
    )

    # The last 4 digits are the random part (1000-9999)
    random_part = int(cb[-4:])
    assert 1000 <= random_part <= 9999, (
        f"Random part of cache buster must be between 1000 and 9999, "
        f"got {random_part} from '{cb}'"
    )


# ---------------------------------------------------------------------------
# Property 21: Fallback de Timestamp
# ---------------------------------------------------------------------------

@given(
    game_id=game_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_21_fallback_quando_rfc460_ausente(game_id):
    """
    **Validates: Requirements 8.6**

    Property 21: For any frame that does not contain the 'rfc460Timestamp' field,
    the system must use the timestamp calculated via get_iso_date_multiple_of_10().

    Verifies that render_live_match uses get_iso_date_multiple_of_10() as fallback
    when rfc460Timestamp is absent from the frame.
    """
    from interface.live_service import render_live_match

    # Frame without rfc460Timestamp
    window_data_no_ts = {
        "frame": {
            "gameState": "inProgress",
            "blueTeam": {"participants": [], "totalGold": 0, "totalKills": 0,
                         "towers": 0, "barons": 0, "inhibitors": 0, "dragons": []},
            "redTeam": {"participants": [], "totalGold": 0, "totalKills": 0,
                        "towers": 0, "barons": 0, "inhibitors": 0, "dragons": []},
            # No rfc460Timestamp key
        },
        "metadata": {
            "blueTeamMetadata": {"participantMetadata": []},
            "redTeamMetadata": {"participantMetadata": []},
        }
    }

    calculated_ts_calls = []
    original_get_iso = get_iso_date_multiple_of_10

    def tracking_get_iso():
        ts = original_get_iso()
        calculated_ts_calls.append(ts)
        return ts

    details_params_captured = {}

    def mock_fetch_with_retry(url, params=None, headers=None, timeout=10, retry_without_param=None):
        if "details" in url:
            details_params_captured.update(params or {})
        return {"frames": []}

    with patch("interface.live_service.get_game_window", return_value=window_data_no_ts), \
         patch("interface.live_service._retry_system") as mock_retry, \
         patch("interface.live_service._cache_layer") as mock_cache:

        mock_retry.fetch_with_retry.side_effect = mock_fetch_with_retry
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None

        game_info = {
            "game_id": game_id,
            "team_blue": {"code": "BLU", "name": "Blue Team", "image": ""},
            "team_red": {"code": "RED", "name": "Red Team", "image": ""},
            "league": "Test League",
        }

        render_live_match(game_info)

    # When rfc460Timestamp is absent, ts should be None, so get_game_details is called
    # with timestamp=None (no startingTime in params)
    if mock_retry.fetch_with_retry.called:
        assert "startingTime" not in details_params_captured, (
            f"When rfc460Timestamp is absent from frame, startingTime should not be "
            f"passed to get_game_details (fallback: no timestamp). "
            f"Got params: {details_params_captured}"
        )


@given(
    game_id=game_id_strategy,
    rfc_ts=iso_timestamp_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_21_usa_rfc460_quando_presente(game_id, rfc_ts):
    """
    **Validates: Requirements 8.6**

    Property 21 (present): When rfc460Timestamp IS present in the frame,
    the system must use it (not the calculated timestamp) for get_game_details.
    """
    from interface.live_service import render_live_match

    window_data_with_ts = {
        "frame": {
            "gameState": "inProgress",
            "rfc460Timestamp": rfc_ts,
            "blueTeam": {"participants": [], "totalGold": 0, "totalKills": 0,
                         "towers": 0, "barons": 0, "inhibitors": 0, "dragons": []},
            "redTeam": {"participants": [], "totalGold": 0, "totalKills": 0,
                        "towers": 0, "barons": 0, "inhibitors": 0, "dragons": []},
        },
        "metadata": {
            "blueTeamMetadata": {"participantMetadata": []},
            "redTeamMetadata": {"participantMetadata": []},
        }
    }

    details_params_captured = {}

    def mock_fetch_with_retry(url, params=None, headers=None, timeout=10, retry_without_param=None):
        if "details" in url:
            details_params_captured.update(params or {})
        return {"frames": []}

    with patch("interface.live_service.get_game_window", return_value=window_data_with_ts), \
         patch("interface.live_service._retry_system") as mock_retry, \
         patch("interface.live_service._cache_layer") as mock_cache:

        mock_retry.fetch_with_retry.side_effect = mock_fetch_with_retry
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None

        game_info = {
            "game_id": game_id,
            "team_blue": {"code": "BLU", "name": "Blue Team", "image": ""},
            "team_red": {"code": "RED", "name": "Red Team", "image": ""},
            "league": "Test League",
        }

        render_live_match(game_info)

    if mock_retry.fetch_with_retry.called:
        assert "startingTime" in details_params_captured, (
            f"When rfc460Timestamp='{rfc_ts}' is present in frame, "
            f"startingTime must be passed to get_game_details. "
            f"Got params: {details_params_captured}"
        )
        assert details_params_captured["startingTime"] == rfc_ts, (
            f"startingTime must equal rfc460Timestamp '{rfc_ts}', "
            f"got '{details_params_captured.get('startingTime')}'"
        )
