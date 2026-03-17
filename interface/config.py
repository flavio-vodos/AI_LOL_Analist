"""
config.py
Configuração centralizada do sistema de extração de dados em tempo real.

Todas as configurações são lidas de environment variables com fallbacks padrão.

Variáveis de ambiente suportadas:
    CACHE_TTL_GAME_WINDOW       TTL do cache para game window (segundos). Padrão: 5
    CACHE_TTL_GAME_DETAILS      TTL do cache para game details (segundos). Padrão: 5
    CACHE_TTL_LIVE_GAMES        TTL do cache para lista de jogos ao vivo (segundos). Padrão: 10
    CACHE_TTL_SCHEDULE          TTL do cache para schedule do dia (segundos). Padrão: 60

    RETRY_MAX_ATTEMPTS          Número máximo de tentativas de retry. Padrão: 3
    RETRY_BASE_DELAY            Delay base para backoff exponencial (segundos). Padrão: 2.0
    RETRY_MAX_DELAY             Delay máximo entre tentativas (segundos). Padrão: 60.0
    RETRY_BACKOFF_FACTOR        Fator multiplicador do backoff exponencial. Padrão: 2.0

    POLLING_INTERVAL_SECONDS    Intervalo entre iterações de polling (segundos). Padrão: 10

    HEALTH_CHECK_INTERVAL       Intervalo entre health checks (segundos). Padrão: 60
    HEALTH_FAILURE_THRESHOLD    Número de falhas consecutivas para marcar unhealthy. Padrão: 3
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """
    Configuração centralizada do sistema.

    Todos os valores podem ser sobrescritos via environment variables.
    Use Config.from_env() para criar uma instância lendo do ambiente.
    Use validate() para garantir que os valores são válidos antes de usar.
    """

    # ── Cache TTLs (segundos) ─────────────────────────────────────────────────
    # TTL para dados de game window (stats de time e jogadores por frame)
    cache_ttl_game_window: int = 5
    # TTL para dados de game details (itens dos jogadores por frame)
    cache_ttl_game_details: int = 5
    # TTL para lista de jogos ao vivo (getLive endpoint)
    cache_ttl_live_games: int = 10
    # TTL para schedule do dia (getSchedule endpoint)
    cache_ttl_schedule: int = 60

    # ── Retry settings ────────────────────────────────────────────────────────
    # Número máximo de tentativas antes de desistir
    retry_max_attempts: int = 3
    # Delay base para cálculo de backoff exponencial (segundos)
    retry_base_delay: float = 2.0
    # Delay máximo entre tentativas (segundos)
    retry_max_delay: float = 60.0
    # Fator multiplicador do backoff: delay = base_delay * (backoff_factor ^ attempt)
    retry_backoff_factor: float = 2.0

    # ── Polling settings ──────────────────────────────────────────────────────
    # Intervalo entre iterações de polling (segundos)
    polling_interval_seconds: int = 10

    # ── Health monitor settings ───────────────────────────────────────────────
    # Intervalo entre health checks (segundos)
    health_check_interval: int = 60
    # Número de falhas consecutivas para marcar a API como unhealthy
    health_failure_threshold: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        """
        Cria Config lendo de environment variables.

        Cada campo tem um fallback para o valor padrão caso a variável
        de ambiente não esteja definida.

        Returns:
            Config com valores lidos do ambiente
        """
        return cls(
            cache_ttl_game_window=int(os.getenv("CACHE_TTL_GAME_WINDOW", "5")),
            cache_ttl_game_details=int(os.getenv("CACHE_TTL_GAME_DETAILS", "5")),
            cache_ttl_live_games=int(os.getenv("CACHE_TTL_LIVE_GAMES", "10")),
            cache_ttl_schedule=int(os.getenv("CACHE_TTL_SCHEDULE", "60")),
            retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            retry_base_delay=float(os.getenv("RETRY_BASE_DELAY", "2.0")),
            retry_max_delay=float(os.getenv("RETRY_MAX_DELAY", "60.0")),
            retry_backoff_factor=float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0")),
            polling_interval_seconds=int(os.getenv("POLLING_INTERVAL_SECONDS", "10")),
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            health_failure_threshold=int(os.getenv("HEALTH_FAILURE_THRESHOLD", "3")),
        )

    def validate(self) -> None:
        """
        Valida que os valores de configuração são válidos.

        Raises:
            AssertionError: Se algum valor for inválido
        """
        assert self.cache_ttl_game_window > 0, "cache_ttl_game_window must be > 0"
        assert self.cache_ttl_game_details > 0, "cache_ttl_game_details must be > 0"
        assert self.cache_ttl_live_games > 0, "cache_ttl_live_games must be > 0"
        assert self.cache_ttl_schedule > 0, "cache_ttl_schedule must be > 0"
        assert self.retry_max_attempts > 0, "retry_max_attempts must be > 0"
        assert self.retry_base_delay > 0, "retry_base_delay must be > 0"
        assert self.retry_max_delay > 0, "retry_max_delay must be > 0"
        assert self.retry_backoff_factor > 1, "retry_backoff_factor must be > 1"
        assert self.polling_interval_seconds > 0, "polling_interval_seconds must be > 0"
        assert self.health_check_interval > 0, "health_check_interval must be > 0"
        assert self.health_failure_threshold > 0, "health_failure_threshold must be > 0"
