"""
polling_service.py
Serviço de polling automático para dados ao vivo de partidas.

Gerencia o ciclo de vida do polling em thread daemon separada,
com suporte a pausa/resume e logging detalhado de transições de estado.
"""

from enum import Enum
import asyncio
import logging
from typing import Optional, Callable, Any, Awaitable


class PollingState(Enum):
    """Estados do polling service."""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class PollingService:
    """Serviço de polling automático para dados ao vivo."""

    def __init__(
        self,
        fetch_callback: Callable[[], Awaitable[Any]],
        interval_seconds: int = 10,
        logger: logging.Logger = None
    ):
        """
        Inicializa o polling service.
        """
        self.fetch_callback = fetch_callback
        self.interval_seconds = interval_seconds
        self.logger = logger or logging.getLogger(__name__)

        self._state = PollingState.IDLE
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    async def start(self) -> None:
        """Inicia o polling as síncronamente."""
        async with self._lock:
            if self._state == PollingState.ACTIVE:
                self.logger.warning("PollingService já está ativo")
                return
            if self._state == PollingState.STOPPED:
                self.logger.warning("PollingService foi parado; crie uma nova instância")
                return

            self._stop_event.clear()
            self._pause_event.set()
            self._state = PollingState.ACTIVE
            self._task = asyncio.create_task(self._polling_loop())

        self.logger.info(
            f"PollingService iniciado (intervalo: {self.interval_seconds}s)",
            extra={"polling_state": PollingState.ACTIVE.value}
        )

    async def stop(self) -> None:
        """Para o polling gracefully."""
        async with self._lock:
            if self._state == PollingState.STOPPED:
                return
            self._state = PollingState.STOPPED

        self._pause_event.set()
        self._stop_event.set()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self.logger.info(
            "PollingService parado",
            extra={"polling_state": PollingState.STOPPED.value}
        )

    async def pause(self) -> None:
        """Pausa o polling temporariamente."""
        async with self._lock:
            if self._state != PollingState.ACTIVE:
                return
            self._state = PollingState.PAUSED

        self._pause_event.clear()
        self.logger.info("PollingService pausado")

    async def resume(self) -> None:
        """Resume o polling pausado."""
        async with self._lock:
            if self._state != PollingState.PAUSED:
                return
            self._state = PollingState.ACTIVE

        self._pause_event.set()
        self.logger.info("PollingService resumido")

    async def _polling_loop(self) -> None:
        """Loop principal de polling."""
        self.logger.info("Ciclo de polling iniciado")

        while not self._stop_event.is_set():
            await self._pause_event.wait()

            if self._stop_event.is_set():
                break

            try:
                self.logger.info("Iniciando iteração de polling")
                await self.fetch_callback()
                self.logger.info("Iteração de polling concluída")
            except Exception as e:
                self.logger.error(f"Erro no polling: {e}", exc_info=True)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

        self.logger.info("Ciclo de polling finalizado")

    async def get_state(self) -> PollingState:
        """Retorna estado atual do polling."""
        async with self._lock:
            return self._state
