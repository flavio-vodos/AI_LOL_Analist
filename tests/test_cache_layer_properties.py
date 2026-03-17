"""
Property-based tests for CacheLayer.

**Validates: Requirements 2.3**

Property 4: Cache Retorna Dados Válidos
  Para qualquer chave de cache com dados não expirados, o sistema deve retornar
  os dados em cache sem fazer nova requisição à API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.cache_layer import CacheLayer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid cache keys: any non-empty string that is not "unknown"
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
        max_size=10,
    ),
    st.text(min_size=0, max_size=100),
    st.integers(),
    st.lists(st.integers(), min_size=0, max_size=10),
)

# TTL values: positive integers (large enough to not expire during test)
ttl_strategy = st.integers(min_value=10, max_value=3600)


# ---------------------------------------------------------------------------
# Property 4: Cache Retorna Dados Válidos
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
def test_property_cache_returns_valid_data_without_api_call(key, value, ttl):
    """
    **Validates: Requirements 2.3**

    Property 4: Para qualquer chave de cache com dados não expirados, o sistema
    deve retornar os dados em cache sem fazer nova requisição à API.

    Verifica que:
    1. Os dados retornados são iguais aos dados armazenados.
    2. Uma função de API mockada NÃO é chamada quando há cache hit.
    """
    cache = CacheLayer()

    # Mock de função de API que NÃO deve ser chamada em cache hit
    mock_api_fn = MagicMock(return_value={"fresh": "data"})

    # Armazena dados no cache com TTL suficientemente grande
    cache.set(key, value, ttl_seconds=ttl)

    # Simula o padrão de uso: verifica cache antes de chamar API
    cached_result = cache.get(key)

    if cached_result is not None:
        # Cache hit: não deve chamar a API
        result = cached_result
    else:
        # Cache miss: chamaria a API (não deve acontecer aqui)
        result = mock_api_fn(key)

    # Os dados retornados devem ser iguais aos armazenados
    assert result == value, (
        f"Expected cached value {value!r}, got {result!r} for key {key!r}"
    )

    # A função de API NÃO deve ter sido chamada (cache hit)
    mock_api_fn.assert_not_called()


@given(
    key=cache_key_strategy,
    value=cache_value_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_hit_identity(key, value):
    """
    **Validates: Requirements 2.3**

    Property 4 (identidade): Para qualquer dado armazenado no cache com TTL
    padrão (não expirado), o valor retornado deve ser idêntico ao valor
    armazenado.
    """
    cache = CacheLayer()

    # Armazena com TTL grande para garantir que não expira durante o teste
    cache.set(key, value, ttl_seconds=3600)

    retrieved = cache.get(key)

    assert retrieved is not None, (
        f"Expected cache hit for key {key!r}, but got None"
    )
    assert retrieved == value, (
        f"Cache returned {retrieved!r} but expected {value!r} for key {key!r}"
    )


# ---------------------------------------------------------------------------
# Property 5: Cache Expira e Revalida
# ---------------------------------------------------------------------------

@given(
    key=cache_key_strategy,
    value=cache_value_strategy,
    new_value=cache_value_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_cache_expires_and_revalidates(key, value, new_value):
    """
    **Validates: Requirements 2.4**

    Property 5: Para qualquer chave de cache com dados expirados (TTL excedido),
    o sistema deve retornar None e permitir que novos dados sejam armazenados e
    recuperados corretamente.

    Verifica que:
    1. Após expiração (simulada via created_at no passado), cache.get retorna None.
    2. Novos dados podem ser armazenados e recuperados após a expiração.
    """
    from datetime import timedelta

    cache = CacheLayer()

    # Armazena dados com TTL de 60 segundos
    cache.set(key, value, ttl_seconds=60)

    # Simula expiração: retrocede created_at em 120 segundos (além do TTL)
    with cache._lock:
        entry = cache._cache[key]
        entry.created_at = entry.created_at - timedelta(seconds=120)

    # Após expiração, get deve retornar None
    expired_result = cache.get(key)
    assert expired_result is None, (
        f"Expected None for expired key {key!r}, but got {expired_result!r}"
    )

    # A entrada expirada deve ter sido removida do cache
    with cache._lock:
        assert key not in cache._cache, (
            f"Expired entry for key {key!r} should have been removed from cache"
        )

    # Novos dados podem ser armazenados e recuperados após expiração
    cache.set(key, new_value, ttl_seconds=3600)
    revalidated_result = cache.get(key)

    assert revalidated_result is not None, (
        f"Expected new data for key {key!r} after revalidation, but got None"
    )
    assert revalidated_result == new_value, (
        f"Expected new value {new_value!r} after revalidation, got {revalidated_result!r}"
    )


# ---------------------------------------------------------------------------
# Property 6: Cache Usa Game_ID como Chave
# ---------------------------------------------------------------------------

@given(
    game_id_a=cache_key_strategy.filter(lambda k: k != "unknown"),
    game_id_b=cache_key_strategy.filter(lambda k: k != "unknown"),
    value_a=cache_value_strategy,
    value_b=cache_value_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_different_game_ids_are_independent(game_id_a, game_id_b, value_a, value_b):
    """
    **Validates: Requirements 2.5**

    Property 6: Para quaisquer dois game_ids distintos, as entradas de cache
    devem ser completamente independentes — armazenar ou remover dados de um
    game_id não deve afetar o outro.
    """
    # Only test when the two game_ids are actually different
    if game_id_a == game_id_b:
        return

    cache = CacheLayer()

    cache.set(game_id_a, value_a, ttl_seconds=3600)
    cache.set(game_id_b, value_b, ttl_seconds=3600)

    # Each game_id must return its own value
    assert cache.get(game_id_a) == value_a, (
        f"game_id_a={game_id_a!r}: expected {value_a!r}, got {cache.get(game_id_a)!r}"
    )
    assert cache.get(game_id_b) == value_b, (
        f"game_id_b={game_id_b!r}: expected {value_b!r}, got {cache.get(game_id_b)!r}"
    )

    # Deleting game_id_a must not affect game_id_b
    cache.delete(game_id_a)
    assert cache.get(game_id_a) is None, (
        f"After delete, game_id_a={game_id_a!r} should be None"
    )
    assert cache.get(game_id_b) == value_b, (
        f"Deleting game_id_a={game_id_a!r} must not affect game_id_b={game_id_b!r}"
    )


@given(
    game_id_a=cache_key_strategy,
    game_id_b=cache_key_strategy,
    value_a=cache_value_strategy,
    new_value_a=cache_value_strategy,
)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_setting_one_game_id_does_not_affect_another(
    game_id_a, game_id_b, value_a, new_value_a
):
    """
    **Validates: Requirements 2.5**

    Property 6: Armazenar dados para game_id A não deve alterar os dados
    armazenados para game_id B.
    """
    if game_id_a == game_id_b:
        return

    cache = CacheLayer()

    # Store initial value for B
    cache.set(game_id_b, value_a, ttl_seconds=3600)
    value_b_before = cache.get(game_id_b)

    # Now set/overwrite A with a different value
    cache.set(game_id_a, new_value_a, ttl_seconds=3600)

    # B must remain unchanged
    value_b_after = cache.get(game_id_b)
    assert value_b_before == value_b_after, (
        f"Setting game_id_a={game_id_a!r} changed game_id_b={game_id_b!r}: "
        f"before={value_b_before!r}, after={value_b_after!r}"
    )


@given(value=cache_value_strategy)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_unknown_game_id_is_rejected(value):
    """
    **Validates: Requirements 2.5, 2.7**

    Property 6: Quando o game_id é "unknown", o Cache_Layer NÃO deve armazenar
    dados. cache.get("unknown") deve sempre retornar None.
    """
    cache = CacheLayer()

    cache.set("unknown", value, ttl_seconds=3600)

    result = cache.get("unknown")
    assert result is None, (
        f"cache.get('unknown') should return None, but got {result!r}"
    )

    # Internal store must also be empty for "unknown"
    with cache._lock:
        assert "unknown" not in cache._cache, (
            "Key 'unknown' must never be stored in the internal cache dict"
        )


# ---------------------------------------------------------------------------
# Property 7: Cache Armazena Timestamp
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
def test_property_cache_stores_timestamp(key, value, ttl):
    """
    **Validates: Requirements 2.6**

    Property 7: Para qualquer entrada criada no cache, deve existir um campo
    `created_at` com o timestamp de criação para cálculo de expiração.

    Verifica que:
    1. O campo `created_at` existe na entrada do cache.
    2. `created_at` é um objeto `datetime`.
    3. `created_at` é próximo de `datetime.now()` (dentro de 5 segundos).
    4. O campo `ttl_seconds` é armazenado corretamente.
    """
    from datetime import datetime, timedelta

    cache = CacheLayer()
    before = datetime.now()
    cache.set(key, value, ttl_seconds=ttl)
    after = datetime.now()

    with cache._lock:
        assert key in cache._cache, (
            f"Key {key!r} should be present in internal cache after set()"
        )
        entry = cache._cache[key]

    # created_at deve existir e ser um datetime
    assert hasattr(entry, "created_at"), (
        "CacheEntry must have a 'created_at' field"
    )
    assert isinstance(entry.created_at, datetime), (
        f"'created_at' must be a datetime, got {type(entry.created_at)}"
    )

    # created_at deve estar dentro do intervalo [before, after]
    assert before - timedelta(seconds=1) <= entry.created_at <= after + timedelta(seconds=1), (
        f"'created_at' {entry.created_at} is not close to now() "
        f"(expected between {before} and {after})"
    )

    # ttl_seconds deve ser armazenado corretamente
    assert entry.ttl_seconds == ttl, (
        f"Expected ttl_seconds={ttl}, got {entry.ttl_seconds}"
    )
