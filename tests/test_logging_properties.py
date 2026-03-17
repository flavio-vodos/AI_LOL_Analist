"""
Property-based tests for logging of cache operations.

**Validates: Requirements 6.4**

Property 10: Logging de Operações de Cache
  Para qualquer operação de cache (hit, miss, expiration, set), deve haver uma
  entrada correspondente no log com nível DEBUG.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import timedelta
from unittest.mock import patch, MagicMock, call
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.cache_layer import CacheLayer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid cache keys: non-empty strings that are not "unknown"
cache_key_strategy = st.text(
    min_size=1,
    max_size=50,
).filter(lambda k: k != "unknown")

# Cache values: dicts, strings, integers, lists
cache_value_strategy = st.one_of(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=0,
        max_size=5,
    ),
    st.text(min_size=0, max_size=50),
    st.integers(),
    st.lists(st.integers(), min_size=0, max_size=5),
)

# TTL values: large enough to not expire during test
ttl_strategy = st.integers(min_value=10, max_value=3600)


# ---------------------------------------------------------------------------
# Property 10: Logging de Operações de Cache — Cache HIT
# ---------------------------------------------------------------------------

@given(
    key=cache_key_strategy,
    value=cache_value_strategy,
    ttl=ttl_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_hit_emits_debug_log(key, value, ttl):
    """
    **Validates: Requirements 6.4**

    Property 10 (hit): Para qualquer chave de cache com dados não expirados,
    ao chamar cache.get(), deve haver uma entrada no log com nível DEBUG
    indicando cache hit.
    """
    cache = CacheLayer()
    cache.set(key, value, ttl_seconds=ttl)

    with patch.object(cache.logger, "debug") as mock_debug:
        result = cache.get(key)

    # The get must return the stored value (confirming it's a hit)
    assert result == value, (
        f"Expected cache hit returning {value!r}, got {result!r}"
    )

    # At least one DEBUG log must have been emitted
    assert mock_debug.call_count >= 1, (
        f"Expected at least one DEBUG log on cache hit for key {key!r}, "
        f"but logger.debug was not called"
    )

    # Collect all messages and extras from debug calls
    all_messages = []
    all_extras = []
    for call_args in mock_debug.call_args_list:
        args, kwargs = call_args
        all_messages.append(args[0] if args else "")
        all_extras.append(kwargs.get("extra", {}))

    # At least one log entry must indicate a cache hit (cache_hit=True)
    hit_logged = any(extra.get("cache_hit") is True for extra in all_extras)
    assert hit_logged, (
        f"Expected a DEBUG log entry with cache_hit=True for key {key!r}. "
        f"Extras: {all_extras}"
    )


# ---------------------------------------------------------------------------
# Property 10: Logging de Operações de Cache — Cache MISS
# ---------------------------------------------------------------------------

@given(
    key=cache_key_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_miss_emits_debug_log(key):
    """
    **Validates: Requirements 6.4**

    Property 10 (miss): Para qualquer chave inexistente no cache, ao chamar
    cache.get(), deve haver uma entrada no log com nível DEBUG indicando
    cache miss.
    """
    cache = CacheLayer()  # empty cache — guaranteed miss

    with patch.object(cache.logger, "debug") as mock_debug:
        result = cache.get(key)

    # The get must return None (confirming it's a miss)
    assert result is None, (
        f"Expected None on cache miss for key {key!r}, got {result!r}"
    )

    # At least one DEBUG log must have been emitted
    assert mock_debug.call_count >= 1, (
        f"Expected at least one DEBUG log on cache miss for key {key!r}, "
        f"but logger.debug was not called"
    )

    # Collect extras from debug calls
    all_extras = []
    for call_args in mock_debug.call_args_list:
        args, kwargs = call_args
        all_extras.append(kwargs.get("extra", {}))

    # At least one log entry must indicate a cache miss (cache_hit=False)
    miss_logged = any(extra.get("cache_hit") is False for extra in all_extras)
    assert miss_logged, (
        f"Expected a DEBUG log entry with cache_hit=False for key {key!r}. "
        f"Extras: {all_extras}"
    )


# ---------------------------------------------------------------------------
# Property 10: Logging de Operações de Cache — Cache EXPIRATION
# ---------------------------------------------------------------------------

@given(
    key=cache_key_strategy,
    value=cache_value_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_expiration_emits_debug_log(key, value):
    """
    **Validates: Requirements 6.4**

    Property 10 (expiration): Para qualquer chave de cache com dados expirados,
    ao chamar cache.get(), deve haver uma entrada no log com nível DEBUG
    indicando expiração.
    """
    cache = CacheLayer()
    cache.set(key, value, ttl_seconds=60)

    # Simulate expiry by backdating created_at beyond TTL
    with cache._lock:
        entry = cache._cache[key]
        entry.created_at = entry.created_at - timedelta(seconds=120)

    with patch.object(cache.logger, "debug") as mock_debug:
        result = cache.get(key)

    # The get must return None (confirming expiration)
    assert result is None, (
        f"Expected None for expired key {key!r}, got {result!r}"
    )

    # At least one DEBUG log must have been emitted
    assert mock_debug.call_count >= 1, (
        f"Expected at least one DEBUG log on cache expiration for key {key!r}, "
        f"but logger.debug was not called"
    )

    # Collect extras from debug calls
    all_extras = []
    for call_args in mock_debug.call_args_list:
        args, kwargs = call_args
        all_extras.append(kwargs.get("extra", {}))

    # At least one log entry must indicate expiration (expired=True)
    expiration_logged = any(extra.get("expired") is True for extra in all_extras)
    assert expiration_logged, (
        f"Expected a DEBUG log entry with expired=True for key {key!r}. "
        f"Extras: {all_extras}"
    )


# ---------------------------------------------------------------------------
# Property 10: All cache operation log entries must be at DEBUG level
# ---------------------------------------------------------------------------

@given(
    key=cache_key_strategy,
    value=cache_value_strategy,
    ttl=ttl_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_operations_log_only_at_debug_level(key, value, ttl):
    """
    **Validates: Requirements 6.4**

    Property 10 (level): Para qualquer operação de cache (hit, miss, set),
    os logs emitidos devem ser exclusivamente em nível DEBUG — nunca INFO,
    WARNING ou ERROR.
    """
    cache = CacheLayer()

    # Use a real MemoryHandler to capture actual log records
    log_records: list[logging.LogRecord] = []

    class CapturingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(record)

    handler = CapturingHandler()
    handler.setLevel(logging.DEBUG)
    cache.logger.addHandler(handler)
    cache.logger.setLevel(logging.DEBUG)

    try:
        # Perform set (should log DEBUG)
        cache.set(key, value, ttl_seconds=ttl)

        # Perform get — cache hit (should log DEBUG)
        cache.get(key)

        # Perform get on empty key — cache miss (should log DEBUG)
        cache.get(key + "_nonexistent_suffix")
    finally:
        cache.logger.removeHandler(handler)

    # All captured records must be at DEBUG level
    assert len(log_records) >= 1, (
        "Expected at least one log record from cache operations"
    )

    non_debug = [
        r for r in log_records if r.levelno != logging.DEBUG
    ]
    assert non_debug == [], (
        f"All cache operation logs must be at DEBUG level. "
        f"Found non-DEBUG records: {[(r.levelname, r.getMessage()) for r in non_debug]}"
    )


# ===========================================================================
# Property 12: Níveis de Log Apropriados
# ===========================================================================
# **Validates: Requirements 6.6**
#
# Para qualquer evento registrado no log, o nível deve ser apropriado:
#   - DEBUG  → detalhes técnicos
#   - INFO   → operações normais (requisição bem-sucedida)
#   - WARNING → situações anormais não críticas (falha parcial, erro 400)
#   - ERROR  → falhas (todas as tentativas esgotadas, exceção inesperada)
# ===========================================================================

import requests as _requests
from unittest.mock import patch as _patch, MagicMock as _MagicMock
from interface.retry_system import RetrySystem, RetryConfig
from interface.health_monitor import HealthMonitor


# ---------------------------------------------------------------------------
# Strategies for Property 12
# ---------------------------------------------------------------------------

_url_strategy = st.builds(
    lambda path: f"https://example.com/{path}",
    path=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
        min_size=1,
        max_size=30,
    ),
)

_response_data_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10),
    values=st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=0,
    max_size=5,
)

_get_live_url_strategy = st.builds(
    lambda host: f"https://{host}/getLive",
    host=st.sampled_from([
        "feed.lolesports.com",
        "api.lolesports.com",
        "esports.example.com",
    ]),
)


# ---------------------------------------------------------------------------
# Helper: capture log records from a logger
# ---------------------------------------------------------------------------

class _CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


# ---------------------------------------------------------------------------
# Property 12a: RetrySystem — requisição bem-sucedida → INFO
# ---------------------------------------------------------------------------

@given(
    url=_url_strategy,
    response_data=_response_data_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_retry_success_logs_at_info(url, response_data):
    """
    **Validates: Requirements 6.6**

    Property 12 (retry success): Para qualquer requisição bem-sucedida ao
    RetrySystem, deve haver pelo menos uma entrada de log em nível INFO
    confirmando o sucesso — e nenhuma entrada em nível ERROR.
    """
    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    handler = _CapturingHandler()
    system.logger.addHandler(handler)
    system.logger.setLevel(logging.DEBUG)

    response_200 = _MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = response_data

    try:
        with _patch("interface.retry_system.requests.get", return_value=response_200), \
             _patch("interface.retry_system.time.sleep"):
            result = system.fetch_with_retry(url=url, params={}, headers={}, timeout=5)
    finally:
        system.logger.removeHandler(handler)

    assert result == response_data

    info_records = [r for r in handler.records if r.levelno == logging.INFO]
    error_records = [r for r in handler.records if r.levelno == logging.ERROR]

    assert len(info_records) >= 1, (
        f"Expected at least one INFO log on success, got none. "
        f"Records: {[(r.levelname, r.getMessage()) for r in handler.records]}"
    )
    assert len(error_records) == 0, (
        f"Expected no ERROR logs on success, but got: "
        f"{[(r.levelname, r.getMessage()) for r in error_records]}"
    )


# ---------------------------------------------------------------------------
# Property 12b: RetrySystem — falha parcial (HTTP 5xx) → WARNING
# ---------------------------------------------------------------------------

@given(
    url=_url_strategy,
    response_data=_response_data_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_retry_partial_failure_logs_at_warning(url, response_data):
    """
    **Validates: Requirements 6.6**

    Property 12 (retry partial failure): Quando uma tentativa falha com HTTP 5xx
    mas uma tentativa posterior tem sucesso, deve haver pelo menos uma entrada
    WARNING (para a falha) e pelo menos uma INFO (para o sucesso) — sem ERROR.
    """
    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    handler = _CapturingHandler()
    system.logger.addHandler(handler)
    system.logger.setLevel(logging.DEBUG)

    response_500 = _MagicMock()
    response_500.status_code = 500
    response_500.text = "Internal Server Error"

    response_200 = _MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = response_data

    call_count = [0]

    def fake_get(*args, **kwargs):
        call_count[0] += 1
        return response_500 if call_count[0] == 1 else response_200

    try:
        with _patch("interface.retry_system.requests.get", side_effect=fake_get), \
             _patch("interface.retry_system.time.sleep"):
            result = system.fetch_with_retry(url=url, params={}, headers={}, timeout=5)
    finally:
        system.logger.removeHandler(handler)

    assert result == response_data

    warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
    info_records = [r for r in handler.records if r.levelno == logging.INFO]
    error_records = [r for r in handler.records if r.levelno == logging.ERROR]

    assert len(warning_records) >= 1, (
        f"Expected at least one WARNING log for the failed attempt. "
        f"Records: {[(r.levelname, r.getMessage()) for r in handler.records]}"
    )
    assert len(info_records) >= 1, (
        f"Expected at least one INFO log for the successful attempt. "
        f"Records: {[(r.levelname, r.getMessage()) for r in handler.records]}"
    )
    assert len(error_records) == 0, (
        f"Expected no ERROR logs when recovery succeeds, but got: "
        f"{[(r.levelname, r.getMessage()) for r in error_records]}"
    )


# ---------------------------------------------------------------------------
# Property 12c: RetrySystem — todas as tentativas falham → ERROR final
# ---------------------------------------------------------------------------

@given(
    url=_url_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_retry_all_attempts_fail_logs_error(url):
    """
    **Validates: Requirements 6.6**

    Property 12 (retry all fail): Quando todas as tentativas do RetrySystem
    falham, o erro final deve ser registrado em nível ERROR.
    """
    config = RetryConfig(max_attempts=3, base_delay=0.0, backoff_factor=0.0)
    system = RetrySystem(config=config)

    handler = _CapturingHandler()
    system.logger.addHandler(handler)
    system.logger.setLevel(logging.DEBUG)

    response_500 = _MagicMock()
    response_500.status_code = 500
    response_500.text = "Internal Server Error"

    try:
        with _patch("interface.retry_system.requests.get", return_value=response_500), \
             _patch("interface.retry_system.time.sleep"):
            result = system.fetch_with_retry(url=url, params={}, headers={}, timeout=5)
    finally:
        system.logger.removeHandler(handler)

    assert result is None

    error_records = [r for r in handler.records if r.levelno == logging.ERROR]

    assert len(error_records) >= 1, (
        f"Expected at least one ERROR log when all attempts fail. "
        f"Records: {[(r.levelname, r.getMessage()) for r in handler.records]}"
    )


# ---------------------------------------------------------------------------
# Property 12d: HealthMonitor — status muda para unhealthy → WARNING/ERROR
# ---------------------------------------------------------------------------

@given(
    check_url=_get_live_url_strategy,
    failure_threshold=st.integers(min_value=2, max_value=5),
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_health_monitor_unhealthy_logs_warning_or_error(
    check_url, failure_threshold
):
    """
    **Validates: Requirements 6.6**

    Property 12 (health unhealthy): Quando o HealthMonitor marca o status como
    "unhealthy" (após failure_threshold falhas consecutivas), deve haver pelo
    menos uma entrada de log em nível WARNING ou ERROR — nunca apenas DEBUG/INFO.
    """
    monitor = HealthMonitor(
        check_url=check_url,
        failure_threshold=failure_threshold,
    )

    handler = _CapturingHandler()
    monitor.logger.addHandler(handler)
    monitor.logger.setLevel(logging.DEBUG)

    response_error = _MagicMock()
    response_error.status_code = 503
    response_error.text = "Service Unavailable"

    try:
        with _patch("interface.health_monitor.requests.get", return_value=response_error):
            # Trigger exactly failure_threshold checks to reach unhealthy state
            for _ in range(failure_threshold):
                monitor._check_health()
    finally:
        monitor.logger.removeHandler(handler)

    status = monitor.get_status()
    assert not status.is_healthy, (
        f"Expected unhealthy status after {failure_threshold} failures"
    )

    elevated_records = [
        r for r in handler.records
        if r.levelno >= logging.WARNING
    ]

    assert len(elevated_records) >= 1, (
        f"Expected at least one WARNING or ERROR log when status becomes unhealthy. "
        f"Records: {[(r.levelname, r.getMessage()) for r in handler.records]}"
    )


# ===========================================================================
# Property 13: Logs Contêm Identificadores
# ===========================================================================
# **Validates: Requirements 6.7**
#
# Para qualquer mensagem de log relacionada a uma partida específica,
# deve conter os campos `game_id` (e `match_id` quando disponível) quando
# disponíveis — ou seja, o game_id passado para get_game_window / get_game_details
# deve aparecer nos registros de log emitidos por essas funções.
# ===========================================================================

import interface.live_service as _live_service


# ---------------------------------------------------------------------------
# Strategy for Property 13
# ---------------------------------------------------------------------------

# Valid game_ids: non-empty strings, not "unknown"
_game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=1,
    max_size=40,
).filter(lambda g: g != "unknown" and g.strip() != "")


# ---------------------------------------------------------------------------
# Helper: capture log records from a logger
# ---------------------------------------------------------------------------

class _LogCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


# ---------------------------------------------------------------------------
# Property 13a: get_game_window — logs contêm game_id
# ---------------------------------------------------------------------------

@given(game_id=_game_id_strategy)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_get_game_window_logs_contain_game_id(game_id):
    """
    **Validates: Requirements 6.7**

    Property 13 (window): Para qualquer game_id válido passado a
    get_game_window(), todos os registros de log emitidos pela função
    devem conter o campo game_id igual ao valor fornecido.
    """
    handler = _LogCapture()
    _live_service.logger.addHandler(handler)
    _live_service.logger.setLevel(logging.DEBUG)

    # Mock cache miss so the function proceeds to log
    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # cache miss

    # Mock retry system to return None (simulates API failure path)
    mock_retry = MagicMock()
    mock_retry.fetch_with_retry.return_value = None

    try:
        with patch.object(_live_service, "_cache_layer", mock_cache), \
             patch.object(_live_service, "_retry_system", mock_retry):
            _live_service.get_game_window(game_id)
    finally:
        _live_service.logger.removeHandler(handler)

    # Must have emitted at least one log record
    assert len(handler.records) >= 1, (
        f"Expected at least one log record from get_game_window({game_id!r}), "
        f"but none were emitted"
    )

    # Every record emitted by this function must carry game_id
    for record in handler.records:
        assert hasattr(record, "game_id"), (
            f"Log record is missing 'game_id' field. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )
        assert record.game_id == game_id, (
            f"Expected record.game_id == {game_id!r}, "
            f"got {record.game_id!r}. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )


# ---------------------------------------------------------------------------
# Property 13b: get_game_details — logs contêm game_id
# ---------------------------------------------------------------------------

@given(game_id=_game_id_strategy)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_get_game_details_logs_contain_game_id(game_id):
    """
    **Validates: Requirements 6.7**

    Property 13 (details): Para qualquer game_id válido passado a
    get_game_details(), todos os registros de log emitidos pela função
    devem conter o campo game_id igual ao valor fornecido.
    """
    handler = _LogCapture()
    _live_service.logger.addHandler(handler)
    _live_service.logger.setLevel(logging.DEBUG)

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # cache miss

    mock_retry = MagicMock()
    mock_retry.fetch_with_retry.return_value = None

    try:
        with patch.object(_live_service, "_cache_layer", mock_cache), \
             patch.object(_live_service, "_retry_system", mock_retry):
            _live_service.get_game_details(game_id)
    finally:
        _live_service.logger.removeHandler(handler)

    assert len(handler.records) >= 1, (
        f"Expected at least one log record from get_game_details({game_id!r}), "
        f"but none were emitted"
    )

    for record in handler.records:
        assert hasattr(record, "game_id"), (
            f"Log record is missing 'game_id' field. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )
        assert record.game_id == game_id, (
            f"Expected record.game_id == {game_id!r}, "
            f"got {record.game_id!r}. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )


# ---------------------------------------------------------------------------
# Property 13c: get_game_window cache hit — log contém game_id
# ---------------------------------------------------------------------------

@given(
    game_id=_game_id_strategy,
    cached_value=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.one_of(st.text(), st.integers()),
        min_size=0,
        max_size=3,
    ),
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_get_game_window_cache_hit_log_contains_game_id(game_id, cached_value):
    """
    **Validates: Requirements 6.7**

    Property 13 (window cache hit): Mesmo quando há cache hit em
    get_game_window(), o log de cache hit deve conter o game_id correto.
    """
    handler = _LogCapture()
    _live_service.logger.addHandler(handler)
    _live_service.logger.setLevel(logging.DEBUG)

    mock_cache = MagicMock()
    mock_cache.get.return_value = cached_value  # cache hit

    try:
        with patch.object(_live_service, "_cache_layer", mock_cache):
            result = _live_service.get_game_window(game_id)
    finally:
        _live_service.logger.removeHandler(handler)

    assert result == cached_value

    assert len(handler.records) >= 1, (
        f"Expected at least one log record on cache hit for game_id={game_id!r}"
    )

    for record in handler.records:
        assert hasattr(record, "game_id"), (
            f"Log record missing 'game_id'. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )
        assert record.game_id == game_id, (
            f"Expected record.game_id == {game_id!r}, got {record.game_id!r}"
        )


# ---------------------------------------------------------------------------
# Property 13d: get_game_details cache hit — log contém game_id
# ---------------------------------------------------------------------------

@given(
    game_id=_game_id_strategy,
    cached_value=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.one_of(st.text(), st.integers()),
        min_size=0,
        max_size=3,
    ),
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_get_game_details_cache_hit_log_contains_game_id(game_id, cached_value):
    """
    **Validates: Requirements 6.7**

    Property 13 (details cache hit): Mesmo quando há cache hit em
    get_game_details(), o log de cache hit deve conter o game_id correto.
    """
    handler = _LogCapture()
    _live_service.logger.addHandler(handler)
    _live_service.logger.setLevel(logging.DEBUG)

    mock_cache = MagicMock()
    mock_cache.get.return_value = cached_value  # cache hit

    try:
        with patch.object(_live_service, "_cache_layer", mock_cache):
            result = _live_service.get_game_details(game_id)
    finally:
        _live_service.logger.removeHandler(handler)

    assert result == cached_value

    assert len(handler.records) >= 1, (
        f"Expected at least one log record on cache hit for game_id={game_id!r}"
    )

    for record in handler.records:
        assert hasattr(record, "game_id"), (
            f"Log record missing 'game_id'. "
            f"Record: level={record.levelname}, msg={record.getMessage()!r}"
        )
        assert record.game_id == game_id, (
            f"Expected record.game_id == {game_id!r}, got {record.game_id!r}"
        )
