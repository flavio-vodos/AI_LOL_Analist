"""
Property-based tests for the /api/health endpoint.

**Validates: Requirements 7.6**

Property 16: Health Status Exposto via API
  Para qualquer requisição ao endpoint /api/health, a resposta deve conter
  o status atual de saúde da API externa incluindo is_healthy, last_check,
  e consecutive_failures.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from unittest.mock import patch, MagicMock
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from fastapi.testclient import TestClient

from api import app, health_monitor
from interface.health_monitor import HealthStatus


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Generate arbitrary consecutive_failures counts
failures_strategy = st.integers(min_value=0, max_value=20)

# Generate is_healthy values
is_healthy_strategy = st.booleans()

# Generate optional response_time_ms
response_time_strategy = st.one_of(
    st.none(),
    st.floats(min_value=0.1, max_value=5000.0, allow_nan=False, allow_infinity=False),
)

# Generate optional last_error
last_error_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100),
)


# ---------------------------------------------------------------------------
# Property 16: Health Status Exposto via API
# ---------------------------------------------------------------------------

@given(
    is_healthy=is_healthy_strategy,
    consecutive_failures=failures_strategy,
    response_time_ms=response_time_strategy,
    last_error=last_error_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_health_status_exposto_via_api(
    is_healthy, consecutive_failures, response_time_ms, last_error
):
    """
    **Validates: Requirements 7.6**

    Property 16: Para qualquer combinação de status de saúde (is_healthy,
    consecutive_failures, response_time_ms, last_error), o endpoint /api/health
    deve retornar exatamente esses valores no corpo da resposta JSON.

    Campos obrigatórios: is_healthy, last_check, consecutive_failures.
    Campos opcionais (só presentes quando não-None): last_error, response_time_ms.
    """
    fixed_time = datetime(2024, 3, 15, 10, 30, 0)

    mock_status = HealthStatus(
        is_healthy=is_healthy,
        last_check=fixed_time,
        consecutive_failures=consecutive_failures,
        last_error=last_error,
        response_time_ms=response_time_ms,
    )

    with patch.object(health_monitor, "get_status", return_value=mock_status):
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/api/health")

    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}"
    )

    body = response.json()

    # --- Required fields ---
    assert "is_healthy" in body, "Response must contain 'is_healthy'"
    assert body["is_healthy"] == is_healthy, (
        f"Expected is_healthy={is_healthy}, got {body['is_healthy']}"
    )

    assert "last_check" in body, "Response must contain 'last_check'"
    assert isinstance(body["last_check"], str), (
        f"Expected last_check to be a string (ISO 8601), got {type(body['last_check'])}"
    )
    # Verify it's a valid ISO 8601 datetime string
    parsed = datetime.fromisoformat(body["last_check"])
    assert parsed == fixed_time, (
        f"Expected last_check={fixed_time.isoformat()}, got {body['last_check']}"
    )

    assert "consecutive_failures" in body, "Response must contain 'consecutive_failures'"
    assert body["consecutive_failures"] == consecutive_failures, (
        f"Expected consecutive_failures={consecutive_failures}, got {body['consecutive_failures']}"
    )

    # --- Optional fields ---
    if last_error is not None:
        assert "last_error" in body, (
            f"Expected 'last_error' in response when last_error={last_error!r}"
        )
        assert body["last_error"] == last_error, (
            f"Expected last_error={last_error!r}, got {body['last_error']!r}"
        )
    else:
        assert "last_error" not in body, (
            f"Expected 'last_error' to be absent when last_error=None, but found it: {body.get('last_error')}"
        )

    if response_time_ms is not None:
        assert "response_time_ms" in body, (
            f"Expected 'response_time_ms' in response when response_time_ms={response_time_ms}"
        )
        assert abs(body["response_time_ms"] - response_time_ms) < 0.001, (
            f"Expected response_time_ms≈{response_time_ms}, got {body['response_time_ms']}"
        )
    else:
        assert "response_time_ms" not in body, (
            f"Expected 'response_time_ms' to be absent when None, but found it: {body.get('response_time_ms')}"
        )
