"""
cache_layer.py
Sistema de cache em memória thread-safe com TTL.

Implementa cache temporário de dados da API com expiração baseada em TTL,
thread-safety usando locks, e logging detalhado de todas as operações.
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import logging


@dataclass
class CacheEntry:
    """Entrada no cache com dados e metadados."""
    data: Any
    created_at: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        """
        Verifica se a entrada expirou.
        
        Returns:
            True se a entrada expirou, False caso contrário
        """
        return datetime.now() >= self.created_at + timedelta(seconds=self.ttl_seconds)


class CacheLayer:
    """Cache em memória thread-safe com TTL."""
    
    def __init__(self, logger: logging.Logger = None):
        """
        Inicializa o cache layer.
        
        Args:
            logger: Logger para registrar operações (cria novo se None)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self.logger = logger or logging.getLogger(__name__)
        self._hits: int = 0
        self._misses: int = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Busca valor no cache.
        
        Verifica se a chave existe e se os dados não expiraram.
        Remove automaticamente entradas expiradas durante a busca.
        
        Args:
            key: Chave de identificação (ex: game_id)
            
        Returns:
            Dados armazenados ou None se não existir/expirado
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                self.logger.debug(
                    f"Cache miss para chave '{key}'",
                    extra={
                        "key": key,
                        "cache_hit": False
                    }
                )
                return None
            
            entry = self._cache[key]
            
            # Verifica se expirou
            if entry.is_expired():
                self._misses += 1
                self.logger.debug(
                    f"Cache expirado para chave '{key}'",
                    extra={
                        "key": key,
                        "cache_hit": False,
                        "expired": True,
                        "created_at": entry.created_at.isoformat(),
                        "ttl_seconds": entry.ttl_seconds
                    }
                )
                # Remove entrada expirada
                del self._cache[key]
                return None
            
            # Cache hit
            self._hits += 1
            self.logger.debug(
                f"Cache hit para chave '{key}'",
                extra={
                    "key": key,
                    "cache_hit": True,
                    "created_at": entry.created_at.isoformat(),
                    "ttl_seconds": entry.ttl_seconds
                }
            )
            return entry.data
    
    def set(self, key: str, value: Any, ttl_seconds: int = 5) -> None:
        """
        Armazena valor no cache.
        
        Não armazena dados se a chave for "unknown" (game_id inválido).
        
        Args:
            key: Chave de identificação
            value: Dados a armazenar
            ttl_seconds: Tempo de vida em segundos (padrão: 5)
        """
        # Validação: não armazenar se key == "unknown"
        if key == "unknown":
            self.logger.debug(
                "Não armazenando dados com chave 'unknown'",
                extra={
                    "key": key,
                    "rejected": True
                }
            )
            return
        
        with self._lock:
            entry = CacheEntry(
                data=value,
                created_at=datetime.now(),
                ttl_seconds=ttl_seconds
            )
            self._cache[key] = entry
            
            self.logger.debug(
                f"Dados armazenados no cache para chave '{key}'",
                extra={
                    "key": key,
                    "ttl_seconds": ttl_seconds,
                    "created_at": entry.created_at.isoformat()
                }
            )
    
    def delete(self, key: str) -> None:
        """
        Remove entrada do cache.
        
        Args:
            key: Chave de identificação
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug(
                    f"Entrada removida do cache para chave '{key}'",
                    extra={
                        "key": key,
                        "deleted": True
                    }
                )
            else:
                self.logger.debug(
                    f"Tentativa de remover chave inexistente '{key}'",
                    extra={
                        "key": key,
                        "deleted": False
                    }
                )
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self.logger.debug(
                f"Cache limpo completamente",
                extra={
                    "entries_cleared": count
                }
            )
    
    def get_stats(self) -> dict:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com hits, misses, size e hit_rate
        """
        with self._lock:
            size = len(self._cache)
        total = self._hits + self._misses
        hit_rate = round(self._hits / total, 4) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": size,
            "hit_rate": hit_rate,
        }

    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas.
        
        Returns:
            Quantidade de entradas removidas
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.logger.debug(
                    f"Limpeza de cache: {len(expired_keys)} entradas expiradas removidas",
                    extra={
                        "expired_count": len(expired_keys),
                        "expired_keys": expired_keys
                    }
                )
            
            return len(expired_keys)
