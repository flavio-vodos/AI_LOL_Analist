"""
Property-based tests for RetrySystem.

**Validates: Requirements 1.1, 1.2, 8.3**

Property 1: Retry com Fallback de Parâmetro
  Para qualquer requisição à API que retorna erro 400, quando o sistema tenta
  novamente, a requisição subsequente deve omitir o parâmetro `startingTime`.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock, call
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.retry_system import RetrySystem, RetryConfig


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

url_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-._~:/?#[]@!$&'()*+,;=%"),
    min_size=1,
    max_size=100,
).map(lambda s: f"https://example.com/{s}")

param_value_strategy = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(),
)

extra_params_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda k: k != "startingTime"),
    values=param_value_strategy,
    min_size=0,
    max_size=5,
)

starting_time_value_strategy = st.one_of(
    st.text(min_size=1, max_size=30),
    st.integers(min_value=0),
)

response_data_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=0,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 1: Retry com Fallback de Parâmetro
# ---------------------------------------------------------------------------

@given(
    url=url_strategy,
    extra_params=extra_params_strategy,
    starting_time_value=starting_time_value_strategy,
    response_data=response_data_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_retry_omits_starting_time_on_400(
    url, extra_params, starting_time_value, response_data
):
    """
    **Validates: Requirements 1.1, 1.2, 8.3**

    Property 1: Para qualquer requisição com parâmetro `startingTime` que recebe
    erro 400, a tentativa de retry subsequente NÃO deve incluir `startingTime`.
    """
    params = {**extra_params, "startingTime": starting_time_value}

    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    response_400 = MagicMock()
    response_400.status_code = 400
    response_400.text = "Bad Request"

    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = response_data

    captured_calls = []

    def fake_get(url_arg, params=None, headers=None, timeout=None):
        captured_calls.append(dict(params or {}))
        if len(captured_calls) == 1:
            return response_400
        return response_200

    with patch("interface.retry_system.requests.get", side_effect=fake_get), \
         patch("interface.retry_system.time.sleep"):

        result = system.fetch_with_retry(
            url=url,
            params=params,
            headers={},
            timeout=5,
            retry_without_param="startingTime",
        )

    # At least two calls must have been made (first 400, then retry)
    assert len(captured_calls) >= 2, (
        f"Expected at least 2 calls, got {len(captured_calls)}"
    )

    # First call must include startingTime
    assert "startingTime" in captured_calls[0], (
        "First call should include 'startingTime'"
    )

    # All subsequent calls must NOT include startingTime
    for i, call_params in enumerate(captured_calls[1:], start=2):
        assert "startingTime" not in call_params, (
            f"Call {i} should NOT include 'startingTime', but got params: {call_params}"
        )

    # The successful result should be returned
    assert result == response_data


# ---------------------------------------------------------------------------
# Property 2: Backoff Exponencial
# ---------------------------------------------------------------------------

@given(
    base_delay=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    backoff_factor=st.floats(min_value=1.5, max_value=3.0, allow_nan=False, allow_infinity=False),
    max_attempts=st.integers(min_value=2, max_value=5),
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_exponential_backoff_delays(base_delay, backoff_factor, max_attempts):
    """
    **Validates: Requirements 1.3, 1.4, 1.5, 1.6**

    Property 2: Para qualquer sequência de falhas de requisição, o delay entre
    tentativas deve seguir progressão exponencial com base backoff_factor
    (base_delay * backoff_factor^attempt), respeitando o máximo de max_attempts.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=float("inf"),  # disable cap so we can verify raw formula
        backoff_factor=backoff_factor,
    )
    system = RetrySystem(config=config)

    # Always-failing 5xx response
    response_5xx = MagicMock()
    response_5xx.status_code = 500
    response_5xx.text = "Internal Server Error"

    request_call_count = [0]

    def fake_get(url_arg, params=None, headers=None, timeout=None):
        request_call_count[0] += 1
        return response_5xx

    sleep_delays = []

    with patch("interface.retry_system.requests.get", side_effect=fake_get), \
         patch("interface.retry_system.time.sleep", side_effect=lambda d: sleep_delays.append(d)):

        result = system.fetch_with_retry(
            url="https://example.com/test",
            params={},
            headers={},
            timeout=5,
        )

    # All attempts must have been made and result must be None
    assert result is None, "Expected None when all attempts fail"
    assert request_call_count[0] == max_attempts, (
        f"Expected exactly {max_attempts} requests, got {request_call_count[0]}"
    )

    # Sleep is called between attempts: (max_attempts - 1) times
    expected_sleep_count = max_attempts - 1
    assert len(sleep_delays) == expected_sleep_count, (
        f"Expected {expected_sleep_count} sleep calls, got {len(sleep_delays)}"
    )

    # Each sleep delay must follow base_delay * (backoff_factor ** attempt)
    # where attempt is 1-indexed (as used in the loop)
    for i, actual_delay in enumerate(sleep_delays):
        attempt_number = i + 1  # loop uses range(1, max_attempts+1)
        expected_delay = base_delay * (backoff_factor ** attempt_number)
        assert abs(actual_delay - expected_delay) < 1e-9, (
            f"Sleep {i}: expected {expected_delay} (base={base_delay} * factor={backoff_factor}^{attempt_number}), "
            f"got {actual_delay}"
        )


# ---------------------------------------------------------------------------
# Property 3: Logging Completo de Requisições
# ---------------------------------------------------------------------------

import logging


@given(
    url=url_strategy,
    extra_params=extra_params_strategy,
    response_data=response_data_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_logging_completo_sucesso(url, extra_params, response_data):
    """
    **Validates: Requirements 1.7, 6.1, 6.2, 6.3**

    Property 3: Para qualquer requisição bem-sucedida, o sistema deve registrar
    no log: o endpoint (URL), os parâmetros, o status code e o tempo de resposta.
    """
    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = response_data

    with patch("interface.retry_system.requests.get", return_value=response_200), \
         patch("interface.retry_system.time.sleep"):

        with patch.object(system.logger, "info") as mock_info:
            result = system.fetch_with_retry(
                url=url,
                params=extra_params,
                headers={},
                timeout=5,
            )

    assert result == response_data

    # Collect all log messages and extras from info calls
    all_messages = []
    all_extras = []
    for call_args in mock_info.call_args_list:
        args, kwargs = call_args
        all_messages.append(args[0] if args else "")
        all_extras.append(kwargs.get("extra", {}))

    # At least one log entry must reference the URL (endpoint)
    url_logged = any(url in msg for msg in all_messages) or \
                 any(url == extra.get("url") for extra in all_extras)
    assert url_logged, (
        f"Expected URL '{url}' to appear in at least one log entry. "
        f"Messages: {all_messages}"
    )

    # At least one log entry must include status_code 200
    status_logged = any(extra.get("status_code") == 200 for extra in all_extras)
    assert status_logged, (
        f"Expected status_code=200 in at least one log entry. Extras: {all_extras}"
    )

    # At least one log entry must include response_time_ms
    response_time_logged = any("response_time_ms" in extra for extra in all_extras)
    assert response_time_logged, (
        f"Expected 'response_time_ms' in at least one log entry. Extras: {all_extras}"
    )


@given(
    url=url_strategy,
    extra_params=extra_params_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_logging_completo_falha(url, extra_params):
    """
    **Validates: Requirements 1.7, 6.1, 6.2, 6.3**

    Property 3 (falha): Para qualquer requisição que falha em todas as tentativas,
    o sistema deve registrar o erro com detalhes completos (URL, parâmetros,
    número de tentativas, último erro).
    """
    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    response_500 = MagicMock()
    response_500.status_code = 500
    response_500.text = "Internal Server Error"

    with patch("interface.retry_system.requests.get", return_value=response_500), \
         patch("interface.retry_system.time.sleep"):

        with patch.object(system.logger, "error") as mock_error:
            result = system.fetch_with_retry(
                url=url,
                params=extra_params,
                headers={},
                timeout=5,
            )

    assert result is None

    # At least one error log must have been emitted
    assert mock_error.call_count >= 1, (
        "Expected at least one error log when all attempts fail"
    )

    # Collect all error log extras
    all_error_extras = []
    all_error_messages = []
    for call_args in mock_error.call_args_list:
        args, kwargs = call_args
        all_error_messages.append(args[0] if args else "")
        all_error_extras.append(kwargs.get("extra", {}))

    # At least one error log must reference the URL
    url_in_error = any(url in msg for msg in all_error_messages) or \
                   any(url == extra.get("url") for extra in all_error_extras)
    assert url_in_error, (
        f"Expected URL '{url}' in error log. Messages: {all_error_messages}"
    )

    # At least one error log must include max_attempts or last_error details
    has_failure_details = any(
        "max_attempts" in extra or "last_error" in extra
        for extra in all_error_extras
    )
    assert has_failure_details, (
        f"Expected failure details (max_attempts or last_error) in error log. "
        f"Extras: {all_error_extras}"
    )


@given(
    url=url_strategy,
    extra_params=extra_params_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_logging_excecao_com_stack_trace(url, extra_params):
    """
    **Validates: Requirements 1.7, 6.3**

    Property 3 (exceção): Quando uma requisição lança exceção inesperada,
    o sistema deve registrar o erro com exc_info=True (stack trace completo).
    """
    config = RetryConfig(max_attempts=2, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    def raise_exception(*args, **kwargs):
        raise RuntimeError("Simulated unexpected error")

    with patch("interface.retry_system.requests.get", side_effect=raise_exception), \
         patch("interface.retry_system.time.sleep"):

        with patch.object(system.logger, "error") as mock_error:
            result = system.fetch_with_retry(
                url=url,
                params=extra_params,
                headers={},
                timeout=5,
            )

    assert result is None

    # At least one error call must have exc_info=True (stack trace)
    exc_info_logged = any(
        call_args[1].get("exc_info") is True
        for call_args in mock_error.call_args_list
    )
    assert exc_info_logged, (
        "Expected at least one error log with exc_info=True for unexpected exceptions. "
        f"Calls: {mock_error.call_args_list}"
    )
