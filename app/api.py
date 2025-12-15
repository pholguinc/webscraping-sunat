#!/usr/bin/env python3
"""
API REST con FastAPI para consulta de RUC en SUNAT
"""

from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel
from typing import Optional, List, Union, Any
import time
from scraper import SUNATScraper

app = FastAPI(
    title="API Consulta RUC SUNAT",
    description="API REST para consultar información de RUC en la página de SUNAT",
    version="1.0.0"
)


class RUCResponse(BaseModel):
    """Modelo de respuesta con los datos del RUC"""
    ruc: str
    numero_ruc: Optional[str] = None
    razon_social: Optional[str] = None
    tipo_contribuyente: Optional[str] = None
    nombre_comercial: Optional[str] = None
    fecha_inscripcion: Optional[str] = None
    fecha_inicio_actividades: Optional[str] = None
    estado: Optional[str] = None
    condicion: Optional[str] = None
    direccion_fiscal: Optional[str] = None
    sistema_emision: Optional[str] = None
    actividad_comercio_exterior: Optional[str] = None
    sistema_contabilidad: Optional[str] = None
    actividades_economicas: Optional[List[str]] = None
    comprobantes_pago: Optional[List[str]] = None
    emisor_electronico_desde: Optional[str] = None
    comprobantes_electronicos: Optional[str] = None
    afiliado_ple_desde: Optional[str] = None
    fecha_consulta: str
    tiempo_procesamiento: Optional[str] = None
    cantidad_trabajadores: Optional[List[dict]] = None
    representantes_legales: Optional[List[dict]] = None
    informacion_historica: Optional[dict] = None
    deuda_coactiva: Optional[Any] = None  # Puede ser List[dict] o dict con mensaje
    reactiva_peru: Optional[dict] = None
    programa_covid19: Optional[dict] = None
    establecimientos_anexos: Optional[List[dict]] = None


class ErrorResponse(BaseModel):
    """Modelo de respuesta de error"""
    detail: str


class ConsultaLoteRequest(BaseModel):
    """Modelo de request para consulta en lote"""
    rucs: List[str]
    trabajadores: bool = False
    representantes: bool = False
    historico: bool = False
    deuda_coactiva: bool = False
    reactiva_peru: bool = False
    programa_covid19: bool = False
    establecimientos: bool = False
    use_threading: bool = True
    max_workers: int = 3


class ConsultaLoteResponse(BaseModel):
    """Modelo de respuesta para consulta en lote"""
    total: int
    exitosos: int
    fallidos: int
    tiempo_procesamiento: str
    resultados: List[dict]


@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "API Consulta RUC SUNAT",
        "version": "1.0.0",
        "endpoints": {
            "consultar_ruc": "/consultar/{ruc}",
            "consultar_lote": "/consultar-lote",
            "documentacion": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get(
    "/consultar/{ruc}",
    response_model=RUCResponse,
    responses={
        400: {"model": ErrorResponse, "description": "RUC inválido"},
        404: {"model": ErrorResponse, "description": "RUC no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
    tags=["Consultas"]
)
async def consultar_ruc(
    ruc: str = Path(..., description="Número de RUC de 11 dígitos", example="20267367146"),
    trabajadores: bool = Query(False, description="Incluir datos de trabajadores y prestadores de servicio"),
    representantes: bool = Query(False, description="Incluir representantes legales"),
    historico: bool = Query(False, description="Incluir información histórica"),
    deuda_coactiva: bool = Query(False, description="Incluir deuda coactiva remitida a centrales de riesgo"),
    reactiva_peru: bool = Query(False, description="Incluir información de Reactiva Perú"),
    programa_covid19: bool = Query(False, description="Incluir información del Programa de Garantías COVID-19"),
    establecimientos: bool = Query(False, description="Incluir establecimientos anexos"),
):
    """
    Consulta información de un RUC en SUNAT
    
    **Parámetros:**
    - **ruc**: Número de RUC de 11 dígitos
    - **trabajadores**: Si es True, incluye información de cantidad de trabajadores
    - **representantes**: Si es True, incluye información de representantes legales
    - **historico**: Si es True, incluye información histórica (nombres anteriores, condiciones, direcciones)

    """
    
    # Validar formato del RUC
    if not ruc.isdigit() or len(ruc) != 11:
        raise HTTPException(
            status_code=400, 
            detail="El RUC debe tener exactamente 11 dígitos numéricos"
        )
    
    scraper = SUNATScraper()
    
    try:
        inicio = time.time()
        scraper.setup_driver()
        
        resultado = scraper.consultar_ruc(ruc)
        
        if not resultado:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontraron datos para el RUC {ruc}"
            )
        
        razon_social = resultado.get('razon_social', '')
        
        if trabajadores and razon_social:
            datos_trab = scraper.extraer_cantidad_trabajadores(ruc, razon_social)
            if datos_trab:
                resultado['cantidad_trabajadores'] = datos_trab
        
        if representantes and razon_social:
            datos_repr = scraper.extraer_representantes_legales(ruc, razon_social)
            if datos_repr:
                resultado['representantes_legales'] = datos_repr
        
        if historico and razon_social:
            datos_hist = scraper.extraer_informacion_historica(ruc, razon_social)
            if datos_hist:
                resultado['informacion_historica'] = datos_hist
        
        if deuda_coactiva and razon_social:
            datos_deuda = scraper.extraer_deuda_coactiva(ruc, razon_social)
            if datos_deuda:
                resultado['deuda_coactiva'] = datos_deuda
        
        if reactiva_peru and razon_social:
            datos_reactiva = scraper.extraer_reactiva_peru(ruc, razon_social)
            if datos_reactiva:
                resultado['reactiva_peru'] = datos_reactiva
        
        if programa_covid19 and razon_social:
            datos_covid = scraper.extraer_programa_covid19(ruc, razon_social)
            if datos_covid:
                resultado['programa_covid19'] = datos_covid
        
        if establecimientos and razon_social:
            datos_est = scraper.extraer_establecimientos_anexos(ruc, razon_social)
            if datos_est:
                resultado['establecimientos_anexos'] = datos_est
        
        # Calcular tiempo de procesamiento
        fin = time.time()
        tiempo_total = fin - inicio
        resultado['tiempo_procesamiento'] = f"{tiempo_total:.2f} segundos"
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al consultar el RUC: {str(e)}"
        )
    finally:
        scraper.close()


@app.post(
    "/consultar-lote",
    response_model=ConsultaLoteResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Solicitud inválida"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
    tags=["Consultas"]
)
async def consultar_lote(request: ConsultaLoteRequest):
    """
    Consulta múltiples RUCs en lote (con soporte de procesamiento paralelo)
    
    **Parámetros:**
    - **rucs**: Lista de números de RUC de 11 dígitos
    - **trabajadores**: Si es True, incluye información de cantidad de trabajadores para todos los RUCs
    - **representantes**: Si es True, incluye información de representantes legales para todos los RUCs
    - **historico**: Si es True, incluye información histórica para todos los RUCs
    - **deuda_coactiva**: Si es True, incluye deuda coactiva para todos los RUCs
    - **reactiva_peru**: Si es True, incluye Reactiva Perú para todos los RUCs
    - **programa_covid19**: Si es True, incluye Programa COVID-19 para todos los RUCs
    - **establecimientos**: Si es True, incluye establecimientos anexos para todos los RUCs
    - **use_threading**: Si es True, procesa RUCs en paralelo (default: True)
    - **max_workers**: Número de threads concurrentes (default: 3, max: 5)
    
    **Respuesta:**
    - Retorna un objeto con estadísticas y lista de resultados
    - Cada resultado incluye el campo 'success' indicando si fue exitoso
    - Los RUCs fallidos incluyen el campo 'error' con descripción del problema
    
    """
    
    # Validar que no esté vacía la lista
    if not request.rucs:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un RUC"
        )
    
    # Validar límite razonable
    if len(request.rucs) > 50:
        raise HTTPException(
            status_code=400,
            detail="Máximo 50 RUCs por consulta"
        )
    
    scraper = SUNATScraper()
    
    try:
        inicio = time.time()
        
        scraper.setup_driver()
        
        # Validar max_workers
        max_workers = min(max(1, request.max_workers), 5)  # Entre 1 y 5
        
        # Consultar múltiples RUCs
        resultados = scraper.consultar_multiples_rucs(
            lista_rucs=request.rucs,
            incluir_trabajadores=request.trabajadores,
            incluir_representantes=request.representantes,
            incluir_historico=request.historico,
            incluir_deuda_coactiva=request.deuda_coactiva,
            incluir_reactiva_peru=request.reactiva_peru,
            incluir_programa_covid19=request.programa_covid19,
            incluir_establecimientos=request.establecimientos,
            use_threading=request.use_threading,
            max_workers=max_workers
        )
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        # Contar exitosos y fallidos
        exitosos = sum(1 for r in resultados if r.get('success', False))
        fallidos = len(resultados) - exitosos
        
        return {
            "total": len(resultados),
            "exitosos": exitosos,
            "fallidos": fallidos,
            "tiempo_procesamiento": f"{tiempo_total:.2f} segundos",
            "resultados": resultados
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al procesar el lote: {str(e)}"
        )
    finally:
        scraper.close()


@app.get("/health", tags=["General"])
async def health_check():
    """Verifica el estado de la API"""
    return {
        "status": "healthy",
        "service": "SUNAT RUC Scraper API"
    }


# Para ejecutar: uvicorn api:app --reload
# Documentación: http://localhost:8000/docs
