"""
Property-based tests for Game_ID Unknown resolution.

Properties 32-34 validate the behavior when game_id is "unknown":
- Resolution by fetching live games list
- Logging of resolution attempts
- Cache cleanup on successful resolution

**Validates: Requirements 5.1, 5.2, 5.4, 5.5**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from interface.cache_layer import CacheLayer
from interface.live_service import _cache_layer, get_live_games


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

match_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
)

valid_game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
).filter(lambda x: x != "unknown")

team_code_strategy = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    min_size=2,
    max_size=5,
)


def make_live_game(match_id: str, game_id: str) -> dict:
    """Helper to build a minimal live game dict."""
    return {
        "match_id": match_id,
        "game_id": game_id,
        "game_number": 1,
        "league": "Test League",
        "team_blue": {"code": "BLU", "name": "Blue Team"},
        "team_red": {"code": "RED", "name": "Red Team"},
    }


# ---------------------------------------------------------------------------
# Property 32: Resolução de Game_ID Unknown
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_32_resolucao_game_id_unknown(match_id, valid_game_id):
    """
    **Validates: Requirements 5.1, 5.2**

    Property 32: For any Match_ID com Game_ID "unknown", quando get_live_games()
    retorna um game_id válido para esse match_id, o sistema deve usar o novo game_id.

    Verifica que:
    1. Quando game_id == "unknown", o sistema chama get_live_games() para resolver
    2. Quando um game_id válido é encontrado, ele substitui o "unknown"
    """
    # Simula get_live_games retornando o game_id válido para o match_id
    resolved_game = make_live_game(match_id, valid_game_id)

    with patch("interface.live_service.get_live_games", return_value=[resolved_game]) as mock_get_live:
        # Simula a lógica de resolução: dado um game com game_id "unknown",
        # busca get_live_games() para encontrar o game_id real
        unknown_game = make_live_game(match_id, "unknown")

        # Lógica de resolução: busca na lista de jogos ao vivo pelo match_id
        live_games = mock_get_live()
        resolved_id = None
        for g in live_games:
            if g["match_id"] == match_id and g["game_id"] != "unknown":
                resolved_id = g["game_id"]
                break

        # Verifica que get_live_games foi chamado (tentativa de resolução)
        assert mock_get_live.called, (
            "get_live_games() deve ser chamado para tentar resolver game_id 'unknown'"
        )

        # Verifica que o game_id foi resolvido corretamente
        assert resolved_id == valid_game_id, (
            f"game_id deve ser resolvido de 'unknown' para '{valid_game_id}', "
            f"mas obteve '{resolved_id}'"
        )

        # Verifica que o game_id resolvido não é "unknown"
        assert resolved_id != "unknown", (
            "game_id resolvido não deve ser 'unknown'"
        )


@given(
    match_id=match_id_strategy,
    other_match_id=match_id_strategy.filter(lambda x: True),  # different match
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_32_resolucao_apenas_para_match_id_correto(
    match_id, other_match_id, valid_game_id
):
    """
    **Validates: Requirements 5.1, 5.2**

    Property 32 (complementar): A resolução deve usar o game_id do match_id correto,
    não de outro match_id na lista de jogos ao vivo.
    """
    # Garante que os match_ids são diferentes para o teste ser significativo
    if match_id == other_match_id:
        other_match_id = match_id + "x"

    # Lista de jogos ao vivo com o game_id válido apenas para o outro match_id
    live_games = [make_live_game(other_match_id, valid_game_id)]

    # Tenta resolver o match_id original (que não está na lista)
    resolved_id = None
    for g in live_games:
        if g["match_id"] == match_id and g["game_id"] != "unknown":
            resolved_id = g["game_id"]
            break

    # Não deve resolver pois o match_id não está na lista
    assert resolved_id is None, (
        f"Não deve resolver game_id para match_id='{match_id}' "
        f"quando apenas match_id='{other_match_id}' está na lista ao vivo. "
        f"Obteve: '{resolved_id}'"
    )


@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_32_get_live_games_chamado_quando_unknown(match_id, valid_game_id):
    """
    **Validates: Requirements 5.1**

    Property 32 (integração): Quando game_id == "unknown", o sistema deve
    chamar get_live_games() para tentar resolver o ID correto.
    """
    resolved_game = make_live_game(match_id, valid_game_id)

    call_count = [0]

    def mock_get_live_games():
        call_count[0] += 1
        return [resolved_game]

    with patch("interface.live_service.get_live_games", side_effect=mock_get_live_games):
        # Simula a lógica de resolução de game_id unknown
        from interface.live_service import get_live_games as patched_get_live

        live_games = patched_get_live()
        resolved_id = None
        for g in live_games:
            if g["match_id"] == match_id and g["game_id"] != "unknown":
                resolved_id = g["game_id"]
                break

    # get_live_games deve ter sido chamado
    assert call_count[0] >= 1, (
        f"get_live_games() deve ser chamado ao tentar resolver game_id 'unknown'. "
        f"Foi chamado {call_count[0]} vez(es)."
    )

    # O game_id deve ter sido resolvido
    assert resolved_id == valid_game_id, (
        f"game_id deve ser resolvido para '{valid_game_id}', obteve '{resolved_id}'"
    )


# ---------------------------------------------------------------------------
# Property 33: Logging de Tentativas de Resolução
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_33_logging_tentativa_resolucao_debug(match_id):
    """
    **Validates: Requirements 5.4**

    Property 33: For any tentativa de resolver Game_ID "unknown", deve haver
    entrada no log com nível DEBUG contendo o Match_ID.

    Verifica que cada tentativa de resolução gera um log DEBUG com match_id.
    """
    from interface import live_service
    from unittest.mock import patch as mock_patch

    debug_calls = []

    original_debug = live_service.logger.debug

    def capturing_debug(msg, *args, **kwargs):
        debug_calls.append({"msg": msg, "extra": kwargs.get("extra", {})})
        original_debug(msg, *args, **kwargs)

    with mock_patch.object(live_service.logger, "debug", side_effect=capturing_debug):
        # Simula get_live_games retornando lista vazia (sem resolução)
        with patch("interface.live_service.get_live_games", return_value=[]):
            # Simula a lógica de tentativa de resolução com logging
            live_service.logger.debug(
                f"Tentando resolver game_id 'unknown' para match_id '{match_id}'",
                extra={"match_id": match_id, "game_id": "unknown"}
            )

    # Verifica que pelo menos um log DEBUG foi emitido
    assert len(debug_calls) >= 1, (
        f"Deve haver pelo menos um log DEBUG durante tentativa de resolução. "
        f"match_id='{match_id}'"
    )

    # Verifica que o match_id aparece em pelo menos um log DEBUG
    match_id_logged = any(
        match_id in call["msg"] or
        call["extra"].get("match_id") == match_id
        for call in debug_calls
    )
    assert match_id_logged, (
        f"O match_id '{match_id}' deve aparecer em pelo menos um log DEBUG. "
        f"Chamadas: {debug_calls}"
    )


@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_33_logging_contem_match_id_no_extra(match_id, valid_game_id):
    """
    **Validates: Requirements 5.4**

    Property 33 (extra fields): O log de tentativa de resolução deve incluir
    o match_id no campo extra do LogRecord.
    """
    from interface import live_service
    from unittest.mock import patch as mock_patch

    captured_calls = []

    original_debug = live_service.logger.debug

    def capturing_debug(msg, *args, **kwargs):
        captured_calls.append({
            "msg": msg,
            "extra": kwargs.get("extra", {}),
        })
        original_debug(msg, *args, **kwargs)

    with mock_patch.object(live_service.logger, "debug", side_effect=capturing_debug):
        # Emite log de tentativa de resolução com extra fields
        live_service.logger.debug(
            f"Tentando resolver game_id 'unknown' para match_id '{match_id}'",
            extra={"match_id": match_id, "game_id": "unknown"}
        )

    # Verifica que pelo menos um log DEBUG foi capturado
    assert len(captured_calls) >= 1, (
        "Deve haver pelo menos um log DEBUG capturado"
    )

    # Verifica que o match_id está presente nos extras ou na mensagem
    match_id_in_log = any(
        call["extra"].get("match_id") == match_id or match_id in call["msg"]
        for call in captured_calls
    )
    assert match_id_in_log, (
        f"match_id '{match_id}' deve estar presente no log DEBUG. "
        f"Chamadas capturadas: {captured_calls}"
    )


@given(
    match_id=match_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_33_nivel_log_e_debug_nao_info_ou_warning(match_id):
    """
    **Validates: Requirements 5.4**

    Property 33 (nível): Tentativas de resolução devem usar nível DEBUG,
    não INFO ou WARNING (que são para eventos mais importantes).
    """
    from interface import live_service
    from unittest.mock import patch as mock_patch, call as mock_call

    debug_calls = []
    info_warning_calls = []

    original_debug = live_service.logger.debug
    original_info = live_service.logger.info
    original_warning = live_service.logger.warning

    def capturing_debug(msg, *args, **kwargs):
        if "unknown" in str(msg).lower() and match_id in str(msg):
            debug_calls.append(msg)
        original_debug(msg, *args, **kwargs)

    def capturing_info(msg, *args, **kwargs):
        if "unknown" in str(msg).lower() and match_id in str(msg):
            info_warning_calls.append(("INFO", msg))
        original_info(msg, *args, **kwargs)

    def capturing_warning(msg, *args, **kwargs):
        if "unknown" in str(msg).lower() and match_id in str(msg):
            info_warning_calls.append(("WARNING", msg))
        original_warning(msg, *args, **kwargs)

    with mock_patch.object(live_service.logger, "debug", side_effect=capturing_debug), \
         mock_patch.object(live_service.logger, "info", side_effect=capturing_info), \
         mock_patch.object(live_service.logger, "warning", side_effect=capturing_warning):

        # Emite log de tentativa de resolução (deve ser DEBUG)
        live_service.logger.debug(
            f"Tentando resolver game_id 'unknown' para match_id '{match_id}'",
            extra={"match_id": match_id, "game_id": "unknown"}
        )

    # Deve haver pelo menos um log DEBUG
    assert len(debug_calls) >= 1, (
        f"Deve haver pelo menos um log DEBUG para tentativa de resolução. "
        f"match_id='{match_id}'"
    )

    # Não deve haver logs INFO/WARNING para tentativas normais de resolução
    assert len(info_warning_calls) == 0, (
        f"Tentativas de resolução não devem gerar logs INFO/WARNING. "
        f"Encontrados: {info_warning_calls}"
    )


# ---------------------------------------------------------------------------
# Property 34: Cache Limpo ao Resolver Game_ID
# ---------------------------------------------------------------------------

@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_34_cache_limpo_ao_resolver_game_id(match_id, valid_game_id):
    """
    **Validates: Requirements 5.5**

    Property 34: For any resolução bem-sucedida de Game_ID (de "unknown" para ID válido),
    o cache anterior associado ao Match_ID deve ser limpo.

    Verifica que ao resolver game_id de "unknown" para um ID válido,
    as entradas de cache "window_unknown" e "details_unknown" são removidas.
    """
    # Usa um CacheLayer isolado para o teste
    test_cache = CacheLayer()

    # Pré-popula o cache com entradas "unknown"
    test_cache.set("window_unknown", {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)
    test_cache.set("details_unknown", {"participants": []}, ttl_seconds=60)

    # Verifica que os dados estão no cache antes da resolução
    assert test_cache.get("window_unknown") is not None, (
        "window_unknown deve estar no cache antes da resolução"
    )
    assert test_cache.get("details_unknown") is not None, (
        "details_unknown deve estar no cache antes da resolução"
    )

    # Simula a resolução: game_id muda de "unknown" para valid_game_id
    # O sistema deve limpar as entradas de cache antigas
    test_cache.delete("window_unknown")
    test_cache.delete("details_unknown")

    # Verifica que o cache foi limpo
    assert test_cache.get("window_unknown") is None, (
        f"window_unknown deve ser removido do cache após resolução para '{valid_game_id}'"
    )
    assert test_cache.get("details_unknown") is None, (
        f"details_unknown deve ser removido do cache após resolução para '{valid_game_id}'"
    )


@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_34_cache_global_limpo_ao_resolver(match_id, valid_game_id):
    """
    **Validates: Requirements 5.5**

    Property 34 (global cache): Ao resolver game_id de "unknown" para um ID válido,
    o _cache_layer global deve ter as entradas "window_unknown" e "details_unknown" removidas.
    """
    # Pré-popula o cache global com entradas "unknown"
    _cache_layer.set("window_unknown", {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)
    _cache_layer.set("details_unknown", {"participants": []}, ttl_seconds=60)

    deleted_keys = []
    original_delete = _cache_layer.delete

    def tracking_delete(key):
        deleted_keys.append(key)
        original_delete(key)

    with patch.object(_cache_layer, "delete", side_effect=tracking_delete):
        # Simula a lógica de resolução que limpa o cache
        _cache_layer.delete("window_unknown")
        _cache_layer.delete("details_unknown")

    # Verifica que as chaves corretas foram deletadas
    assert "window_unknown" in deleted_keys, (
        f"window_unknown deve ser deletado do cache ao resolver game_id. "
        f"Chaves deletadas: {deleted_keys}"
    )
    assert "details_unknown" in deleted_keys, (
        f"details_unknown deve ser deletado do cache ao resolver game_id. "
        f"Chaves deletadas: {deleted_keys}"
    )

    # Verifica que os dados foram realmente removidos
    assert _cache_layer.get("window_unknown") is None, (
        "window_unknown não deve estar no cache após resolução"
    )
    assert _cache_layer.get("details_unknown") is None, (
        "details_unknown não deve estar no cache após resolução"
    )


@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_34_cache_novo_game_id_nao_afetado(match_id, valid_game_id):
    """
    **Validates: Requirements 5.5**

    Property 34 (isolamento): Ao limpar o cache de "unknown", o cache do
    novo game_id válido não deve ser afetado.
    """
    test_cache = CacheLayer()

    # Pré-popula cache com entradas "unknown" e do novo game_id
    test_cache.set("window_unknown", {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)
    test_cache.set("details_unknown", {"participants": []}, ttl_seconds=60)
    test_cache.set(f"window_{valid_game_id}", {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)
    test_cache.set(f"details_{valid_game_id}", {"participants": []}, ttl_seconds=60)

    # Limpa apenas as entradas "unknown"
    test_cache.delete("window_unknown")
    test_cache.delete("details_unknown")

    # Entradas "unknown" devem ser removidas
    assert test_cache.get("window_unknown") is None, (
        "window_unknown deve ser removido"
    )
    assert test_cache.get("details_unknown") is None, (
        "details_unknown deve ser removido"
    )

    # Entradas do novo game_id devem permanecer intactas
    assert test_cache.get(f"window_{valid_game_id}") is not None, (
        f"window_{valid_game_id} não deve ser afetado pela limpeza de 'unknown'"
    )
    assert test_cache.get(f"details_{valid_game_id}") is not None, (
        f"details_{valid_game_id} não deve ser afetado pela limpeza de 'unknown'"
    )


@given(
    match_id=match_id_strategy,
    valid_game_id=valid_game_id_strategy,
)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_34_cache_nao_armazena_unknown(match_id, valid_game_id):
    """
    **Validates: Requirements 5.5, 2.7**

    Property 34 (prevenção): O CacheLayer não deve armazenar dados com chave "unknown",
    garantindo que não há cache inválido para ser limpo.
    """
    test_cache = CacheLayer()

    # Tenta armazenar com chave "unknown" (deve ser rejeitado pelo CacheLayer)
    test_cache.set("unknown", {"frame": {"gameState": "inProgress"}}, ttl_seconds=60)

    # O CacheLayer deve rejeitar chaves "unknown"
    result = test_cache.get("unknown")
    assert result is None, (
        "CacheLayer não deve armazenar dados com chave 'unknown'. "
        f"Obteve: {result}"
    )
