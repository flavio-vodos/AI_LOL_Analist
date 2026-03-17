"""
health_monitor.py
Monitor de saúde da API do LoL Esports.

Verifica periodicamente a disponibilidade da API, rastreia falhas consecutivas
e expõe o status atual via get_status(). Usa threading para monitoramento
em background sem bloquear a aplicação principal.
"""

from typing import Optional
from dataclasses import dataclass
import asyncio
import httpx
from datetime import datetime
import logging


@dataclass
class HealthStatus:
    """Status de saúde da API."""
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None


class HealthMonitor:
    """Monitor de saúde da API externa."""

    def __init__(
        self,
        check_url: str,
        check_interval: int = 60,
        failure_threshold: int = 3,
        logger: logging.Logger = None,
        headers: dict = None
    ):
        """
        Inicializa o monitor de saúde.

        Args:
            check_url: URL para health check (endpoint getLive)
            check_interval: Intervalo entre checks em segundos (padrão: 60)
            failure_threshold: Número de falhas consecutivas para marcar unhealthy (padrão: 3)
            logger: Logger para registrar operações (cria novo se None)
            headers: Headers HTTP opcionais para a requisição de health check
        """
        self.check_url = check_url
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.headers = headers or {}
        self.logger = logger or logging.getLogger(__name__)

        self._status = HealthStatus(
            is_healthy=True,
            last_check=datetime.now(),
            consecutive_failures=0
        )
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._is_running = False

    def start(self) -> None:
        """Inicia monitoramento as síncronamente."""
        if self._task is not None and not self._task.done():
            self.logger.warning("Health monitor já está em execução")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(
            f"Health monitor iniciado (intervalo: {self.check_interval}s, "
            f"threshold: {self.failure_threshold} falhas)"
        )

    async def stop(self) -> None:
        """Para o monitoramento gracefully."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self.logger.info("Health monitor parado")
            self._task = None

    async def get_status(self) -> HealthStatus:
        """Retorna status atual de saúde."""
        async with self._lock:
            return HealthStatus(
                is_healthy=self._status.is_healthy,
                last_check=self._status.last_check,
                consecutive_failures=self._status.consecutive_failures,
                last_error=self._status.last_error,
                response_time_ms=self._status.response_time_ms
            )

    async def _check_health(self) -> bool:
        """Executa check de saúde fazendo requisição leve ao endpoint getLive."""
        import time
        start_time = time.time()
        error_msg: Optional[str] = None
        response_time_ms: Optional[float] = None

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
                response = await client.get(self.check_url)
                response_time_ms = (time.time() - start_time) * 1000

                if 200 <= response.status_code < 300:
                    async with self._lock:
                        was_unhealthy = not self._status.is_healthy
                        self._status = HealthStatus(
                            is_healthy=True,
                            last_check=datetime.now(),
                            consecutive_failures=0,
                            last_error=None,
                            response_time_ms=round(response_time_ms, 2)
                        )
                    if was_unhealthy:
                        self.logger.info(f"API recuperada - healthy ({response_time_ms:.1f}ms)")
                    return True
                else:
                    error_msg = f"HTTP {response.status_code}"

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)

        async with self._lock:
            new_failures = self._status.consecutive_failures + 1
            was_healthy = self._status.is_healthy
            became_unhealthy = was_healthy and new_failures >= self.failure_threshold

            self._status = HealthStatus(
                is_healthy=new_failures < self.failure_threshold,
                last_check=datetime.now(),
                consecutive_failures=new_failures,
                last_error=error_msg,
                response_time_ms=round(response_time_ms, 2) if response_time_ms is not None else None
            )

        if became_unhealthy:
            self.logger.error(f"ALERTA: API marked unhealthy: {error_msg}")
        return False

    async def _monitoring_loop(self) -> None:
        """Loop principal de monitoramento."""
        self.logger.debug("Loop de monitoramento iniciado")

        while self._is_running:
            try:
                await self._check_health()
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")

            try:
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break

        self.logger.debug("Loop de monitoramento finalizado")
