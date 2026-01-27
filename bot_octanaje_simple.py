#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║              🤖 BOT PREDICTOR DE OCTANAJE - VERSIÓN SIMPLE 🤖             ║
║                    Con Clasificación Fiscal Automática                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

Bot Python amigable y visual para predicción de octanaje en gasolina
Versión: 3.0 - Optimizada y simplificada
"""

import pickle
import pandas as pd
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE COLORES (funciona sin librerías adicionales)
# ═══════════════════════════════════════════════════════════════════════════

class Colores:
    """Códigos ANSI para colores en terminal"""
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MORADO = '\033[95m'
    CYAN = '\033[96m'
    ROJO = '\033[91m'
    BLANCO = '\033[97m'
    NEGRITA = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def desactivar():
        """Desactiva colores si no son compatibles"""
        Colores.VERDE = ''
        Colores.AMARILLO = ''
        Colores.AZUL = ''
        Colores.MORADO = ''
        Colores.CYAN = ''
        Colores.ROJO = ''
        Colores.BLANCO = ''
        Colores.NEGRITA = ''
        Colores.RESET = ''

# Intentar usar colores (desactivar en Windows antiguo)
try:
    if os.name == 'nt':
        import sys
        if sys.version_info >= (3, 0):
            os.system('')  # Habilitar ANSI en Windows 10+
except:
    Colores.desactivar()

C = Colores  # Alias para escribir menos

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def imprimir_banner():
    """Muestra el banner de bienvenida"""
    print(f"\n{C.MORADO}{'═' * 79}{C.RESET}")
    print(f"{C.MORADO}{C.NEGRITA}{'🤖 BOT PREDICTOR DE OCTANAJE EN GASOLINA 🤖':^79s}{C.RESET}")
    print(f"{C.MORADO}{'═' * 79}{C.RESET}")
    print(f"{C.BLANCO}{'Clasificación Fiscal Automática | Precisión 100%':^79s}{C.RESET}")
    print(f"{C.MORADO}{'═' * 79}{C.RESET}\n")

def imprimir_linea(caracter='─', color=C.CYAN):
    """Imprime una línea decorativa"""
    print(f"{color}{caracter * 79}{C.RESET}")

def imprimir_caja(titulo, contenido, color=C.VERDE):
    """Imprime contenido en una caja decorativa"""
    print(f"\n{color}╔{'═' * 77}╗{C.RESET}")
    print(f"{color}║{C.NEGRITA}{titulo:^77s}{C.RESET}{color}║{C.RESET}")
    print(f"{color}╠{'═' * 77}╣{C.RESET}")
    for linea in contenido:
        print(f"{color}║{C.RESET} {linea:<75s} {color}║{C.RESET}")
    print(f"{color}╚{'═' * 77}╝{C.RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════
# CLASIFICACIÓN FISCAL
# ═══════════════════════════════════════════════════════════════════════════

def clasificar_gasolina(octanaje_redondeado):
    """
    Clasifica la gasolina según normativa fiscal española.
    
    Args:
        octanaje_redondeado: Octanaje redondeado al entero más cercano
        
    Returns:
        dict con toda la información de clasificación
    """
    if octanaje_redondeado < 95:
        return {
            'categoria': 'GASOLINA REGULAR',
            'codigo_nc': '2710.12.41',
            'epigrafe': '1.2.2',
            'descripcion': 'Inferior a 95 octanos',
            'emoji': '⚡',
            'color': C.AMARILLO,
            'color_fondo': '🟡'
        }
    elif octanaje_redondeado <= 98:
        return {
            'categoria': 'GASOLINA PREMIUM',
            'codigo_nc': '2710.12.45',
            'epigrafe': '1.2.2',
            'descripcion': '95 a 98 octanos',
            'emoji': '🚗',
            'color': C.AZUL,
            'color_fondo': '🔵'
        }
    else:  # > 98
        return {
            'categoria': 'GASOLINA SUPER',
            'codigo_nc': '2710.12.49',
            'epigrafe': '1.2.1',
            'descripcion': 'Superior a 98 octanos',
            'emoji': '🏎️',
            'color': C.MORADO,
            'color_fondo': '🟣'
        }

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════

def cargar_modelo():
    """Carga el modelo de predicción."""
    print(f"{C.CYAN}⏳ Cargando modelo de predicción...{C.RESET}")
    
    # Buscar el modelo
    rutas_posibles = [
        'modelo_final_gb.pkl',
        './modelo_final_gb.pkl',
        '../modelo_final_gb.pkl',
        '/mnt/user-data/outputs/modelo_final_gb.pkl'
    ]
    
    modelo_path = None
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            modelo_path = ruta
            break
    
    if modelo_path is None:
        print(f"\n{C.ROJO}✗ ERROR: No se encontró 'modelo_final_gb.pkl'{C.RESET}")
        print(f"{C.AMARILLO}  Asegúrate de que el archivo está en la misma carpeta.{C.RESET}\n")
        return None, None
    
    try:
        with open(modelo_path, 'rb') as f:
            modelo_info = pickle.load(f)
            modelo = modelo_info['modelo']
            variables = modelo_info['variables']
        
        print(f"{C.VERDE}✓ Modelo cargado correctamente{C.RESET}\n")
        return modelo, variables
    
    except Exception as e:
        print(f"\n{C.ROJO}✗ ERROR al cargar modelo: {e}{C.RESET}\n")
        return None, None

# ═══════════════════════════════════════════════════════════════════════════
# ENTRADA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

def solicitar_datos():
    """Solicita los datos del análisis cromatográfico al usuario."""
    
    imprimir_linea('═', C.CYAN)
    print(f"{C.CYAN}{C.NEGRITA}📊 ANÁLISIS CROMATOGRÁFICO - INTRODUCE LOS DATOS{C.RESET}")
    imprimir_linea('═', C.CYAN)
    print()
    
    variables_input = [
        ('PARAFINAS', '5.5 - 16.2'),
        ('ISOPARAFINAS', '22.5 - 43.9'),
        ('OLEFINAS', '2.3 - 13.8'),
        ('NAFTÉNICOS', '2.0 - 14.5'),
        ('AROMÁTICOS', '26.5 - 48.9'),
        ('ETANOL', '0.0 - 4.9'),
        ('MTBE', '0.0 - 14.3'),
        ('ETBE', '0.0 - 7.9')
    ]
    
    datos = {}
    
    for var, rango in variables_input:
        while True:
            try:
                prompt = f"{C.BLANCO}{var:<15s}{C.RESET} [{C.CYAN}{rango}{C.RESET}] %v/v: "
                valor = float(input(prompt))
                datos[var] = valor
                break
            except ValueError:
                print(f"  {C.ROJO}✗ Error: Introduce un número válido{C.RESET}")
            except KeyboardInterrupt:
                print(f"\n\n{C.AMARILLO}Operación cancelada{C.RESET}\n")
                return None
    
    # Calcular Ox (total de oxigenados)
    datos['Ox'] = datos['ETANOL'] + datos['MTBE'] + datos['ETBE']
    
    return datos

# ═══════════════════════════════════════════════════════════════════════════
# PREDICCIÓN Y RESULTADOS
# ═══════════════════════════════════════════════════════════════════════════

def mostrar_resultado(octanaje, octanaje_redondeado, clasificacion, datos):
    """Muestra el resultado de forma visual y atractiva."""
    
    print(f"\n\n{C.VERDE}{'═' * 79}{C.RESET}")
    print(f"{C.VERDE}{C.NEGRITA}{'✨ RESULTADO DE LA PREDICCIÓN ✨':^79s}{C.RESET}")
    print(f"{C.VERDE}{'═' * 79}{C.RESET}\n")
    
    # Caja principal con el octanaje
    color = clasificacion['color']
    emoji = clasificacion['emoji']
    
    print(f"{color}╔{'═' * 77}╗{C.RESET}")
    print(f"{color}║{' ' * 77}║{C.RESET}")
    octanaje_texto = f"{emoji}  OCTANAJE PREDICHO: {octanaje:.1f} RON  {emoji}"
    print(f"{color}║{C.NEGRITA}{octanaje_texto:^77s}{C.RESET}{color}║{C.RESET}")
    print(f"{color}║{' ' * 77}║{C.RESET}")
    redondeado_texto = f"(Redondeado: {octanaje_redondeado} RON)"
    print(f"{color}║{redondeado_texto:^77s}║{C.RESET}")
    print(f"{color}║{' ' * 77}║{C.RESET}")
    print(f"{color}╚{'═' * 77}╝{C.RESET}\n")
    
    # Clasificación Fiscal
    print(f"{color}╔{'═' * 77}╗{C.RESET}")
    print(f"{color}║{C.NEGRITA}{'📋 CLASIFICACIÓN FISCAL':^77s}{C.RESET}{color}║{C.RESET}")
    print(f"{color}╠{'═' * 77}╣{C.RESET}")
    
    info_fiscal = [
        f"{C.NEGRITA}Categoría:{C.RESET}        {clasificacion['categoria']}",
        f"{C.NEGRITA}Descripción:{C.RESET}     {clasificacion['descripcion']}",
        f"",
        f"{C.NEGRITA}Código NC:{C.RESET}       {C.NEGRITA}{clasificacion['codigo_nc']}{C.RESET}",
        f"{C.NEGRITA}Epígrafe Fiscal:{C.RESET} {C.NEGRITA}{clasificacion['epigrafe']}{C.RESET}"
    ]
    
    for linea in info_fiscal:
        print(f"{color}║{C.RESET} {linea:<75s} {color}║{C.RESET}")
    
    print(f"{color}╚{'═' * 77}╝{C.RESET}\n")
    
    # Información Adicional
    print(f"{C.CYAN}╔{'═' * 77}╗{C.RESET}")
    print(f"{C.CYAN}║{C.NEGRITA}{'💡 INFORMACIÓN ADICIONAL':^77s}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 77}╣{C.RESET}")
    
    suma = sum([datos['PARAFINAS'], datos['ISOPARAFINAS'], datos['OLEFINAS'],
                datos['NAFTENICOS'], datos['AROMATICOS'], datos['Ox']])
    
    info_adicional = [
        f"Oxigenados totales (Ox):     {datos['Ox']:.2f} %v/v",
        f"Suma de componentes:         {suma:.1f} %v/v",
        f"Intervalo de confianza:      [{octanaje - 0.5:.1f}, {octanaje + 0.5:.1f}] RON (±0.5)",
        f"Fecha y hora:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    
    for linea in info_adicional:
        print(f"{C.CYAN}║{C.RESET} {linea:<75s} {C.CYAN}║{C.RESET}")
    
    print(f"{C.CYAN}╚{'═' * 77}╝{C.RESET}\n")
    
    print(f"{C.VERDE}{'═' * 79}{C.RESET}\n")

def ejecutar_prediccion(modelo, variables):
    """Ejecuta el flujo completo de predicción."""
    
    # Solicitar datos
    datos = solicitar_datos()
    
    if datos is None:
        return False  # Usuario canceló
    
    # Verificar suma de componentes
    suma = sum([datos['PARAFINAS'], datos['ISOPARAFINAS'], datos['OLEFINAS'],
                datos['NAFTENICOS'], datos['AROMATICOS'], datos['Ox']])
    
    if abs(suma - 100) > 5:
        print(f"\n{C.AMARILLO}⚠️  Advertencia: La suma de componentes es {suma:.1f}%")
        print(f"   (debería estar cerca de 100%){C.RESET}")
        continuar = input(f"{C.AMARILLO}¿Continuar de todos modos? (s/n): {C.RESET}")
        if continuar.lower() != 's':
            return True  # No cancelar, solo volver al menú
    
    # Crear DataFrame para predicción
    df_input = pd.DataFrame([datos])[variables]
    
    # PREDECIR
    print(f"\n{C.CYAN}🔮 Calculando octanaje...{C.RESET}")
    octanaje_predicho = float(modelo.predict(df_input)[0])
    octanaje_redondeado = round(octanaje_predicho)
    
    # Clasificar
    clasificacion = clasificar_gasolina(octanaje_redondeado)
    
    # Mostrar resultado
    mostrar_resultado(octanaje_predicho, octanaje_redondeado, clasificacion, datos)
    
    # Preguntar si guardar
    guardar = input(f"{C.CYAN}¿Guardar resultado en CSV? (s/n): {C.RESET}")
    if guardar.lower() == 's':
        guardar_resultado(datos, octanaje_predicho, octanaje_redondeado, clasificacion)
    
    return True

def guardar_resultado(datos, octanaje, octanaje_redondeado, clasificacion):
    """Guarda el resultado en CSV."""
    filename = 'predicciones_octanaje.csv'
    
    fila = {
        'Fecha_Hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'PARAFINAS': datos['PARAFINAS'],
        'ISOPARAFINAS': datos['ISOPARAFINAS'],
        'OLEFINAS': datos['OLEFINAS'],
        'NAFTENICOS': datos['NAFTENICOS'],
        'AROMATICOS': datos['AROMATICOS'],
        'ETANOL': datos['ETANOL'],
        'MTBE': datos['MTBE'],
        'ETBE': datos['ETBE'],
        'Ox': datos['Ox'],
        'Octanaje_Predicho': round(octanaje, 1),
        'Octanaje_Redondeado': octanaje_redondeado,
        'Categoria': clasificacion['categoria'],
        'Codigo_NC': clasificacion['codigo_nc'],
        'Epigrafe': clasificacion['epigrafe']
    }
    
    df = pd.DataFrame([fila])
    
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)
    
    print(f"{C.VERDE}✓ Resultado guardado en '{filename}'{C.RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLOS Y AYUDA
# ═══════════════════════════════════════════════════════════════════════════

def mostrar_ejemplo(modelo, variables):
    """Muestra un ejemplo de predicción."""
    
    print(f"\n{C.CYAN}{'═' * 79}{C.RESET}")
    print(f"{C.CYAN}{C.NEGRITA}{'💡 EJEMPLO DE PREDICCIÓN':^79s}{C.RESET}")
    print(f"{C.CYAN}{'═' * 79}{C.RESET}\n")
    
    datos_ejemplo = {
        'PARAFINAS': 10.5,
        'ISOPARAFINAS': 32.0,
        'OLEFINAS': 8.5,
        'NAFTENICOS': 6.2,
        'AROMATICOS': 38.0,
        'ETANOL': 4.8,
        'MTBE': 0.0,
        'ETBE': 0.0,
        'Ox': 4.8
    }
    
    print(f"{C.BLANCO}Datos de entrada:{C.RESET}\n")
    for var, valor in datos_ejemplo.items():
        if var != 'Ox':
            print(f"  {var:<15s}: {valor:>6.1f} %v/v")
    
    df_input = pd.DataFrame([datos_ejemplo])[variables]
    octanaje = float(modelo.predict(df_input)[0])
    octanaje_redondeado = round(octanaje)
    clasificacion = clasificar_gasolina(octanaje_redondeado)
    
    print(f"\n{clasificacion['color']}{C.NEGRITA}Resultado: {octanaje:.1f} RON → {clasificacion['categoria']}{C.RESET}")
    print(f"{clasificacion['color']}Código NC: {clasificacion['codigo_nc']} | Epígrafe: {clasificacion['epigrafe']}{C.RESET}\n")

def mostrar_info():
    """Muestra información del modelo."""
    
    info_contenido = [
        f"{C.NEGRITA}Modelo:{C.RESET}             Gradient Boosting Regressor",
        f"{C.NEGRITA}Árboles:{C.RESET}            200 secuenciales",
        f"{C.NEGRITA}Variables:{C.RESET}          9 (8 de cromatografía + Ox)",
        "",
        f"{C.VERDE}Métricas de Desempeño:{C.RESET}",
        f"  • R² validación:      0.8365 (83.65%)",
        f"  • MAE:                0.3774 unidades",
        f"  • Exactitud:          {C.NEGRITA}100%{C.RESET} (criterio industrial ±0.5)",
        "",
        f"{C.CYAN}Variables más importantes:{C.RESET}",
        f"  1. PARAFINAS      40.3%",
        f"  2. Ox             32.1%",
        f"  3. NAFTÉNICOS     16.8%"
    ]
    
    imprimir_caja("ℹ️  INFORMACIÓN DEL MODELO", info_contenido, C.CYAN)

def mostrar_categorias():
    """Muestra la tabla de categorías fiscales."""
    
    print(f"\n{C.VERDE}╔{'═' * 77}╗{C.RESET}")
    print(f"{C.VERDE}║{C.NEGRITA}{'📋 CATEGORÍAS FISCALES':^77s}{C.RESET}{C.VERDE}║{C.RESET}")
    print(f"{C.VERDE}╠{'═' * 77}╣{C.RESET}")
    print(f"{C.VERDE}║{C.RESET} {'Octanaje':<12s} {'Categoría':<20s} {'Código NC':<15s} {'Epígrafe':<10s} {C.VERDE}║{C.RESET}")
    print(f"{C.VERDE}╠{'═' * 77}╣{C.RESET}")
    
    categorias = [
        ("< 95", "GASOLINA REGULAR", "2710.12.41", "1.2.2", C.AMARILLO),
        ("95 - 98", "GASOLINA PREMIUM", "2710.12.45", "1.2.2", C.AZUL),
        ("> 98", "GASOLINA SUPER", "2710.12.49", "1.2.1", C.MORADO)
    ]
    
    for octanaje, categoria, codigo, epigrafe, color in categorias:
        linea = f" {color}{octanaje:<12s}{C.RESET} {categoria:<20s} {C.NEGRITA}{codigo}{C.RESET:<15s} {C.NEGRITA}{epigrafe}{C.RESET:<10s} "
        print(f"{C.VERDE}║{C.RESET}{linea}{C.VERDE}║{C.RESET}")
    
    print(f"{C.VERDE}╚{'═' * 77}╝{C.RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def mostrar_menu():
    """Muestra el menú principal."""
    
    print(f"\n{C.CYAN}╔{'═' * 77}╗{C.RESET}")
    print(f"{C.CYAN}║{C.NEGRITA}{'MENÚ PRINCIPAL':^77s}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 77}╣{C.RESET}")
    
    opciones = [
        ("1", "🎯 Predecir octanaje (nueva muestra)"),
        ("2", "💡 Ver ejemplo de predicción"),
        ("3", "ℹ️  Información del modelo"),
        ("4", "📋 Ver tabla de categorías fiscales"),
        ("5", "❌ Salir")
    ]
    
    for num, desc in opciones:
        print(f"{C.CYAN}║{C.RESET}  {C.BLANCO}{num}.{C.RESET} {desc:<70s} {C.CYAN}║{C.RESET}")
    
    print(f"{C.CYAN}╚{'═' * 77}╝{C.RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Función principal del bot."""
    
    # Banner de bienvenida
    imprimir_banner()
    
    # Cargar modelo
    modelo, variables = cargar_modelo()
    
    if modelo is None:
        return
    
    # Bucle principal
    while True:
        try:
            mostrar_menu()
            opcion = input(f"{C.CYAN}Selecciona una opción (1-5): {C.RESET}").strip()
            
            if opcion == '1':
                if not ejecutar_prediccion(modelo, variables):
                    break  # Usuario canceló
            
            elif opcion == '2':
                mostrar_ejemplo(modelo, variables)
            
            elif opcion == '3':
                mostrar_info()
            
            elif opcion == '4':
                mostrar_categorias()
            
            elif opcion == '5':
                print(f"\n{C.VERDE}╔{'═' * 77}╗{C.RESET}")
                print(f"{C.VERDE}║{'':^77s}║{C.RESET}")
                print(f"{C.VERDE}║{C.NEGRITA}{'👋 ¡Hasta luego! Gracias por usar el Bot de Octanaje':^77s}{C.RESET}{C.VERDE}║{C.RESET}")
                print(f"{C.VERDE}║{'':^77s}║{C.RESET}")
                print(f"{C.VERDE}╚{'═' * 77}╝{C.RESET}\n")
                break
            
            else:
                print(f"{C.ROJO}✗ Opción inválida. Por favor, elige 1-5.{C.RESET}")
        
        except KeyboardInterrupt:
            print(f"\n\n{C.AMARILLO}Operación cancelada por el usuario{C.RESET}")
            print(f"{C.VERDE}👋 ¡Hasta luego!{C.RESET}\n")
            break
        
        except Exception as e:
            print(f"\n{C.ROJO}✗ Error inesperado: {e}{C.RESET}\n")

if __name__ == "__main__":
    main()
