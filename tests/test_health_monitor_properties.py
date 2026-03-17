"""
Property-based tests for HealthMonitor.

**Validates: Requirements 7.2**

Property 14: Health Check Usa Endpoint Correto
  Para qualquer health check executado pelo Health Monitor, a requisição deve
  ser feita ao endpoint getLive configurado no check_url.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.health_monitor import HealthMonitor


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Generate valid getLive URLs with various base domains and path variations
get_live_url_strategy = st.builds(
    lambda host, suffix: f"https://{host}/getLive{suffix}",
    host=st.sampled_from([
        "feed.lolesports.com/livestats/v1",
        "api.lolesports.com/v1",
        "esports.example.com",
        "live.example.org",
    ]),
    suffix=st.one_of(
        st.just(""),
        st.just("?hl=pt-BR"),
        st.just("?hl=en-US"),
        st.builds(
            lambda k, v: f"?{k}={v}",
            k=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
            v=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Property 14: Health Check Usa Endpoint Correto
# ---------------------------------------------------------------------------

@given(check_url=get_live_url_strategy)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_health_check_usa_endpoint_correto(check_url):
    """
    **Validates: Requirements 7.2**

    Property 14: Para qualquer health check executado pelo Health Monitor,
    a requisição HTTP deve ser feita exatamente ao check_url configurado,
    que deve conter o endpoint getLive.
    """
    monitor = HealthMonitor(check_url=check_url)

    response_200 = MagicMock()
    response_200.status_code = 200

    captured_urls = []

    def fake_get(url, timeout=None, **kwargs):
        captured_urls.append(url)
        return response_200

    with patch("interface.health_monitor.requests.get", side_effect=fake_get):
        monitor._check_health()

    # Exactly one request must have been made
    assert len(captured_urls) == 1, (
        f"Expected exactly 1 HTTP request, got {len(captured_urls)}"
    )

    # The request must be made to the configured check_url
    assert captured_urls[0] == check_url, (
        f"Expected request to '{check_url}', but got '{captured_urls[0]}'"
    )

    # The URL must contain 'getLive' (requirement 7.2)
    assert "getLive" in captured_urls[0], (
        f"Expected URL to contain 'getLive', but got '{captured_urls[0]}'"
    )


# ---------------------------------------------------------------------------
# Property 15: Health Status Reflete Sucesso
# ---------------------------------------------------------------------------

# Strategy: generate 2xx status codes
success_status_code_strategy = st.integers(min_value=200, max_value=299)

# Strategy: generate a positive number of pre-existing consecutive failures
pre_existing_failures_strategy = st.integers(min_value=1, max_value=10)


@given(
    check_url=get_live_url_strategy,
    status_code=success_status_code_strategy,
    pre_failures=pre_existing_failures_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_health_status_reflete_sucesso(check_url, status_code, pre_failures):
    """
    **Validates: Requirements 7.3**

    Property 15: Para qualquer resposta bem-sucedida (status 2xx) do health check,
    o status deve ser marcado como "healthy" e o contador de falhas deve ser
    resetado para 0, independentemente de quantas falhas consecutivas existiam antes.
    """
    monitor = HealthMonitor(check_url=check_url)

    # Simulate pre-existing consecutive failures
    with monitor._lock:
        monitor._status.consecutive_failures = pre_failures
        monitor._status.is_healthy = False

    response_mock = MagicMock()
    response_mock.status_code = status_code

    with patch("interface.health_monitor.requests.get", return_value=response_mock):
        monitor._check_health()

    status = monitor.get_status()

    assert status.is_healthy is True, (
        f"Expected is_healthy=True after {status_code} response, got False "
        f"(pre_failures={pre_failures})"
    )
    assert status.consecutive_failures == 0, (
        f"Expected consecutive_failures=0 after {status_code} response, "
        f"got {status.consecutive_failures} (pre_failures={pre_failures})"
    )
