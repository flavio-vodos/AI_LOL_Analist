"""
Testes de integração end-to-end para o sistema de extração de dados em tempo real.

Cobre:
1. Fluxo completo de requisição (frontend → API → live_service → cache/retry → LoL Esports API)
2. Cenários de erro e recuperação (400, retries, fallback)
3. Polling com gerenciamento de estado de partidas

**Validates: Requirements 1.1, 1.2, 1.3, 2.3, 2.4, 3.1, 3.2, 7.6, 9.1, 9.2, 9.3**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import threading
import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Fixtures compartilhadas
# ---------------------------------------------------------------------------

GAME_ID = "game_e2e_001"
MATCH_ID = "match_e2e_001"

FAKE_FRAME = {
    "blueTeam": {
        "participants": [{"level": 10, "currentHealth": 1000, "maxHealth": 2000,
                          "creepScore": 120, "kills": 3, "deaths": 1, "assists": 2,
                          "totalGold": 8000}] * 5,
        "totalGold": 40000,
        "totalKills": 5,
        "towers": 2,
        "barons": 0,
        "inhibitors": 0,
        "dragons": ["infernal"],
    },
    "redTeam": {
        "participants": [{"level": 9, "currentHealth": 800, "maxHealth": 1800,
                          "creepScore": 100, "kills": 2, "deaths": 2, "assists": 1,
                          "totalGold": 7000}] * 5,
        "totalGold": 35000,
        "totalKills": 3,
        "towers": 1,
        "barons": 0,
        "inhibitors": 0,
        "dragons": [],
    },
    "gameState": "inProgress",
    "rfc460Timestamp": "2024-01-01T00:10:00.000Z",
}

FAKE_METADATA = {
    "blueTeamMetadata": {
        "participantMetadata": [
            {"championId": "Caitlyn", "summonerName": "Player1", "esportsPlayerId": "p1"}
        ] * 5
    },
    "redTeamMetadata": {
        "participantMetadata": [
            {"championId": "Jinx", "summonerName": "Player6", "esportsPlayerId": "p6"}
        ] * 5
    },
}

FAKE_WINDOW_API_RESPONSE = {
    "frames": [FAKE_FRAME],
    "gameMetadata": FAKE_METADATA,
}

FAKE_DETAILS_FRAME = {
    "blueTeam": {
        "participants": [
            {"item0": 3031, "item1": 3006, "item2": 0, "item3": 0,
             "item4": 0, "item5": 0, "item6": 3364}
        ] * 5
    },
    "redTeam": {
        "participants": [
            {"item0": 3153, "item1": 3006, "item2": 0, "item3": 0,
             "item4": 0, "item5": 0, "item6": 3364}
        ] * 5
    },
}

FAKE_DETAILS_API_RESPONSE = {
    "frames": [FAKE_DETAILS_FRAME],
}

FAKE_GAME_INFO = {
    "match_id": MATCH_ID,
    "game_id": GAME_ID,
    "game_number": 1,
    "league": "LCK",
    "team_blue": {"code": "T1", "name": "T1", "image": ""},
    "team_red": {"code": "GEN", "name": "Gen.G", "image": ""},
}


# ---------------------------------------------------------------------------
# 1. Fluxo completo de requisição
# ---------------------------------------------------------------------------

class TestFullRequestFlow(unittest.TestCase):
    """Testa o fluxo completo: cache miss → retry → API → cache set → retorno."""

    def test_full_flow_cache_miss_then_api_success(self):
        """Cache miss → API retorna dados → resultado processado e cacheado."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = FAKE_WINDOW_API_RESPONSE

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            # Resultado deve conter frame e metadata
            self.assertIsNotNone(result)
            self.assertIn("frame", result)
            self.assertIn("metadata", result)
            self.assertEqual(result["frame"]["gameState"], "inProgress")

            # Cache deve ter sido populado
            mock_cache.set.assert_called_once_with(
                f"window_{GAME_ID}", result, ttl_seconds=5
            )

    def test_full_flow_cache_hit_skips_api(self):
        """Cache hit → API não é chamada → dados retornados diretamente."""
        cached_data = {"frame": FAKE_FRAME, "metadata": FAKE_METADATA}

        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = cached_data

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertEqual(result, cached_data)
            mock_retry.fetch_with_retry.assert_not_called()
            mock_cache.set.assert_not_called()

    def test_full_flow_window_then_details(self):
        """Fluxo completo: window → extrai timestamp → details com timestamp."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.side_effect = [
                FAKE_WINDOW_API_RESPONSE,
                FAKE_DETAILS_API_RESPONSE,
            ]

            from interface.live_service import get_game_window, get_game_details
            window = get_game_window(GAME_ID)
            ts = window["frame"].get("rfc460Timestamp")
            details = get_game_details(GAME_ID, timestamp=ts)

            self.assertIsNotNone(window)
            self.assertIsNotNone(details)
            self.assertEqual(mock_retry.fetch_with_retry.call_count, 2)

            # Segunda chamada deve incluir o timestamp do frame
            _, kwargs = mock_retry.fetch_with_retry.call_args_list[1]
            params = kwargs.get("params") or {}
            self.assertEqual(params.get("startingTime"), ts)

    def test_render_live_match_returns_html(self):
        """render_live_match retorna HTML quando dados estão disponíveis."""
        window_data = {"frame": FAKE_FRAME, "metadata": FAKE_METADATA}
        details_data = FAKE_DETAILS_FRAME

        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.side_effect = [window_data, details_data]

            from interface.live_service import render_live_match
            html = render_live_match(FAKE_GAME_INFO)

            self.assertIsInstance(html, str)
            self.assertIn("<", html)  # É HTML
            self.assertNotIn("Dados da partida ainda não disponíveis", html)

    def test_render_live_match_no_data_returns_error_html(self):
        """render_live_match retorna mensagem de erro quando sem dados."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import render_live_match
            html = render_live_match(FAKE_GAME_INFO)

            self.assertIn("Dados da partida ainda não disponíveis", html)


# ---------------------------------------------------------------------------
# 2. Cenários de erro e recuperação
# ---------------------------------------------------------------------------

class TestErrorAndRecovery(unittest.TestCase):
    """Testa cenários de erro 400, retries e fallback."""

    def test_400_error_triggers_retry_without_startingTime(self):
        """Erro 400 → RetrySystem remove startingTime e tenta novamente."""
        from interface.retry_system import RetrySystem, RetryConfig
        import requests

        config = RetryConfig(max_attempts=2, base_delay=0.01, backoff_factor=1.0)
        retry = RetrySystem(config=config)

        mock_resp_400 = MagicMock()
        mock_resp_400.status_code = 400
        mock_resp_400.text = "Bad Request"

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = FAKE_WINDOW_API_RESPONSE

        with patch("requests.get", side_effect=[mock_resp_400, mock_resp_200]) as mock_get:
            result = retry.fetch_with_retry(
                url="https://feed.lolesports.com/livestats/v1/window/game_123",
                params={"hl": "pt-BR", "startingTime": "2024-01-01T00:00:00Z"},
                headers={},
                retry_without_param="startingTime",
            )

        self.assertEqual(result, FAKE_WINDOW_API_RESPONSE)
        self.assertEqual(mock_get.call_count, 2)

        # Segunda chamada não deve ter startingTime
        _, second_kwargs = mock_get.call_args_list[1]
        second_params = second_kwargs.get("params", {})
        self.assertNotIn("startingTime", second_params)

    def test_all_retries_exhausted_returns_none(self):
        """Todas as tentativas falham → retorna None."""
        from interface.retry_system import RetrySystem, RetryConfig

        config = RetryConfig(max_attempts=3, base_delay=0.01, backoff_factor=1.0)
        retry = RetrySystem(config=config)

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "Service Unavailable"

        with patch("requests.get", return_value=mock_resp):
            result = retry.fetch_with_retry(
                url="https://feed.lolesports.com/livestats/v1/window/game_123",
                params={"hl": "pt-BR"},
                headers={},
            )

        self.assertIsNone(result)

    def test_timeout_triggers_retry(self):
        """Timeout na requisição → sistema tenta novamente."""
        import requests as req_lib
        from interface.retry_system import RetrySystem, RetryConfig

        config = RetryConfig(max_attempts=2, base_delay=0.01, backoff_factor=1.0)
        retry = RetrySystem(config=config)

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = FAKE_WINDOW_API_RESPONSE

        with patch("requests.get", side_effect=[req_lib.exceptions.Timeout(), mock_resp_200]) as mock_get:
            result = retry.fetch_with_retry(
                url="https://feed.lolesports.com/livestats/v1/window/game_123",
                params={"hl": "pt-BR"},
                headers={},
            )

        self.assertEqual(result, FAKE_WINDOW_API_RESPONSE)
        self.assertEqual(mock_get.call_count, 2)

    def test_connection_error_triggers_retry(self):
        """Erro de conexão → sistema tenta novamente."""
        import requests as req_lib
        from interface.retry_system import RetrySystem, RetryConfig

        config = RetryConfig(max_attempts=2, base_delay=0.01, backoff_factor=1.0)
        retry = RetrySystem(config=config)

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = FAKE_WINDOW_API_RESPONSE

        with patch("requests.get", side_effect=[req_lib.exceptions.ConnectionError("refused"), mock_resp_200]):
            result = retry.fetch_with_retry(
                url="https://feed.lolesports.com/livestats/v1/window/game_123",
                params={"hl": "pt-BR"},
                headers={},
            )

        self.assertEqual(result, FAKE_WINDOW_API_RESPONSE)

    def test_get_game_window_api_failure_returns_none(self):
        """Falha total na API → get_game_window retorna None."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertIsNone(result)
            mock_cache.set.assert_not_called()

    def test_get_game_details_api_failure_returns_none(self):
        """Falha total na API → get_game_details retorna None."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = None

            from interface.live_service import get_game_details
            result = get_game_details(GAME_ID)

            self.assertIsNone(result)
            mock_cache.set.assert_not_called()

    def test_unknown_game_id_not_cached_on_success(self):
        """game_id 'unknown' → dados não são armazenados no cache mesmo com sucesso."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = FAKE_WINDOW_API_RESPONSE

            from interface.live_service import get_game_window
            get_game_window("unknown")

            mock_cache.set.assert_not_called()

    def test_empty_frames_returns_none(self):
        """API retorna resposta sem frames → retorna None."""
        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = None
            mock_retry.fetch_with_retry.return_value = {"frames": [], "gameMetadata": {}}

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertIsNone(result)
            mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Polling com gerenciamento de estado de partidas
# ---------------------------------------------------------------------------

class TestPollingMatchState(unittest.TestCase):
    """Testa detecção de estado de partida e comportamento do polling."""

    def _make_live_games_response(self, game_state="inProgress", all_completed=False):
        """Cria resposta simulada de get_live_games."""
        games = [{"id": GAME_ID, "state": game_state, "number": 1}]
        if all_completed:
            games = [{"id": GAME_ID, "state": "completed", "number": 1}]
        return {
            "data": {
                "schedule": {
                    "events": [{
                        "state": "inProgress",
                        "match": {
                            "id": MATCH_ID,
                            "state": "inProgress",
                            "strategy": {"count": 3},
                            "teams": [
                                {"code": "T1", "result": {"gameWins": 0}},
                                {"code": "GEN", "result": {"gameWins": 0}},
                            ],
                            "games": games,
                        },
                        "league": {"name": "LCK"},
                    }]
                }
            }
        }

    def test_game_state_finished_detected(self):
        """Frame com gameState 'finished' é detectado corretamente."""
        finished_frame = dict(FAKE_FRAME)
        finished_frame["gameState"] = "finished"

        window_data = {"frame": finished_frame, "metadata": FAKE_METADATA}

        with patch("interface.live_service._cache_layer") as mock_cache, \
             patch("interface.live_service._retry_system") as mock_retry:

            mock_cache.get.return_value = window_data

            from interface.live_service import get_game_window
            result = get_game_window(GAME_ID)

            self.assertIsNotNone(result)
            self.assertEqual(result["frame"]["gameState"], "finished")

    def test_all_games_completed_series_finished(self):
        """Todos os games 'completed' → série marcada como finalizada em get_live_games."""
        completed_event = {
            "state": "inProgress",
            "match": {
                "id": MATCH_ID,
                "state": "completed",
                "strategy": {"count": 3},
                "teams": [
                    {"code": "T1", "result": {"gameWins": 2}},
                    {"code": "GEN", "result": {"gameWins": 0}},
                ],
                "games": [
                    {"id": "g1", "state": "completed", "number": 1},
                    {"id": "g2", "state": "completed", "number": 2},
                ],
            },
            "league": {"name": "LCK"},
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"schedule": {"events": [completed_event]}}
        }

        with patch("requests.get", return_value=mock_response):
            from interface.live_service import get_live_games
            result = get_live_games()

        # Partida com match.state == "completed" deve ser filtrada
        match_ids = [g["match_id"] for g in result]
        self.assertNotIn(MATCH_ID, match_ids)

    def test_team_wins_threshold_bo3_filters_match(self):
        """Time com 2 vitórias em BO3 → partida filtrada de get_live_games."""
        event_with_winner = {
            "state": "inProgress",
            "match": {
                "id": MATCH_ID,
                "state": "inProgress",
                "strategy": {"count": 3},
                "teams": [
                    {"code": "T1", "result": {"gameWins": 2}},
                    {"code": "GEN", "result": {"gameWins": 0}},
                ],
                "games": [
                    {"id": "g1", "state": "completed", "number": 1},
                    {"id": "g2", "state": "completed", "number": 2},
                    {"id": "g3", "state": "unstarted", "number": 3},
                ],
            },
            "league": {"name": "LCK"},
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"schedule": {"events": [event_with_winner]}}
        }

        with patch("requests.get", return_value=mock_response):
            from interface.live_service import get_live_games
            result = get_live_games()

        match_ids = [g["match_id"] for g in result]
        self.assertNotIn(MATCH_ID, match_ids)

    def test_inprogress_match_included_in_live_games(self):
        """Partida em andamento → incluída em get_live_games."""
        event_live = {
            "state": "inProgress",
            "match": {
                "id": MATCH_ID,
                "state": "inProgress",
                "strategy": {"count": 3},
                "teams": [
                    {"code": "T1", "name": "T1", "result": {"gameWins": 0}, "image": ""},
                    {"code": "GEN", "name": "Gen.G", "result": {"gameWins": 0}, "image": ""},
                ],
                "games": [
                    {"id": GAME_ID, "state": "inProgress", "number": 1},
                ],
            },
            "league": {"name": "LCK"},
        }

        mock_live_response = MagicMock()
        mock_live_response.status_code = 200
        mock_live_response.json.return_value = {
            "data": {"schedule": {"events": [event_live]}}
        }

        mock_schedule_response = MagicMock()
        mock_schedule_response.status_code = 200
        mock_schedule_response.json.return_value = {
            "data": {"schedule": {"events": []}}
        }

        with patch("requests.get", side_effect=[mock_schedule_response, mock_live_response]):
            from interface.live_service import get_live_games
            result = get_live_games()

        match_ids = [g["match_id"] for g in result]
        self.assertIn(MATCH_ID, match_ids)

        game = next(g for g in result if g["match_id"] == MATCH_ID)
        self.assertEqual(game["game_id"], GAME_ID)


# ---------------------------------------------------------------------------
# 4. Testes de integração da API FastAPI
# ---------------------------------------------------------------------------

class TestFastAPIEndpoints(unittest.TestCase):
    """Testa endpoints da API FastAPI com mocks."""

    def setUp(self):
        from fastapi.testclient import TestClient
        # Patch health_monitor.start para não iniciar thread real
        with patch("api.HealthMonitor") as mock_hm_class:
            mock_hm = MagicMock()
            mock_hm_class.return_value = mock_hm
            import api as api_module
            self.client = TestClient(api_module.app)
            self.mock_hm = mock_hm

    def test_health_endpoint_returns_expected_fields(self):
        """GET /api/health retorna is_healthy, last_check, consecutive_failures."""
        import api as api_module
        mock_status = MagicMock()
        mock_status.is_healthy = True
        mock_status.last_check = datetime(2024, 1, 1, 0, 0, 0)
        mock_status.consecutive_failures = 0
        mock_status.last_error = None
        mock_status.response_time_ms = 123.4

        api_module.health_monitor.get_status = MagicMock(return_value=mock_status)

        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("is_healthy", data)
        self.assertIn("last_check", data)
        self.assertIn("consecutive_failures", data)
        self.assertTrue(data["is_healthy"])
        self.assertEqual(data["consecutive_failures"], 0)

    def test_health_endpoint_unhealthy_includes_error(self):
        """GET /api/health com status unhealthy inclui last_error."""
        import api as api_module
        mock_status = MagicMock()
        mock_status.is_healthy = False
        mock_status.last_check = datetime(2024, 1, 1, 0, 0, 0)
        mock_status.consecutive_failures = 3
        mock_status.last_error = "Connection refused"
        mock_status.response_time_ms = None

        api_module.health_monitor.get_status = MagicMock(return_value=mock_status)

        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data["is_healthy"])
        self.assertEqual(data["consecutive_failures"], 3)
        self.assertEqual(data["last_error"], "Connection refused")

    def test_live_games_endpoint_returns_list(self):
        """GET /api/live/games retorna lista."""
        with patch("interface.live_service.get_live_games", return_value=[FAKE_GAME_INFO]):
            response = self.client.get("/api/live/games")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["match_id"], MATCH_ID)

    def test_live_games_endpoint_handles_exception(self):
        """GET /api/live/games retorna 500 em caso de exceção."""
        with patch("interface.live_service.get_live_games", side_effect=Exception("API down")):
            response = self.client.get("/api/live/games")

        self.assertEqual(response.status_code, 500)

    def test_today_games_endpoint_returns_list(self):
        """GET /api/live/today retorna lista de partidas do dia."""
        fake_schedule = [{"match_id": MATCH_ID, "state": "unstarted", "league": "LCK",
                          "team_blue": {}, "team_red": {}, "start_time": "2024-01-01T18:00:00Z",
                          "strategy": {"count": 3}}]
        with patch("interface.live_service.get_schedule_today", return_value=fake_schedule):
            response = self.client.get("/api/live/today")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


# ---------------------------------------------------------------------------
# 5. Testes de cache com TTL real
# ---------------------------------------------------------------------------

class TestCacheTTLIntegration(unittest.TestCase):
    """Testa comportamento de TTL do cache com tempo real."""

    def test_cache_expires_after_ttl(self):
        """Dados expiram após TTL e cache retorna None."""
        from interface.cache_layer import CacheLayer

        cache = CacheLayer()
        cache.set("test_key", {"data": "value"}, ttl_seconds=1)

        # Imediatamente disponível
        self.assertIsNotNone(cache.get("test_key"))

        # Após expirar
        time.sleep(1.1)
        self.assertIsNone(cache.get("test_key"))

    def test_cache_hit_within_ttl(self):
        """Dados dentro do TTL são retornados corretamente."""
        from interface.cache_layer import CacheLayer

        cache = CacheLayer()
        data = {"frame": FAKE_FRAME}
        cache.set("window_game_123", data, ttl_seconds=10)

        result = cache.get("window_game_123")
        self.assertEqual(result, data)

    def test_cache_unknown_key_not_stored(self):
        """Chave 'unknown' não é armazenada no cache."""
        from interface.cache_layer import CacheLayer

        cache = CacheLayer()
        cache.set("unknown", {"data": "value"}, ttl_seconds=10)

        result = cache.get("unknown")
        self.assertIsNone(result)

    def test_cache_thread_safety(self):
        """Cache é thread-safe com múltiplas escritas simultâneas."""
        from interface.cache_layer import CacheLayer

        cache = CacheLayer()
        errors = []

        def write_cache(i):
            try:
                cache.set(f"key_{i}", {"value": i}, ttl_seconds=5)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_cache, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        # Todas as chaves devem estar no cache
        for i in range(20):
            self.assertIsNotNone(cache.get(f"key_{i}"))

    def test_cache_cleanup_expired(self):
        """cleanup_expired remove entradas expiradas."""
        from interface.cache_layer import CacheLayer

        cache = CacheLayer()
        cache.set("expired_key", {"data": "old"}, ttl_seconds=1)
        cache.set("valid_key", {"data": "new"}, ttl_seconds=60)

        time.sleep(1.1)
        removed = cache.cleanup_expired()

        self.assertEqual(removed, 1)
        self.assertIsNone(cache.get("expired_key"))
        self.assertIsNotNone(cache.get("valid_key"))


# ---------------------------------------------------------------------------
# 6. Testes de health monitor
# ---------------------------------------------------------------------------

class TestHealthMonitorIntegration(unittest.TestCase):
    """Testa o HealthMonitor com mocks de requisições HTTP."""

    def test_healthy_on_200_response(self):
        """Resposta 200 → status healthy, falhas resetadas."""
        from interface.health_monitor import HealthMonitor

        monitor = HealthMonitor(
            check_url="https://esports-api.lolesports.com/persisted/gw/getLive",
            check_interval=60,
            failure_threshold=3,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.get", return_value=mock_resp):
            result = monitor._check_health()

        self.assertTrue(result)
        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 0)

    def test_unhealthy_after_threshold_failures(self):
        """3 falhas consecutivas → status unhealthy."""
        from interface.health_monitor import HealthMonitor

        monitor = HealthMonitor(
            check_url="https://esports-api.lolesports.com/persisted/gw/getLive",
            check_interval=60,
            failure_threshold=3,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("requests.get", return_value=mock_resp):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertFalse(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 3)

    def test_recovery_after_failure(self):
        """Após falhas, resposta 200 reseta para healthy."""
        from interface.health_monitor import HealthMonitor

        monitor = HealthMonitor(
            check_url="https://esports-api.lolesports.com/persisted/gw/getLive",
            check_interval=60,
            failure_threshold=3,
        )

        mock_fail = MagicMock()
        mock_fail.status_code = 503

        mock_ok = MagicMock()
        mock_ok.status_code = 200

        with patch("requests.get", side_effect=[mock_fail, mock_fail, mock_fail, mock_ok]):
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()
            monitor._check_health()

        status = monitor.get_status()
        self.assertTrue(status.is_healthy)
        self.assertEqual(status.consecutive_failures, 0)

    def test_check_uses_correct_url(self):
        """Health check usa a URL configurada."""
        from interface.health_monitor import HealthMonitor

        check_url = "https://esports-api.lolesports.com/persisted/gw/getLive"
        monitor = HealthMonitor(check_url=check_url, check_interval=60)

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.get", return_value=mock_resp) as mock_get:
            monitor._check_health()

        args, _ = mock_get.call_args
        self.assertEqual(args[0], check_url)


if __name__ == "__main__":
    unittest.main()
