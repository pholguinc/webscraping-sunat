#!/usr/bin/env python3
"""
Script CLI para consultar RUC en SUNAT
"""

import json
import argparse
import os
from scraper import SUNATScraper


def main():
    parser = argparse.ArgumentParser(
        description='Web Scraper para consultar RUC en SUNAT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    ruc_group = parser.add_mutually_exclusive_group(required=True)
    
    ruc_group.add_argument(
        'ruc',
        type=str,
        nargs='?',
        help='Número de RUC a consultar (11 dígitos)'
    )
    
    ruc_group.add_argument(
        '--rucs',
        type=str,
        help='Múltiples RUCs separados por comas: 20267367146,20100070970)'
    )
    
    ruc_group.add_argument(
        '--archivo',
        type=str,
        help='Ruta a archivo de texto con RUCs (uno por línea)'
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
    
    parser.add_argument(
        '--historico',
        action='store_true',
        help='Extraer también la información histórica (nombres anteriores, condiciones, direcciones)'
    )
    
    parser.add_argument(
        '--deuda-coactiva',
        action='store_true',
        help='Extraer también la deuda coactiva remitida a centrales de riesgo'
    )
    
    parser.add_argument(
        '--reactiva-peru',
        action='store_true',
        help='Extraer también información de Reactiva Perú'
    )
    
    parser.add_argument(
        '--programa-covid19',
        action='store_true',
        help='Extraer también información del Programa de Garantías COVID-19'
    )
    
    parser.add_argument(
        '--establecimientos-anexos',
        action='store_true',
        help='Extraer también establecimientos anexos (sucursales)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Archivo de salida para guardar resultados en JSON'
    )
    
    args = parser.parse_args()
    
    rucs = []
    
    if args.ruc:
        rucs = [args.ruc]
    elif args.rucs:
        rucs = [r.strip() for r in args.rucs.split(',') if r.strip()]
    elif args.archivo:
        if not os.path.exists(args.archivo):
            print(f"Error: El archivo '{args.archivo}' no existe")
            return
        
        with open(args.archivo, 'r') as f:
            rucs = [line.strip() for line in f if line.strip()]
    
    if not rucs:
        print("Error: Debe proporcionar al menos un RUC")
        return
    
    rucs_invalidos = [ruc for ruc in rucs if not ruc.isdigit() or len(ruc) != 11]
    if rucs_invalidos:
        print(f"Error: Los siguientes RUCs son inválidos (deben tener 11 dígitos):")
        for ruc in rucs_invalidos:
            print(f"  - {ruc}")
        return
    
    scraper = SUNATScraper()
    
    try:
        scraper.setup_driver()
        
        print("="*60)
        print("        WEB SCRAPER - CONSULTA RUC SUNAT")
        print("="*60)
        
        if len(rucs) == 1:
            resultado = scraper.consultar_ruc(rucs[0])
            
            if resultado:
                razon_social = resultado.get('razon_social', '')
                
                if args.trabajadores and razon_social:
                    trabajadores = scraper.extraer_cantidad_trabajadores(rucs[0], razon_social)
                    if trabajadores:
                        resultado['cantidad_trabajadores'] = trabajadores
                
                if args.representantes and razon_social:
                    representantes = scraper.extraer_representantes_legales(rucs[0], razon_social)
                    if representantes:
                        resultado['representantes_legales'] = representantes
                
                if args.historico and razon_social:
                    historico = scraper.extraer_informacion_historica(rucs[0], razon_social)
                    if historico:
                        resultado['informacion_historica'] = historico
                
                if args.deuda_coactiva and razon_social:
                    deuda = scraper.extraer_deuda_coactiva(rucs[0], razon_social)
                    if deuda:
                        resultado['deuda_coactiva'] = deuda
                
                if args.reactiva_peru and razon_social:
                    reactiva = scraper.extraer_reactiva_peru(rucs[0], razon_social)
                    if reactiva:
                        resultado['reactiva_peru'] = reactiva
                
                if args.programa_covid19 and razon_social:
                    covid = scraper.extraer_programa_covid19(rucs[0], razon_social)
                    if covid:
                        resultado['programa_covid19'] = covid
                
                if args.establecimientos_anexos and razon_social:
                    establecimientos = scraper.extraer_establecimientos_anexos(rucs[0], razon_social)
                    if establecimientos:
                        resultado['establecimientos_anexos'] = establecimientos
                
                resultados_finales = resultado
            else:
                print("\nNo se pudieron obtener datos del RUC")
                resultados_finales = None
        else:
            resultados = scraper.consultar_multiples_rucs(
                lista_rucs=rucs,
                incluir_trabajadores=args.trabajadores,
                incluir_representantes=args.representantes,
                incluir_historico=args.historico,
                incluir_deuda_coactiva=args.deuda_coactiva,
                incluir_reactiva_peru=args.reactiva_peru,
                incluir_programa_covid19=args.programa_covid19,
                incluir_establecimientos=args.establecimientos_anexos
            )
            resultados_finales = resultados
        
        if resultados_finales:
            print("\n" + "="*60)
            print("DATOS EXTRAÍDOS:")
            print("="*60)
            print(json.dumps(resultados_finales, ensure_ascii=False, indent=2))
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(resultados_finales, f, ensure_ascii=False, indent=2)
                print(f"\n Resultados guardados en: {args.output}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
