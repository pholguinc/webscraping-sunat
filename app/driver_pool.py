#!/usr/bin/env python3
"""
Pool de drivers Chrome reutilizables para mejorar performance
"""

import threading
import queue
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class DriverPool:
    """
    Singleton que mantiene un pool de drivers Chrome reutilizables.
    Reduce el tiempo de respuesta al evitar crear un nuevo navegador por request.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, pool_size: int = 2):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, pool_size: int = 2):
        if self._initialized:
            return
        
        self._pool_size = pool_size
        self._drivers = queue.Queue(maxsize=pool_size)
        self._all_drivers = []
        self._chrome_options = self._create_chrome_options()
        self._service = None
        self._initialized = True
        
        # Registrar cleanup al cerrar
        atexit.register(self.shutdown)
    
    def _create_chrome_options(self) -> webdriver.ChromeOptions:
        """Crea las opciones optimizadas para Chrome headless"""
        options = webdriver.ChromeOptions()
        
        # Modo headless optimizado
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
        
        # Optimizaciones de rendimiento
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # Deshabilitar carga de imágenes para mayor velocidad
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'disk-cache-size': 4096
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
    def _create_driver(self) -> webdriver.Chrome:
        """Crea un nuevo driver Chrome"""
        if self._service is None:
            self._service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=self._service, options=self._chrome_options)
        self._all_drivers.append(driver)
        return driver
    
    def initialize(self):
        """Pre-inicializa el pool de drivers"""
        print(f"🚀 Inicializando pool con {self._pool_size} drivers...")
        for i in range(self._pool_size):
            try:
                driver = self._create_driver()
                self._drivers.put(driver)
                print(f"   ✓ Driver {i+1}/{self._pool_size} listo")
            except Exception as e:
                print(f"   ✗ Error creando driver {i+1}: {e}")
        print(f"✓ Pool inicializado con {self._drivers.qsize()} drivers")
    
    def acquire(self, timeout: float = 30.0) -> webdriver.Chrome:
        """
        Obtiene un driver del pool.
        Si no hay disponibles, espera hasta timeout segundos.
        """
        try:
            driver = self._drivers.get(timeout=timeout)
            # Verificar que el driver esté funcionando
            try:
                _ = driver.current_url
                return driver
            except Exception:
                # Driver corrupto, crear uno nuevo
                print("⚠ Driver corrupto detectado, creando nuevo...")
                try:
                    driver.quit()
                except:
                    pass
                return self._create_driver()
        except queue.Empty:
            # No hay drivers disponibles, crear uno temporal
            print("⚠ Pool agotado, creando driver temporal...")
            return self._create_driver()
    
    def release(self, driver: webdriver.Chrome):
        """Devuelve un driver al pool después de limpiarlo"""
        try:
            # Limpiar estado del driver completamente antes de devolverlo
            try:
                # Navegar a página en blanco para limpiar estado
                driver.get("about:blank")
                driver.delete_all_cookies()
            except Exception as e:
                print(f"⚠ Error limpiando driver: {e}")
                # Si falla la limpieza, crear uno nuevo en lugar de devolver corrupto
                try:
                    driver.quit()
                except:
                    pass
                try:
                    driver = self._create_driver()
                except:
                    return  # No podemos crear uno nuevo, simplemente no devolver nada
            
            # Intentar poner de vuelta en el pool
            try:
                self._drivers.put_nowait(driver)
            except queue.Full:
                # Como el pull está lleno, cerramos el driver
                try:
                    driver.quit()
                except:
                    pass
        except Exception as e:
            print(f"⚠ Error liberando driver: {e}")
    
    def shutdown(self):
        """Cierra todos los drivers del pool"""
        print("Cerrando pool de drivers...")
        for driver in self._all_drivers:
            try:
                driver.quit()
            except:
                pass
        self._all_drivers.clear()
        
        # Vaciar la cola
        while not self._drivers.empty():
            try:
                self._drivers.get_nowait()
            except:
                pass
        
        print("✓ Pool cerrado")


# Instancia global del pool
_pool: DriverPool = None


def get_driver_pool(pool_size: int = 2) -> DriverPool:
    """Obtiene la instancia global del pool de drivers"""
    global _pool
    if _pool is None:
        _pool = DriverPool(pool_size=pool_size)
    return _pool


def init_pool(pool_size: int = 2):
    """Inicializa el pool de drivers (llamar al startup de la app)"""
    pool = get_driver_pool(pool_size)
    pool.initialize()


def shutdown_pool():
    """Cierra el pool de drivers (llamar al shutdown de la app)"""
    global _pool
    if _pool is not None:
        _pool.shutdown()
        _pool = None
