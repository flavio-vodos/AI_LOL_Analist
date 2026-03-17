"""
Testes de integração para live_service.py.

Valida o comportamento de cache e retry nas funções get_game_window e get_game_details.

**Validates: Requirements 2.3, 2.4**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GAME_ID = "game_123"
WINDOW_CACHE_KEY = f"window_{GAME_ID}"
DETAILS_CACHE_KEY = f"details_{GAME_ID}"

FAKE_WINDOW_DATA = {
    "frame": {
        "blueTeam": {"participants": [], "totalGold": 1000},
        "redTeam": {"participants": [], "totalGold": 900},
        "gameState": "inProgress",
        "rfc460Timestamp": "2024-01-01T00:00:00.000Z",
    },
    "metadata": {},
}

FAKE_DETAILS_DATA = {
    "blueTeam": {"participants": []},
    "redTeam": {"participants": []},
}


# ---------------------------------------------------------------------------
# Tests for get_game_window
# ---------------------------------------------------------------------------

class TestGetGameWindowCacheHit(unittest.TestCase):
    """Req 2.3: quando há cache válido, retorna dados em cache sem chamar a API."""

    def test_cache_hit_returns_cached_data_without_api_call(self):
        """Cache hit: mock retorna dados, API NÃO deve ser chamada."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = FAKE_WINDOW_DATA

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            # Deve retornar os dados do cache
            self.assertEqual(result, FAKE_WINDOW_DATA)

            # Cache deve ter sido consultado com a chave correta
            mock_cache.get.assert_called_once_with(WINDOW_CACHE_KEY)

            # API NÃO deve ter sido chamada
            mock_retry.fetch_with_retry.assert_not_called()

    def test_cache_hit_does_not_store_again(self):
        """Cache hit: não deve chamar cache.set novamente."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system"):

            mock_cache.get.return_value = FAKE_WINDOW_DATA

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            mock_cache.set.assert_not_called()


class TestGetGameWindowCacheMiss(unittest.TestCase):
    """Req 2.4: quando cache está vazio/expirado, busca da API e armazena no cache."""

    def _make_api_response(self):
        return {
            "frames": [FAKE_WINDOW_DATA["frame"]],
            "gameMetadata": FAKE_WINDOW_DATA["metadata"],
        }

    def test_cache_miss_calls_api(self):
        """Cache miss: API deve ser chamada."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = self._make_api_response()

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            mock_retry.fetch_with_retry.assert_called_once()

    def test_cache_miss_stores_result_in_cache(self):
        """Cache miss: resultado da API deve ser armazenado no cache."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = self._make_api_response()

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            # Deve ter chamado cache.set com a chave e TTL corretos
            mock_cache.set.assert_called_once_with(WINDOW_CACHE_KEY, result, ttl_seconds=5)

    def test_cache_miss_returns_api_data(self):
        """Cache miss: retorna dados processados da API."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = self._make_api_response()

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertIsNotNone(result)
            self.assertIn("frame", result)
            self.assertIn("metadata", result)

    def test_cache_miss_api_failure_returns_none(self):
        """Cache miss com falha na API: retorna None."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertIsNone(result)
            mock_cache.set.assert_not_called()

    def test_unknown_game_id_not_cached(self):
        """game_id 'unknown' não deve ser armazenado no cache."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = self._make_api_response()

            from interface.live_service import get_game_window
            get_game_window("unknown")

            mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for get_game_details
# ---------------------------------------------------------------------------

class TestGetGameDetailsCacheHit(unittest.TestCase):
    """Req 2.3: cache hit em get_game_details não chama a API."""

    def test_cache_hit_returns_cached_data_without_api_call(self):
        """Cache hit: retorna dados em cache, API NÃO é chamada."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = FAKE_DETAILS_DATA

            from interface.live_service import get_game_details
            result = get_game_details(GAME_ID)

            self.assertEqual(result, FAKE_DETAILS_DATA)
            mock_cache.get.assert_called_once_with(DETAILS_CACHE_KEY)
            mock_retry.fetch_with_retry.assert_not_called()


class TestGetGameDetailsCacheMiss(unittest.TestCase):
    """Req 2.4: cache miss em get_game_details busca da API e armazena."""

    def _make_api_response(self):
        return {"frames": [FAKE_DETAILS_DATA]}

    def test_cache_miss_calls_api_and_stores_result(self):
        """Cache miss: API é chamada e resultado é armazenado."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = self._make_api_response()

            from interface.live_service import get_game_details
            result = get_game_details(GAME_ID)

            mock_retry.fetch_with_retry.assert_called_once()
            mock_cache.set.assert_called_once_with(DETAILS_CACHE_KEY, result, ttl_seconds=5)

    def test_cache_miss_api_failure_returns_none(self):
        """Cache miss com falha na API: retorna None e não armazena."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_details
            result = get_game_details(GAME_ID)

            self.assertIsNone(result)
            mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for retry behavior
# ---------------------------------------------------------------------------

class TestRetryBehavior(unittest.TestCase):
    """Verifica que o RetrySystem é usado corretamente em caso de falha."""

    def test_retry_system_called_with_correct_url(self):
        """fetch_with_retry é chamado com a URL correta do endpoint window."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            args, kwargs = mock_retry.fetch_with_retry.call_args
            url = kwargs.get("url") or args[0]
            self.assertIn(GAME_ID, url)
            self.assertIn("window", url)

    def test_retry_system_uses_retry_without_param(self):
        """fetch_with_retry é chamado com retry_without_param='startingTime'."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            _, kwargs = mock_retry.fetch_with_retry.call_args
            self.assertEqual(kwargs.get("retry_without_param"), "startingTime")

    def test_retry_system_called_for_details(self):
        """fetch_with_retry é chamado com a URL correta do endpoint details."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_details
            get_game_details(GAME_ID)

            args, kwargs = mock_retry.fetch_with_retry.call_args
            url = kwargs.get("url") or args[0]
            self.assertIn(GAME_ID, url)
            self.assertIn("details", url)


# ---------------------------------------------------------------------------
# Tests for logging
# ---------------------------------------------------------------------------

class TestLogging(unittest.TestCase):
    """Verifica que operações de cache hit/miss são registradas no log."""

    def test_cache_hit_is_logged(self):
        """Cache hit deve gerar log de debug."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system"), \
             patch("interface.live_service.logger") as mock_logger:

            mock_cache.get.return_value = FAKE_WINDOW_DATA

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            # Deve ter chamado logger.debug pelo menos uma vez
            mock_logger.debug.assert_called()
            # Verifica que alguma mensagem menciona "hit" ou o game_id
            debug_calls = [str(c) for c in mock_logger.debug.call_args_list]
            self.assertTrue(
                any("hit" in msg.lower() or GAME_ID in msg for msg in debug_calls),
                f"Expected cache hit log, got: {debug_calls}"
            )

    def test_cache_miss_is_logged(self):
        """Cache miss deve gerar log de debug."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry, \
             patch("interface.live_service.logger") as mock_logger:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_window
            get_game_window(GAME_ID)

            mock_logger.debug.assert_called()
            debug_calls = [str(c) for c in mock_logger.debug.call_args_list]
            self.assertTrue(
                any("miss" in msg.lower() or GAME_ID in msg for msg in debug_calls),
                f"Expected cache miss log, got: {debug_calls}"
            )


if __name__ == "__main__":
    unittest.main()
