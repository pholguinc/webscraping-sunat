#!/usr/bin/env python3
"""
Web Scraper para consulta de RUC en SUNAT
"""

import json
import time
import argparse
from datetime import datetime
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
                print(f"Datos extraídos exitosamente para RUC {numero_ruc}")
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
                boton = self.driver.find_element(By.CLASS_NAME, "btnInfNumTra")
                print(" Botón encontrado en la página, haciendo clic...")
                boton.click()
                time.sleep(3)
            except NoSuchElementException:
                print("ℹ Botón no visible, intentando envío directo del formulario...")
                
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
                boton = self.driver.find_element(By.CLASS_NAME, "btnInfRepLeg")
                print(" Botón encontrado en la página, haciendo clic...")
                boton.click()
                time.sleep(3)
            except NoSuchElementException:
                print("ℹ Botón no visible, intentando envío directo del formulario...")
                
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


            
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            print("Navegador cerrado")


def main():
    parser = argparse.ArgumentParser(
        description='Web Scraper para consultar RUC en SUNAT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        'ruc',
        type=str,
        help='Número de RUC a consultar (11 dígitos)'
    )
    
    parser.add_argument(
        '--trabajadores',
        action='store_true',
        help='Extraer también la cantidad de trabajadores y prestadores de servicio'
    )
    
    parser.add_argument(
        '--representantes',
        action='store_true',
        help='Extraer también los representantes legales'
    )
    
    args = parser.parse_args()
    
    if not args.ruc.isdigit() or len(args.ruc) != 11:
        print("Error: El RUC debe tener exactamente 11 dígitos numéricos")
        return
    
    scraper = SUNATScraper()
    
    try:
        scraper.setup_driver()
        
        print("="*60)
        print("        WEB SCRAPER - CONSULTA RUC SUNAT")
        print("="*60)
        
        resultado = scraper.consultar_ruc(args.ruc)
        
        if resultado:
            razon_social = resultado.get('razon_social', '')
            
            # Extraer cantidad de trabajadores si se solicitó
            if args.trabajadores:
                if razon_social:
                    trabajadores = scraper.extraer_cantidad_trabajadores(args.ruc, razon_social)
                    if trabajadores:
                        resultado['cantidad_trabajadores'] = trabajadores
                else:
                    print("No se pudo extraer cantidad de trabajadores: falta razón social")
            
            # Extraer representantes legales si se solicitó
            if args.representantes:
                if razon_social:
                    representantes = scraper.extraer_representantes_legales(args.ruc, razon_social)
                    if representantes:
                        resultado['representantes_legales'] = representantes
                else:
                    print("No se pudo extraer representantes legales: falta razón social")
            
            print("\n" + "="*60)
            print("DATOS EXTRAÍDOS:")
            print("="*60)
            print(json.dumps(resultado, ensure_ascii=False, indent=2))
        else:
            print("\nNo se pudieron obtener datos del RUC")
            print("Posibles causas:")
            print("  - El RUC no existe o está inactivo")
            print("  - La estructura de la página cambió")
            print("  - Error en la conexión o timeout")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
