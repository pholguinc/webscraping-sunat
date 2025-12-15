#!/usr/bin/env python3
"""
Web Scraper para consulta de RUC en SUNAT
"""

import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class SUNATScraper:
    """Clase para realizar web scraping de RUC en SUNAT"""
    
    def __init__(self):
        """Iniciar el scraper"""
        self.url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.driver = None
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
    def consultar_ruc(self, numero_ruc):
     
        try:
            print(f"Navegando a SUNAT...")
            self.driver.get(self.url)
            
            wait = WebDriverWait(self.driver, 10)
            input_ruc = wait.until(
                EC.presence_of_element_located((By.ID, "txtRuc"))
            )
            
            
            print(f"Consultando RUC: {numero_ruc}")
            input_ruc.clear()
            time.sleep(0.5) 
            input_ruc.send_keys(numero_ruc)
            time.sleep(1) 
            
            btn_buscar = wait.until(
                EC.element_to_be_clickable((By.ID, "btnAceptar"))
            )
            btn_buscar.click()
            
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "jcrS00Alias" in driver.current_url or 
                    len(driver.find_elements(By.XPATH, "//td[contains(text(), 'RUC')]")) > 0
                )
            except TimeoutException:
                try:
                    alert = self.driver.switch_to.alert
                    print(f"Alerta detectada: {alert.text}")
                    alert.accept()
                    return None
                except:
                    pass
            
            time.sleep(1)
            
            datos = self.extraer_datos()
            
            if datos:
                datos['ruc'] = numero_ruc
                datos['fecha_consulta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f" Datos extraídos exitosamente para RUC {numero_ruc}")
                return datos
            else:
                print(f"No se encontraron datos para el RUC {numero_ruc}")
                return None
                
        except TimeoutException:
            print(f"Error: Tiempo de espera agotado al consultar RUC {numero_ruc}")
            return None
        except Exception as e:
            print(f"Error al consultar RUC {numero_ruc}: {str(e)}")
            return None
            
    def extraer_datos(self):
      
        try:
            datos = {}
            
            def extraer_campo(label_text):
                try:
                    xpath = f"//h4[contains(text(), '{label_text}')]/parent::div/following-sibling::div//p[@class='list-group-item-text']"
                    element = self.driver.find_element(By.XPATH, xpath)
                    return element.text.strip()
                except NoSuchElementException:
                    try:
                        xpath = f"//h4[contains(text(), '{label_text}')]/parent::div/parent::div//p[@class='list-group-item-text']"
                        element = self.driver.find_element(By.XPATH, xpath)
                        return element.text.strip()
                    except NoSuchElementException:
                        return None
            
            try:
                ruc_text = self.driver.find_element(By.XPATH, "//h4[contains(text(), 'Número de RUC:')]/parent::div/following-sibling::div//h4").text.strip()
                if ' - ' in ruc_text:
                    parts = ruc_text.split(' - ', 1)
                    datos['numero_ruc'] = parts[0].strip()
                    datos['razon_social'] = parts[1].strip()
            except NoSuchElementException:
                pass
            
            tipo = extraer_campo('Tipo Contribuyente:')
            if tipo:
                datos['tipo_contribuyente'] = tipo
            
            nombre_comercial = extraer_campo('Nombre Comercial:')
            if nombre_comercial:
                datos['nombre_comercial'] = nombre_comercial
            
            fecha_inscripcion = extraer_campo('Fecha de Inscripción:')
            if fecha_inscripcion:
                datos['fecha_inscripcion'] = fecha_inscripcion
            
            fecha_inicio = extraer_campo('Fecha de Inicio de Actividades:')
            if fecha_inicio:
                datos['fecha_inicio_actividades'] = fecha_inicio
            
            estado = extraer_campo('Estado del Contribuyente:')
            if estado:
                datos['estado'] = estado
            
            condicion = extraer_campo('Condición del Contribuyente:')
            if condicion:
                datos['condicion'] = condicion
            
            direccion = extraer_campo('Domicilio Fiscal:')
            if direccion:
                datos['direccion_fiscal'] = direccion
            
            sistema_emision = extraer_campo('Sistema Emisión de Comprobante:')
            if sistema_emision:
                datos['sistema_emision'] = sistema_emision
            
            comercio = extraer_campo('Actividad Comercio Exterior:')
            if comercio:
                datos['actividad_comercio_exterior'] = comercio
            
            contabilidad = extraer_campo('Sistema Contabilidad:')
            if contabilidad:
                datos['sistema_contabilidad'] = contabilidad
            
            try:
                actividades = []
                actividades_elements = self.driver.find_elements(By.XPATH, "//h4[contains(text(), 'Actividad(es) Económica(s):')]/parent::div/following-sibling::div//table//tr/td")
                for actividad in actividades_elements:
                    texto = actividad.text.strip()
                    if texto:
                        actividades.append(texto)
                if actividades:
                    datos['actividades_economicas'] = actividades
            except NoSuchElementException:
                pass
            
            try:
                comprobantes = []
                comprobantes_elements = self.driver.find_elements(By.XPATH, "//h4[contains(text(), 'Comprobantes de Pago')]/parent::div/following-sibling::div//table//tr/td")
                for comprobante in comprobantes_elements:
                    texto = comprobante.text.strip()
                    if texto:
                        comprobantes.append(texto)
                if comprobantes:
                    datos['comprobantes_pago'] = comprobantes
            except NoSuchElementException:
                pass
            
            emisor_desde = extraer_campo('Emisor electrónico desde:')
            if emisor_desde:
                datos['emisor_electronico_desde'] = emisor_desde
            
            comp_electronicos = extraer_campo('Comprobantes Electrónicos:')
            if comp_electronicos:
                datos['comprobantes_electronicos'] = comp_electronicos
            
            ple_desde = extraer_campo('Afiliado al PLE desde:')
            if ple_desde:
                datos['afiliado_ple_desde'] = ple_desde
            
            return datos if datos else None
            
        except Exception as e:
            print(f"Error al extraer datos: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def extraer_cantidad_trabajadores(self, numero_ruc, razon_social):
        try:
            print("\n" + "="*60)
            print("Consultando cantidad de trabajadores...")
            print("="*60)
            
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfNumTra"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfNumTra")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getCantTrab',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                
                self.driver.execute_script(script)
                time.sleep(3)
            
            try:
                screenshot_path = f"/tmp/sunat_trabajadores_{numero_ruc}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot guardado en: {screenshot_path}")
            except:
                pass
            
            print(f"URL actual: {self.driver.current_url}")
            
            datos_trabajadores = []
            
            try:
              
                tabla = self.driver.find_element(By.XPATH, "//table[@class='table']")
                
                encabezados = []
                headers = tabla.find_elements(By.XPATH, ".//thead//th")
                for header in headers:
                    texto = header.text.strip()
                    if texto:
                        encabezados.append(texto)
                
                print(f"Encabezados encontrados: {encabezados}")
                
                filas = tabla.find_elements(By.XPATH, ".//tbody//tr")
                print(f"Encontradas {len(filas)} filas de datos")
                
                for fila in filas:
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    
                    if len(celdas) >= 4: 
                        periodo = celdas[0].text.strip()
                        trabajadores = celdas[1].text.strip().replace(' ', '') 
                        pensionistas = celdas[2].text.strip().replace(' ', '')
                        prestadores = celdas[3].text.strip().replace(' ', '')
                        
                        registro = {
                            'periodo': periodo,
                            'trabajadores': trabajadores,
                            'pensionistas': pensionistas,
                            'prestadores_servicio': prestadores
                        }
                        
                        datos_trabajadores.append(registro)
                        print(f"   {periodo}: {trabajadores} trabajadores, {pensionistas} pensionistas, {prestadores} prestadores")
                
                if datos_trabajadores:
                    print(f"\nExtraídos {len(datos_trabajadores)} períodos de datos")
                    return datos_trabajadores
                else:
                    print("No se encontraron datos en la tabla")
                    return None
                    
            except NoSuchElementException:
                print("No se encontró la tabla de trabajadores")
                return None
            except Exception as e:
                print(f"Error al extraer datos de trabajadores: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
                
        except Exception as e:
            print(f"Error al consultar cantidad de trabajadores: {str(e)}")
            return None

    
    def extraer_representantes_legales(self, numero_ruc, razon_social):
        """Extrae los representantes legales de la empresa"""
        try:
            print("\n" + "="*60)
            print("Consultando representantes legales...")
            print("="*60)
            
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfRepLeg"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfRepLeg")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getRepLeg',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                
                self.driver.execute_script(script)
                time.sleep(3)
            
            try:
                screenshot_path = f"/tmp/sunat_representantes_{numero_ruc}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot guardado en: {screenshot_path}")
            except:
                pass
            
            print(f"URL actual: {self.driver.current_url}")
            
            datos_representantes = []
            
            try:
                tabla = self.driver.find_element(By.XPATH, "//table[@class='table']")
                
                encabezados = []
                headers = tabla.find_elements(By.XPATH, ".//thead//th")
                for header in headers:
                    texto = header.text.strip()
                    if texto:
                        encabezados.append(texto)
                
                print(f"Encabezados encontrados: {encabezados}")
                
                filas = tabla.find_elements(By.XPATH, ".//tbody//tr")
                print(f"Encontradas {len(filas)} representantes legales")
                
                for fila in filas:
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    
                    if len(celdas) >= 5:
                        tipo_doc = celdas[0].text.strip()
                        nro_doc = celdas[1].text.strip()
                        nombre = celdas[2].text.strip()
                        cargo = celdas[3].text.strip()
                        fecha_desde = celdas[4].text.strip()
                        
                        representante = {
                            'tipo_documento': tipo_doc,
                            'nro_documento': nro_doc,
                            'nombre': nombre,
                            'cargo': cargo,
                            'fecha_desde': fecha_desde
                        }
                        
                        datos_representantes.append(representante)
                        print(f"   {nombre} - {cargo} (desde {fecha_desde})")
                
                if datos_representantes:
                    print(f"\nExtraídos {len(datos_representantes)} representantes legales")
                    return datos_representantes
                else:
                    print("No se encontraron representantes legales")
                    return None
                    
            except NoSuchElementException:
                print("No se encontró la tabla de representantes legales")
                return None
            except Exception as e:
                print(f"Error al extraer representantes legales: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
                
        except Exception as e:
            print(f"Error al consultar representantes legales: {str(e)}")
            return None

    
    def extraer_informacion_historica(self, numero_ruc, razon_social):
        """Extrae la información histórica de la empresa"""
        try:
            print("\n" + "="*60)
            print("Consultando información histórica...")
            print("="*60)
            
            # Intentar hacer clic en el botón de información histórica
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfHis"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfHis")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(5)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(5)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                # Envío directo del formulario usando JavaScript
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getinfHis',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                
                self.driver.execute_script(script)
                time.sleep(6)  # Aumentado a 6 segundos
            
            print(f"URL actual: {self.driver.current_url}")
            
            # Esperar a que la página cargue completamente - intentar esperar por el panel
            try:
                wait = WebDriverWait(self.driver, 15)
                # Esperar por el div que contiene los resultados
                wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "panel-primary"))
                )
                print("✓ Panel de resultados detectado")
                time.sleep(3)  # Espera adicional para que las tablas se rendericen
            except TimeoutException:
                print("⚠ Timeout esperando el panel de resultados")
            
            # Intentar obtener el HTML para debug
            try:
                page_title = self.driver.find_element(By.TAG_NAME, "h3").text
                print(f"Título de página: {page_title}")
            except:
                pass
            
            informacion_historica = {
                'razon_social_anteriores': [],
                'condicion_anteriores': [],
                'direccion_anteriores': []
            }
            
            try:
                # Estrategia 1: Buscar tablas dentro del panel
                tablas = self.driver.find_elements(By.XPATH, "//div[@class='panel panel-primary']//table[@class='table']")
                print(f"Estrategia 1 (panel + table): {len(tablas)} tablas encontradas")
                
                # Estrategia 2: Buscar tablas con class='table'
                if len(tablas) == 0:
                    tablas = self.driver.find_elements(By.XPATH, "//table[@class='table']")
                    print(f"Estrategia 2 (table.table): {len(tablas)} tablas encontradas")
                
                # Estrategia 3: Buscar cualquier tabla en el container
                if len(tablas) == 0:
                    tablas = self.driver.find_elements(By.XPATH, "//div[@class='table-responsive']//table")
                    print(f"Estrategia 3 (table-responsive): {len(tablas)} tablas encontradas")
                
                # Estrategia 4: Buscar todas las tablas
                if len(tablas) == 0:
                    tablas = self.driver.find_elements(By.TAG_NAME, "table")
                    print(f"Estrategia 4 (todas las tablas): {len(tablas)} tablas encontradas")
                
                if len(tablas) == 0:
                    # Debug: Obtener el HTML de la página
                    print("\n⚠ DEBUG: No se encontraron tablas. Analizando HTML...")
                    try:
                        # Verificar si hay contenido en el panel
                        panels = self.driver.find_elements(By.CLASS_NAME, "panel")
                        print(f"   Paneles encontrados: {len(panels)}")
                        
                        # Verificar divs con table-responsive
                        responsive_divs = self.driver.find_elements(By.CLASS_NAME, "table-responsive")
                        print(f"   Divs table-responsive: {len(responsive_divs)}")
                        
                        # Intentar obtener el contenido del body
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "INFORMACION HISTORICA" in body_text.upper():
                            print("   ✓ La página contiene texto de información histórica")
                        else:
                            print("   ✗ La página NO contiene texto esperado")
                            print(f"   Primeros 500 caracteres: {body_text[:500]}")
                    except Exception as debug_e:
                        print(f"   Error en debug: {debug_e}")
                
                # Procesar cada tabla encontrada
                for idx, tabla in enumerate(tablas):
                    try:
                        # Obtener encabezados para identificar la tabla
                        headers = tabla.find_elements(By.XPATH, ".//thead//th")
                        header_texts = [h.text.strip() for h in headers]
                        print(f"\nTabla {idx+1} - Encabezados: {header_texts}")
                        
                        filas = tabla.find_elements(By.XPATH, ".//tbody//tr")
                        print(f"   Filas en tbody: {len(filas)}")
                        
                        # Identificar tipo de tabla por sus encabezados
                        if len(header_texts) >= 2:
                            # Tabla de nombres anteriores o direcciones (2 columnas)
                            if "Nombre" in str(header_texts) or "Razón Social" in str(header_texts):
                                # Primera tabla: Nombres
                                print(f"   → Identificada como tabla de Razón Social Anteriores")
                                for fila in filas:
                                    celdas = fila.find_elements(By.TAG_NAME, "td")
                                    if len(celdas) >= 2:
                                        razon_social_ant = celdas[0].text.strip()
                                        fecha_baja = celdas[1].text.strip()
                                        
                                        if razon_social_ant:  # Solo agregar si hay datos
                                            registro = {
                                                'razon_social': razon_social_ant,
                                                'fecha_baja': fecha_baja
                                            }
                                            informacion_historica['razon_social_anteriores'].append(registro)
                                            print(f"      {razon_social_ant} - Baja: {fecha_baja}")
                            
                            elif "Direcci" in str(header_texts) or "Domicilio" in str(header_texts):
                                # Tabla de direcciones
                                print(f"   → Identificada como tabla de Direcciones")
                                for fila in filas:
                                    celdas = fila.find_elements(By.TAG_NAME, "td")
                                    if len(celdas) >= 2:
                                        direccion = celdas[0].text.strip()
                                        fecha_baja = celdas[1].text.strip()
                                        
                                        if direccion:
                                            registro = {
                                                'direccion': direccion,
                                                'fecha_baja': fecha_baja
                                            }
                                            informacion_historica['direccion_anteriores'].append(registro)
                                            print(f"      {direccion} - Baja: {fecha_baja}")
                            
                            # Tabla de condición del contribuyente (3 columnas)
                            elif len(header_texts) == 3 and ("Condici" in str(header_texts) or 
                                                             "Fecha Desde" in str(header_texts)):
                                print(f"   → Identificada como tabla de Condición del Contribuyente")
                                for fila in filas:
                                    celdas = fila.find_elements(By.TAG_NAME, "td")
                                    if len(celdas) >= 3:
                                        condicion = celdas[0].text.strip()
                                        fecha_desde = celdas[1].text.strip()
                                        fecha_hasta = celdas[2].text.strip()
                                        
                                        if condicion:
                                            registro = {
                                                'condicion': condicion,
                                                'fecha_desde': fecha_desde,
                                                'fecha_hasta': fecha_hasta
                                            }
                                            informacion_historica['condicion_anteriores'].append(registro)
                                            print(f"      {condicion}: {fecha_desde} → {fecha_hasta}")
                            
                            elif len(header_texts) == 2 and len(filas) > 0:
                                # Tabla genérica de 2 columnas - identificar por posición
                                print(f"   → Tabla genérica de 2 columnas (índice {idx})")
                                primer_header = header_texts[0].lower()
                                
                                # Determinar tipo por el primer encabezado o posición
                                if "direcci" in primer_header or "domicilio" in primer_header:
                                    # Es tabla de direcciones
                                    for fila in filas:
                                        celdas = fila.find_elements(By.TAG_NAME, "td")
                                        if len(celdas) >= 2:
                                            direccion = celdas[0].text.strip()
                                            fecha_baja = celdas[1].text.strip()
                                            if direccion:
                                                registro = {
                                                    'direccion': direccion,
                                                    'fecha_baja': fecha_baja
                                                }
                                                informacion_historica['direccion_anteriores'].append(registro)
                                else:
                                    # Asumir nombres si es la primera tabla o tiene "nombre" en encabezado
                                    es_nombres = idx == 0 or "nombre" in primer_header or "raz" in primer_header
                                    
                                    for fila in filas:
                                        celdas = fila.find_elements(By.TAG_NAME, "td")
                                        if len(celdas) >= 2:
                                            valor = celdas[0].text.strip()
                                            fecha = celdas[1].text.strip()
                                            
                                            if valor:
                                                if es_nombres or len(valor) < 150:
                                                    registro = {
                                                        'razon_social': valor,
                                                        'fecha_baja': fecha
                                                    }
                                                    informacion_historica['razon_social_anteriores'].append(registro)
                                                else:
                                                    registro = {
                                                        'direccion': valor,
                                                        'fecha_baja': fecha
                                                    }
                                                    informacion_historica['direccion_anteriores'].append(registro)
                                
                    except Exception as e:
                        print(f"   ⚠ Error procesando tabla {idx+1}: {str(e)}")
                        continue
                
                # Verificar si se obtuvo al menos algún dato
                total_registros = (
                    len(informacion_historica['razon_social_anteriores']) + 
                    len(informacion_historica['condicion_anteriores']) + 
                    len(informacion_historica['direccion_anteriores'])
                )
                
                if total_registros > 0:
                    print(f"\n✓ Extraídos {total_registros} registros históricos en total")
                    print(f"   - Razones sociales: {len(informacion_historica['razon_social_anteriores'])}")
                    print(f"   - Condiciones: {len(informacion_historica['condicion_anteriores'])}")
                    print(f"   - Direcciones: {len(informacion_historica['direccion_anteriores'])}")
                    return informacion_historica
                else:
                    print("ℹ No se encontraron datos históricos en las tablas")
                    return None
                    
            except NoSuchElementException:
                print("✗ No se encontraron tablas de información histórica")
                return None
            except Exception as e:
                print(f"Error al extraer información histórica: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
                
        except Exception as e:
            print(f"Error al consultar información histórica: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    
    def extraer_deuda_coactiva(self, numero_ruc, razon_social):
        """
        Extrae la información de deuda coactiva remitida a centrales de riesgo
        
        Args:
            numero_ruc: Número de RUC
            razon_social: Razón social de la empresa
            
        Returns:
            - Lista de diccionarios con la deuda coactiva si hay deuda
            - Diccionario con {'tiene_deuda': False, 'mensaje': '...'} si no hay deuda
            - None si hay error en la extracción
        """
        try:
            print("\n" + "="*60)
            print("Consultando deuda coactiva...")
            print("="*60)
            
            # Intentar hacer clic en el botón
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfDeuCoa"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfDeuCoa")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                # Enviar formulario directamente con JavaScript
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getInfoDC',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                self.driver.execute_script(script)
                time.sleep(3)
            
            # Esperar a que cargue la página de deuda coactiva
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-primary")))
                time.sleep(2)
                
                print(f"\n📍 URL actual: {self.driver.current_url}")
                
                # Buscar la tabla de deuda coactiva
                deuda_coactiva = []
                
                try:
                    # La tabla está dentro de un div con clase table-responsive
                    tablas = self.driver.find_elements(By.CSS_SELECTOR, "div.table-responsive table.table")
                    
                    if not tablas:
                        # Intentar con selector más general
                        tablas = self.driver.find_elements(By.TAG_NAME, "table")
                    
                    print(f"\n🔍 Encontradas {len(tablas)} tablas en la página")
                    
                    for idx, tabla in enumerate(tablas):
                        print(f"\n📊 Procesando tabla {idx + 1}...")
                        
                        try:
                            # Buscar encabezados
                            headers = tabla.find_elements(By.TAG_NAME, "th")
                            header_texts = [h.text.strip() for h in headers]
                            
                            print(f"   Encabezados: {header_texts}")
                            
                            # Verificar si es la tabla de deuda (tiene 4 columnas específicas)
                            if len(header_texts) >= 4 and any("Monto" in h for h in header_texts):
                                print(f"   → Identificada como tabla de Deuda Coactiva")
                                
                                # Extraer filas
                                filas = tabla.find_elements(By.TAG_NAME, "tbody")
                                if filas:
                                    filas = filas[0].find_elements(By.TAG_NAME, "tr")
                                else:
                                    filas = tabla.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                                
                                print(f"   Filas encontradas: {len(filas)}")
                                
                                for fila in filas:
                                    celdas = fila.find_elements(By.TAG_NAME, "td")
                                    
                                    if len(celdas) >= 4:
                                        monto = celdas[0].text.strip()
                                        periodo = celdas[1].text.strip()
                                        fecha_inicio = celdas[2].text.strip()
                                        entidad = celdas[3].text.strip()
                                        
                                        if monto and periodo:
                                            registro = {
                                                'monto': monto,
                                                'periodo_tributario': periodo,
                                                'fecha_inicio_cobranza': fecha_inicio,
                                                'entidad': entidad
                                            }
                                            deuda_coactiva.append(registro)
                                            print(f"      {periodo}: S/ {monto} - {entidad}")
                        
                        except Exception as e:
                            print(f"   ⚠ Error procesando tabla {idx + 1}: {str(e)}")
                            continue
                    
                    if len(deuda_coactiva) > 0:
                        print(f"\n✓ Extraídos {len(deuda_coactiva)} registros de deuda coactiva")
                        return deuda_coactiva
                    else:
                        # Buscar el mensaje cuando no hay deuda
                        try:
                            mensaje_elemento = self.driver.find_element(By.CSS_SELECTOR, "div.list-group-item div.col-sm-12")
                            mensaje = mensaje_elemento.text.strip()
                            
                            if mensaje:
                                print(f"ℹ Mensaje encontrado: {mensaje}")
                                return {
                                    'tiene_deuda': False,
                                    'mensaje': mensaje
                                }
                        except NoSuchElementException:
                            pass
                        
                        print("ℹ No se encontró deuda coactiva registrada")
                        return {
                            'tiene_deuda': False,
                            'mensaje': 'No se encontró información de deuda coactiva'
                        }
                        
                except NoSuchElementException:
                    print("✗ No se encontraron tablas de deuda coactiva")
                    return None
                except Exception as e:
                    print(f"Error al extraer deuda coactiva: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
                    
            except Exception as e:
                print(f"Error esperando la página de deuda coactiva: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Error al consultar deuda coactiva: {str(e)}\")")
            import traceback
            traceback.print_exc()
            return None

    
    def extraer_reactiva_peru(self, numero_ruc, razon_social):
        """
        Extrae la información de Reactiva Perú: Deuda en cobranza coactiva
        
        Args:
            numero_ruc: Número de RUC
            razon_social: Razón social de la empresa
            
        Returns:
            Diccionario con información de Reactiva Perú o None si no aplica
        """
        try:
            print("\n" + "="*60)
            print("Consultando Reactiva Perú...")
            print("="*60)
            
            # Intentar hacer clic en el botón
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfReaPer"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfReaPer")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                # Enviar formulario directamente con JavaScript
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getReactivaPeru',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                self.driver.execute_script(script)
                time.sleep(3)
            
            # Esperar a que cargue la página de Reactiva Perú
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-primary")))
                time.sleep(2)
                
                print(f"\n📍 URL actual: {self.driver.current_url}")
                
                # Extraer información de la página
                reactiva_info = {}
                
                try:
                    # Buscar el label de SI/NO
                    tiene_deuda = None
                    fecha_actualizacion = None
                    decreto = None
                    
                    # Buscar por label-danger (SI) o label-success (NO)
                    try:
                        label_element = self.driver.find_element(By.CSS_SELECTOR, "span.label")
                        tiene_deuda = label_element.text.strip()
                        print(f"   ✓ Estado encontrado: {tiene_deuda}")
                    except NoSuchElementException:
                        print("   ⚠ No se encontró el label de estado")
                    
                    # Buscar la fecha de actualización
                    try:
                        h5_elements = self.driver.find_elements(By.TAG_NAME, "h5")
                        for h5 in h5_elements:
                            texto = h5.text.strip()
                            if "actualizada al" in texto.lower():
                                # Extraer la fecha del texto
                                import re
                                match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
                                if match:
                                    fecha_actualizacion = match.group(1)
                                    print(f"   ✓ Fecha de actualización: {fecha_actualizacion}")
                            elif "decreto" in texto.lower():
                                decreto = texto
                                print(f"   ✓ Decreto: {decreto}")
                    except Exception as e:
                        print(f"   ⚠ Error extrayendo detalles: {str(e)}")
                    
                    if tiene_deuda:
                        reactiva_info = {
                            'tiene_deuda_mayor_1_uit': tiene_deuda,
                            'fecha_actualizacion': fecha_actualizacion,
                            'decreto': decreto
                        }
                        print(f"\n✓ Información de Reactiva Perú extraída")
                        return reactiva_info
                    else:
                        print("ℹ No se encontró información de Reactiva Perú")
                        return None
                        
                except NoSuchElementException:
                    print("✗ No se encontró información de Reactiva Perú")
                    return None
                except Exception as e:
                    print(f"Error al extraer Reactiva Perú: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
                    
            except Exception as e:
                print(f"Error esperando la página de Reactiva Perú: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Error al consultar Reactiva Perú: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    
    def extraer_programa_covid19(self, numero_ruc, razon_social):
        """
        Extrae la información del Programa de Garantías COVID-19
        
        Args:
            numero_ruc: Número de RUC
            razon_social: Razón social de la empresa
            
        Returns:
            Diccionario con información del programa COVID-19 o None si no aplica
        """
        try:
            print("\n" + "="*60)
            print("Consultando Programa de Garantías COVID-19...")
            print("="*60)
            
            # Intentar hacer clic en el botón
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfCovid"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfCovid")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    # Si no es clickeable, hacer clic con JavaScript
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                # Enviar formulario directamente con JavaScript
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getPGarantiaCOVID19',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                self.driver.execute_script(script)
                time.sleep(3)
            
            # Esperar a que cargue la página
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-primary")))
                time.sleep(2)
                
                print(f"\n📍 URL actual: {self.driver.current_url}")
                
                # Extraer información
                covid_info = {}
                
                try:
                    tiene_deuda = None
                    fecha_actualizacion = None
                    ley = None
                    
                    #  Buscar el label de SI/NO
                    try:
                        label_element = self.driver.find_element(By.CSS_SELECTOR, "span.label")
                        tiene_deuda = label_element.text.strip()
                        print(f"   ✓ Estado encontrado: {tiene_deuda}")
                    except NoSuchElementException:
                        print("   ⚠ No se encontró el label de estado")
                    
                    # Buscar fecha y ley
                    try:
                        h5_elements = self.driver.find_elements(By.TAG_NAME, "h5")
                        for h5 in h5_elements:
                            texto = h5.text.strip()
                            if "actualizada al" in texto.lower():
                                import re
                                match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
                                if match:
                                    fecha_actualizacion = match.group(1)
                                    print(f"   ✓ Fecha de actualización: {fecha_actualizacion}")
                            elif "ley" in texto.lower():
                                ley = texto
                                print(f"   ✓ Ley: {ley}")
                    except Exception as e:
                        print(f"   ⚠ Error extrayendo detalles: {str(e)}")
                    
                    if tiene_deuda:
                        covid_info = {
                            'tiene_deuda_mayor_1_uit': tiene_deuda,
                            'fecha_actualizacion': fecha_actualizacion,
                            'ley': ley
                        }
                        print(f"\n✓ Información del Programa COVID-19 extraída")
                        return covid_info
                    else:
                        print("ℹ No se encontró información del Programa COVID-19")
                        return None
                        
                except NoSuchElementException:
                    print("✗ No se encontró información del Programa COVID-19")
                    return None
                except Exception as e:
                    print(f"Error al extraer Programa COVID-19: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
                    
            except Exception as e:
                print(f"Error esperando la página del Programa COVID-19: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Error al consultar Programa COVID-19: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    
    def extraer_establecimientos_anexos(self, numero_ruc, razon_social):
        """
        Extrae los establecimientos anexos (sucursales) de la empresa
        
        Args:
            numero_ruc: Número de RUC
            razon_social: Razón social de la empresa
            
        Returns:
            Lista de diccionarios con establecimientos anexos o None si no hay
        """
        try:
            print("\n" + "="*60)
            print("Consultando establecimientos anexos...")
            print("="*60)
            
            # Intentar hacer clic en el botón
            try:
                # Esperar a que el botón esté presente en el DOM
                wait = WebDriverWait(self.driver, 10)
                boton = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btnInfLocAnex"))
                )
                print("✓ Botón encontrado en la página")
                
                # Hacer scroll hacia el botón para asegurar que sea visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
                time.sleep(1)
                
                # Intentar esperar a que sea clickeable
                try:
                    boton = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnInfLocAnex")))
                    print("✓ Haciendo clic en el botón...")
                    boton.click()
                    time.sleep(3)
                except TimeoutException:
                    print("⚠ Botón no clickeable, usando JavaScript...")
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(3)
                    
            except (NoSuchElementException, TimeoutException):
                print("ℹ Botón no encontrado o no visible, intentando envío directo del formulario...")
                
                # Enviar formulario directamente con JavaScript
                script = f"""
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/cl-ti-itmrconsruc/jcrS00Alias';
                
                var inputs = {{
                    'accion': 'getLocAnex',
                    'contexto': 'ti-it',
                    'modo': '1',
                    'nroRuc': '{numero_ruc}',
                    'desRuc': '{razon_social}'
                }};
                
                for (var key in inputs) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = inputs[key];
                    form.appendChild(input);
                }}
                
                document.body.appendChild(form);
                form.submit();
                """
                self.driver.execute_script(script)
                time.sleep(3)
            
            # Esperar a que cargue la página
            try:
                wait = WebDriverWait(self.driver, 10)
                # Buscar por la tabla
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))
                time.sleep(2)
                
                print(f"\n📍 URL actual: {self.driver.current_url}")
                
                # Buscar tabla de establecimientos
                establecimientos = []
                
                try:
                    tabla = self.driver.find_element(By.CSS_SELECTOR, "table.table")
                    
                    # Verificar encabezados
                    headers = tabla.find_elements(By.TAG_NAME, "th")
                    header_texts = [h.text.strip() for h in headers]
                    print(f"\n   Encabezados encontrados: {header_texts}")
                    
                    # Extraer filas del tbody
                    tbody = tabla.find_element(By.TAG_NAME, "tbody")
                    filas = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    print(f"   Filas encontradas: {len(filas)}")
                    
                    for fila in filas:
                        celdas = fila.find_elements(By.TAG_NAME, "td")
                        
                        if len(celdas) >= 4:
                            codigo = celdas[0].text.strip()
                            tipo = celdas[1].text.strip()
                            direccion = celdas[2].text.strip()
                            actividad = celdas[3].text.strip()
                            
                            if codigo:
                                establecimiento = {
                                    'codigo': codigo,
                                    'tipo_establecimiento': tipo,
                                    'direccion': direccion,
                                    'actividad_economica': actividad
                                }
                                establecimientos.append(establecimiento)
                                print(f"      {codigo}: {tipo} - {direccion[:50]}...")
                    
                    if len(establecimientos) > 0:
                        print(f"\n✓ Extraídos {len(establecimientos)} establecimientos anexos")
                        return establecimientos
                    else:
                        print("ℹ No se encontraron establecimientos anexos")
                        return None
                        
                except NoSuchElementException:
                    print("✗ No se encontró tabla de establecimientos anexos")
                    return None
                except Exception as e:
                    print(f"Error al extraer establecimientos: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
                    
            except Exception as e:
                print(f"Error esperando la página de establecimientos: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Error al consultar establecimientos anexos: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


    @staticmethod
    def _worker_procesar_ruc(ruc, incluir_trabajadores=False, incluir_representantes=False, 
                              incluir_historico=False, incluir_deuda_coactiva=False,
                              incluir_reactiva_peru=False, incluir_programa_covid19=False,
                              incluir_establecimientos=False):
        """
        Worker estático para procesar un RUC individualmente en un thread separado.
        Cada worker crea su propia instancia de SUNATScraper y WebDriver.
        
        Args:
            ruc: Número de RUC a consultar
            incluir_trabajadores: Si True, incluye datos de trabajadores
            incluir_representantes: Si True, incluye datos de representantes
            incluir_historico: Si True, incluye información histórica
            incluir_deuda_coactiva: Si True, incluye deuda coactiva
            incluir_reactiva_peru: Si True, incluye Reactiva Perú
            incluir_programa_covid19: Si True, incluye Programa COVID-19
            incluir_establecimientos: Si True, incluye establecimientos anexos
            
        Returns:
            Dict con resultado del procesamiento (success, data, error)
        """
        scraper = None
        try:
            # Validar formato del RUC
            if not ruc.isdigit() or len(ruc) != 11:
                return {
                    'ruc': ruc,
                    'success': False,
                    'error': 'El RUC debe tener exactamente 11 dígitos numéricos',
                    'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # Crear instancia de scraper para este thread
            scraper = SUNATScraper()
            scraper.setup_driver()
            
            # Consultar datos básicos del RUC
            resultado = scraper.consultar_ruc(ruc)
            
            if not resultado:
                return {
                    'ruc': ruc,
                    'success': False,
                    'error': 'No se encontraron datos para este RUC',
                    'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # Obtener la razón social para las consultas adicionales
            razon_social = resultado.get('razon_social', '')
            resultado['success'] = True
            
            # Extraer información adicional según los parámetros
            if incluir_trabajadores and razon_social:
                datos_trab = scraper.extraer_cantidad_trabajadores(ruc, razon_social)
                if datos_trab:
                    resultado['cantidad_trabajadores'] = datos_trab
            
            if incluir_representantes and razon_social:
                datos_repr = scraper.extraer_representantes_legales(ruc, razon_social)
                if datos_repr:
                    resultado['representantes_legales'] = datos_repr
            
            if incluir_historico and razon_social:
                datos_hist = scraper.extraer_informacion_historica(ruc, razon_social)
                if datos_hist:
                    resultado['informacion_historica'] = datos_hist
            
            if incluir_deuda_coactiva and razon_social:
                datos_deuda = scraper.extraer_deuda_coactiva(ruc, razon_social)
                if datos_deuda:
                    resultado['deuda_coactiva'] = datos_deuda
            
            if incluir_reactiva_peru and razon_social:
                datos_reactiva = scraper.extraer_reactiva_peru(ruc, razon_social)
                if datos_reactiva:
                    resultado['reactiva_peru'] = datos_reactiva
            
            if incluir_programa_covid19 and razon_social:
                datos_covid = scraper.extraer_programa_covid19(ruc, razon_social)
                if datos_covid:
                    resultado['programa_covid19'] = datos_covid
            
            if incluir_establecimientos and razon_social:
                datos_establecimientos = scraper.extraer_establecimientos_anexos(ruc, razon_social)
                if datos_establecimientos:
                    resultado['establecimientos_anexos'] = datos_establecimientos
            
            return resultado
            
        except Exception as e:
            return {
                'ruc': ruc,
                'success': False,
                'error': str(e),
                'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        finally:
            # Asegurar que el driver se cierre
            if scraper and scraper.driver:
                try:
                    scraper.driver.quit()
                except:
                    pass


    def consultar_multiples_rucs_paralelo(self, lista_rucs, max_workers=3, 
                                          incluir_trabajadores=False, incluir_representantes=False,
                                          incluir_historico=False, incluir_deuda_coactiva=False,
                                          incluir_reactiva_peru=False, incluir_programa_covid19=False,
                                          incluir_establecimientos=False):
        """
        Consulta múltiples RUCs en paralelo usando ThreadPoolExecutor.
        Cada RUC se procesa en un thread independiente con su propio driver.
        
        Args:
            lista_rucs: Lista de números de RUC a consultar
            max_workers: Número máximo de threads concurrentes (default: 3, recomendado: 3-5)
            incluir_trabajadores: Si True, incluye datos de trabajadores
            incluir_representantes: Si True, incluye datos de representantes
            incluir_historico: Si True, incluye información histórica
            incluir_deuda_coactiva: Si True, incluye deuda coactiva
            incluir_reactiva_peru: Si True, incluye Reactiva Perú
            incluir_programa_covid19: Si True, incluye Programa COVID-19
            incluir_establecimientos: Si True, incluye establecimientos anexos
            
        Returns:
            Lista de diccionarios con resultados (incluye éxitos y errores)
        """
        total = len(lista_rucs)
        resultados = []
        
        print(f"\n{'='*60}")
        print(f"Consultando {total} RUC(s) en PARALELO (max {max_workers} workers)...")
        print(f"{'='*60}\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas al pool de threads
            futures = {
                executor.submit(
                    SUNATScraper._worker_procesar_ruc,
                    ruc,
                    incluir_trabajadores,
                    incluir_representantes,
                    incluir_historico,
                    incluir_deuda_coactiva,
                    incluir_reactiva_peru,
                    incluir_programa_covid19,
                    incluir_establecimientos
                ): ruc 
                for ruc in lista_rucs
            }
            
            # Procesar resultados a medida que se completan
            completados = 0
            for future in as_completed(futures):
                ruc = futures[future]
                completados += 1
                
                try:
                    resultado = future.result(timeout=120)  # 2 minutos timeout por RUC
                    resultados.append(resultado)
                    
                    if resultado.get('success', False):
                        print(f"[{completados}/{total}] ✓ RUC {ruc}: Completado exitosamente")
                    else:
                        error_msg = resultado.get('error', 'Error desconocido')
                        print(f"[{completados}/{total}] ✗ RUC {ruc}: {error_msg}")
                        
                except TimeoutError:
                    print(f"[{completados}/{total}] ⏱ RUC {ruc}: Timeout (>120s)")
                    resultados.append({
                        'ruc': ruc,
                        'success': False,
                        'error': 'Timeout: el procesamiento tomó más de 120 segundos',
                        'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    print(f"[{completados}/{total}] ✗ RUC {ruc}: Excepción - {str(e)}")
                    resultados.append({
                        'ruc': ruc,
                        'success': False,
                        'error': f'Excepción en thread: {str(e)}',
                        'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        print(f"\n{'='*60}")
        exitosos = sum(1 for r in resultados if r.get('success', False))
        print(f"Consultas completadas: {exitosos}/{total} exitosas")
        print(f"{'='*60}\n")
        
        return resultados


    def consultar_multiples_rucs(self, lista_rucs, incluir_trabajadores=False, incluir_representantes=False, 
                                  incluir_historico=False, incluir_deuda_coactiva=False, 
                                  incluir_reactiva_peru=False, incluir_programa_covid19=False, 
                                  incluir_establecimientos=False, use_threading=False, max_workers=3):
        """
        Consulta múltiples RUCs. Puede usar procesamiento secuencial o paralelo.
        
        Args:
            lista_rucs: Lista de números de RUC a consultar
            incluir_trabajadores: Si True, incluye datos de trabajadores
            incluir_representantes: Si True, incluye datos de representantes
            incluir_historico: Si True, incluye información histórica
            incluir_deuda_coactiva: Si True, incluye deuda coactiva
            incluir_reactiva_peru: Si True, incluye información de Reactiva Perú
            incluir_programa_covid19: Si True, incluye información del Programa COVID-19
            incluir_establecimientos: Si True, incluye establecimientos anexos
            use_threading: Si True, usa procesamiento paralelo (default: False para retrocompatibilidad)
            max_workers: Número de threads concurrentes si use_threading=True (default: 3)
            
        Returns:
            Lista de diccionarios con resultados (incluye éxitos y errores)
        """
        # Si se solicita threading, delegar al método paralelo
        if use_threading:
            return self.consultar_multiples_rucs_paralelo(
                lista_rucs=lista_rucs,
                max_workers=max_workers,
                incluir_trabajadores=incluir_trabajadores,
                incluir_representantes=incluir_representantes,
                incluir_historico=incluir_historico,
                incluir_deuda_coactiva=incluir_deuda_coactiva,
                incluir_reactiva_peru=incluir_reactiva_peru,
                incluir_programa_covid19=incluir_programa_covid19,
                incluir_establecimientos=incluir_establecimientos
            )
        
        # Procesamiento secuencial (comportamiento original)
        resultados = []
        total = len(lista_rucs)
        
        print(f"\n{'='*60}")
        print(f"Consultando {total} RUC(s)...")
        print(f"{'='*60}\n")
        
        for idx, ruc in enumerate(lista_rucs, 1):
            try:
                print(f"[{idx}/{total}] Consultando RUC: {ruc}")
                
                # Validar formato del RUC
                if not ruc.isdigit() or len(ruc) != 11:
                    resultado = {
                        'ruc': ruc,
                        'error': 'El RUC debe tener exactamente 11 dígitos numéricos',
                        'success': False,
                        'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    resultados.append(resultado)
                    print(f"  RUC inválido: {ruc}")
                    continue
                
                # Consultar RUC
                resultado = self.consultar_ruc(ruc)
                
                if resultado:
                    resultado['success'] = True
                    razon_social = resultado.get('razon_social', '')
                    
                    # Extraer trabajadores si se solicitó
                    if incluir_trabajadores and razon_social:
                        datos_trab = self.extraer_cantidad_trabajadores(ruc, razon_social)
                        if datos_trab:
                            resultado['cantidad_trabajadores'] = datos_trab
                    
                    # Extraer representantes si se solicitó
                    if incluir_representantes and razon_social:
                        datos_repr = self.extraer_representantes_legales(ruc, razon_social)
                        if datos_repr:
                            resultado['representantes_legales'] = datos_repr
                    
                    # Extraer información histórica si se solicitó
                    if incluir_historico and razon_social:
                        datos_hist = self.extraer_informacion_historica(ruc, razon_social)
                        if datos_hist:
                            resultado['informacion_historica'] = datos_hist
                    
                    # Extraer deuda coactiva si se solicitó
                    if incluir_deuda_coactiva and razon_social:
                        datos_deuda = self.extraer_deuda_coactiva(ruc, razon_social)
                        if datos_deuda:
                            resultado['deuda_coactiva'] = datos_deuda
                    
                    # Extraer Reactiva Perú si se solicitó
                    if incluir_reactiva_peru and razon_social:
                        datos_reactiva = self.extraer_reactiva_peru(ruc, razon_social)
                        if datos_reactiva:
                            resultado['reactiva_peru'] = datos_reactiva
                    
                    # Extraer Programa COVID-19 si se solicitó
                    if incluir_programa_covid19 and razon_social:
                        datos_covid = self.extraer_programa_covid19(ruc, razon_social)
                        if datos_covid:
                            resultado['programa_covid19'] = datos_covid
                    
                    # Extraer establecimientos anexos si se solicitó
                    if incluir_establecimientos and razon_social:
                        datos_establecimientos = self.extraer_establecimientos_anexos(ruc, razon_social)
                        if datos_establecimientos:
                            resultado['establecimientos_anexos'] = datos_establecimientos
                    
                    resultados.append(resultado)
                else:
                    resultado = {
                        'ruc': ruc,
                        'error': 'No se encontraron datos para este RUC',
                        'success': False,
                        'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    resultados.append(resultado)
                
                # Pequeño delay entre consultas para evitar bloqueos
                if idx < total:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  Error al consultar RUC {ruc}: {str(e)}")
                resultado = {
                    'ruc': ruc,
                    'error': str(e),
                    'success': False,
                    'fecha_consulta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                resultados.append(resultado)
        
        print(f"\n{'='*60}")
        exitosos = sum(1 for r in resultados if r.get('success', False))
        print(f"Consultas completadas: {exitosos}/{total} exitosas")
        print(f"{'='*60}\n")
        
        return resultados
            
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            print("Navegador cerrado")
