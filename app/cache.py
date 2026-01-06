#!/usr/bin/env python3
"""
Sistema de caché en memoria para resultados de consultas RUC
"""

import time
import threading
from typing import Optional, Dict, Any


class RUCCache:
    """
    Caché en memoria con TTL para resultados de consultas RUC.
    Thread-safe para uso concurrente.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, ttl_seconds: int = 3600):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, ttl_seconds: int = 3600):
        if self._initialized:
            return
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds  # 1 hora por defecto
        self._lock = threading.RLock()
        self._initialized = True
    
    def _make_key(self, ruc: str, options: Dict[str, bool]) -> str:
        """Genera una clave única basada en RUC y opciones"""
        options_str = "_".join(f"{k}={v}" for k, v in sorted(options.items()) if v)
        return f"{ruc}:{options_str}" if options_str else ruc
    
    def get(self, ruc: str, options: Dict[str, bool] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resultado del caché si existe y no ha expirado.
        
        Args:
            ruc: Número de RUC
            options: Diccionario con las opciones de consulta
        
        Returns:
            Datos cacheados o None si no existe/expiró
        """
        options = options or {}
        key = self._make_key(ruc, options)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Verificar TTL
            if time.time() - entry['timestamp'] > self._ttl:
                del self._cache[key]
                return None
            
            return entry['data']
    
    def set(self, ruc: str, data: Dict[str, Any], options: Dict[str, bool] = None):
        """
        Almacena un resultado en el caché.
        
        Args:
            ruc: Número de RUC
            data: Datos a cachear
            options: Diccionario con las opciones de consulta
        """
        options = options or {}
        key = self._make_key(ruc, options)
        
        with self._lock:
            self._cache[key] = {
                'data': data.copy(),
                'timestamp': time.time()
            }
    
    def invalidate(self, ruc: str = None):
        """
        Invalida entradas del caché.
        
        Args:
            ruc: RUC específico a invalidar. Si es None, invalida todo.
        """
        with self._lock:
            if ruc is None:
                self._cache.clear()
            else:
                # Eliminar todas las entradas que empiecen con este RUC
                keys_to_delete = [k for k in self._cache if k.startswith(f"{ruc}:") or k == ruc]
                for key in keys_to_delete:
                    del self._cache[key]
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché"""
        with self._lock:
            valid_entries = 0
            expired_entries = 0
            current_time = time.time()
            
            for entry in self._cache.values():
                if current_time - entry['timestamp'] > self._ttl:
                    expired_entries += 1
                else:
                    valid_entries += 1
            
            return {
                'total_entries': len(self._cache),
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'ttl_seconds': self._ttl
            }
    
    def cleanup(self):
        """Elimina entradas expiradas del caché"""
        with self._lock:
            current_time = time.time()
            keys_to_delete = [
                k for k, v in self._cache.items()
                if current_time - v['timestamp'] > self._ttl
            ]
            for key in keys_to_delete:
                del self._cache[key]
            
            return len(keys_to_delete)


# Instancia global del caché
_cache: RUCCache = None


def get_cache(ttl_seconds: int = 3600) -> RUCCache:
    """Obtiene la instancia global del caché"""
    global _cache
    if _cache is None:
        _cache = RUCCache(ttl_seconds=ttl_seconds)
    return _cache
