"""
retry_system.py
Sistema de retry com backoff exponencial para requisições HTTP.

Implementa retry automático com estratégia de backoff exponencial,
tratamento especial para erro 400 (remoção de parâmetro startingTime),
e logging detalhado de todas as operações.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import time
import asyncio
import requests
import httpx
import orjson
import logging


@dataclass
class RetryConfig:
    """Configuração do sistema de retry."""
    max_attempts: int = 3
    base_delay: float = 2.0  # segundos
    max_delay: float = 60.0
    backoff_factor: float = 2.0


class AsyncHTTPClient:
    """
    Singleton AsyncHTTPClient com connection pooling.
    
    Mantém uma conexão persistente para reuse entre requisições,
    reduzindo latência e overhead de rede.
    """
    _client: httpx.AsyncClient | None = None
    
    @classmethod
    def get_client(cls, headers: dict = None) -> httpx.AsyncClient:
        """Retorna ou cria o cliente HTTP com connection pooling."""
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                headers=headers or {},
                follow_redirects=True,
            )
        return cls._client
    
    @classmethod
    async def close(cls):
        """Fecha o cliente HTTP."""
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None


class RetrySystem:
    """Sistema de retry com backoff exponencial."""
    
    def __init__(self, config: RetryConfig = None, logger: logging.Logger = None):
        """
        Inicializa o sistema de retry.
        
        Args:
            config: Configuração de retry (usa padrão se None)
            logger: Logger para registrar operações (cria novo se None)
        """
        self.config = config or RetryConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._total_requests: int = 0
        self._successful_requests: int = 0
    
    def fetch_with_retry(
        self,
        url: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        timeout: int = 10,
        retry_without_param: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa requisição HTTP com retry automático.
        
        Implementa retry com backoff exponencial (2s, 4s, 8s) e tratamento
        especial para erro 400 (remove parâmetro especificado e tenta novamente).
        
        Args:
            url: URL do endpoint
            params: Parâmetros da query string
            headers: Headers HTTP
            timeout: Timeout em segundos
            retry_without_param: Nome do parâmetro a remover em caso de erro 400
            
        Returns:
            Dados JSON da resposta ou None se todas as tentativas falharem
        """
        params = params or {}
        headers = headers or {}
        last_error = None
        
        self._total_requests += 1
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                start_time = time.time()
                
                self.logger.debug(
                    f"Tentativa {attempt}/{self.config.max_attempts} para {url}",
                    extra={
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts,
                        "url": url,
                        "params": params
                    }
                )
                
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Sucesso
                if response.status_code == 200:
                    self._successful_requests += 1
                    self.logger.debug(
                        f"Requisição bem-sucedida na tentativa {attempt}",
                        extra={
                            "attempt": attempt,
                            "url": url,
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time_ms, 2)
                        }
                    )
                    return orjson.loads(response.content)
                
                # Erro 400 - tentar sem parâmetro específico
                elif response.status_code == 400 and retry_without_param and retry_without_param in params:
                    self.logger.debug(
                        f"Erro 400 na tentativa {attempt}, removendo parâmetro '{retry_without_param}'",
                        extra={
                            "attempt": attempt,
                            "url": url,
                            "status_code": 400,
                            "removed_param": retry_without_param,
                            "response_time_ms": round(response_time_ms, 2)
                        }
                    )
                    
                    # Remove o parâmetro e tenta novamente imediatamente
                    params = {k: v for k, v in params.items() if k != retry_without_param}
                    continue
                
                # Outros erros HTTP
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_detail = response.text[:200]  # Primeiros 200 chars
                        error_msg += f": {error_detail}"
                    except:
                        pass
                    
                    self.logger.warning(
                        f"Erro HTTP {response.status_code} na tentativa {attempt}",
                        extra={
                            "attempt": attempt,
                            "url": url,
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time_ms, 2),
                            "error": error_msg
                        }
                    )
                    
                    last_error = error_msg
                    
            except requests.exceptions.Timeout as e:
                self.logger.warning(
                    f"Timeout na tentativa {attempt}",
                    extra={
                        "attempt": attempt,
                        "url": url,
                        "timeout": timeout,
                        "error": str(e)
                    }
                )
                last_error = f"Timeout após {timeout}s"
                
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(
                    f"Erro de conexão na tentativa {attempt}",
                    extra={
                        "attempt": attempt,
                        "url": url,
                        "error": str(e)
                    }
                )
                last_error = f"Erro de conexão: {str(e)}"
                
            except Exception as e:
                self.logger.error(
                    f"Erro inesperado na tentativa {attempt}",
                    extra={
                        "attempt": attempt,
                        "url": url,
                        "error": str(e)
                    },
                    exc_info=True
                )
                last_error = f"Erro inesperado: {str(e)}"
            
            # Se não é a última tentativa, aguarda antes de tentar novamente
            if attempt < self.config.max_attempts:
                delay = self._calculate_delay(attempt)
                self.logger.debug(
                    f"Aguardando {delay}s antes da próxima tentativa",
                    extra={
                        "attempt": attempt,
                        "delay_seconds": delay
                    }
                )
                time.sleep(delay)
        
        # Todas as tentativas falharam
        self.logger.error(
            f"Todas as {self.config.max_attempts} tentativas falharam para {url}",
            extra={
                "url": url,
                "params": params,
                "max_attempts": self.config.max_attempts,
                "last_error": last_error
            }
        )
        
        return None
    
    async def async_fetch_with_retry(
        self,
        url: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        timeout: int = 10,
        retry_without_param: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa requisição HTTP assíncrona com httpx e retry automático.
        Usa connection pooling para melhor performance.
        """
        params = params or {}
        headers = headers or {}
        last_error = None
        
        self._total_requests += 1
        
        # Usa cliente com connection pooling (singleton)
        client = AsyncHTTPClient.get_client(headers)
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                start_time = time.time()
                
                self.logger.debug(
                    f"[Async] Tentativa {attempt}/{self.config.max_attempts} para {url}",
                    extra={"url": url, "params": params}
                )
                
                response = await client.get(url, params=params, timeout=timeout)
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    self._successful_requests += 1
                    return orjson.loads(response.content)
                
                elif response.status_code == 400 and retry_without_param and retry_without_param in params:
                    self.logger.debug(f"Erro 400, removendo {retry_without_param}")
                    params = {k: v for k, v in params.items() if k != retry_without_param}
                    continue
                else:
                    last_error = f"HTTP {response.status_code}"
            except httpx.RequestError as e:
                last_error = f"RequestError: {str(e)}"
            except Exception as e:
                last_error = f"Error: {str(e)}"
            
            if attempt < self.config.max_attempts:
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
                
        self.logger.error(f"Falha total em {url}: {last_error}")
        return None
    
    def get_stats(self) -> dict:
        """
        Retorna estatísticas do sistema de retry.
        
        Returns:
            Dict com total_requests, successful_requests e success_rate
        """
        success_rate = (
            round(self._successful_requests / self._total_requests, 4)
            if self._total_requests > 0
            else 0.0
        )
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "success_rate": success_rate,
        }

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcula delay para próxima tentativa usando backoff exponencial.
        
        Fórmula: base_delay * (backoff_factor ^ attempt)
        Exemplo com base_delay=2.0 e backoff_factor=2.0:
        - Tentativa 1: 2.0 * (2.0 ^ 1) = 4.0s
        - Tentativa 2: 2.0 * (2.0 ^ 2) = 8.0s
        
        Args:
            attempt: Número da tentativa atual (1-indexed)
            
        Returns:
            Delay em segundos, limitado ao max_delay
        """
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        return min(delay, self.config.max_delay)
