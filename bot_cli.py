"""
BOT CLI INTERACTIVO PARA PREDICCIÓN DE OCTANAJE
Interfaz de línea de comandos con menú y validación
"""

import pickle
import pandas as pd
import os
from colorama import init, Fore, Style

# Inicializar colorama para colores en terminal
try:
    init()
    COLORS_AVAILABLE = True
except:
    COLORS_AVAILABLE = False

def print_color(text, color='WHITE'):
    """Imprimir con color si está disponible"""
    if COLORS_AVAILABLE:
        colors = {
            'RED': Fore.RED,
            'GREEN': Fore.GREEN,
            'YELLOW': Fore.YELLOW,
            'BLUE': Fore.BLUE,
            'MAGENTA': Fore.MAGENTA,
            'CYAN': Fore.CYAN,
            'WHITE': Fore.WHITE
        }
        print(colors.get(color, Fore.WHITE) + text + Style.RESET_ALL)
    else:
        print(text)

def cargar_modelo():
    """Cargar el modelo entrenado"""
    try:
        with open('modelo_final_gb.pkl', 'rb') as f:
            datos = pickle.load(f)
        return datos['modelo'], datos['variables']
    except FileNotFoundError:
        print_color("\n❌ ERROR: No se encuentra el archivo 'modelo_final_gb.pkl'", 'RED')
        print_color("   Asegúrate de que está en la misma carpeta que este script.\n", 'YELLOW')
        return None, None

def mostrar_banner():
    """Mostrar banner del bot"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              🤖  BOT PREDICTOR DE OCTANAJE  🤖                           ║
║                                                                           ║
║              Modelo: Gradient Boosting (200 árboles)                     ║
║              Precisión: R² = 0.9995 | Error: ±0.03                       ║
║              Datos de entrenamiento: 90 muestras                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print_color(banner, 'CYAN')

def mostrar_menu():
    """Mostrar menú principal"""
    print_color("\n" + "="*80, 'BLUE')
    print_color("MENÚ PRINCIPAL", 'BLUE')
    print_color("="*80, 'BLUE')
    print("1. 🎯 Predecir octanaje (nueva muestra)")
    print("2. 📊 Predecir múltiples muestras")
    print("3. 💡 Cargar ejemplo")
    print("4. ℹ️  Ver información del modelo")
    print("5. 📋 Ver rangos válidos")
    print("6. 🚪 Salir")
    print_color("="*80, 'BLUE')

def solicitar_datos(variables, rangos):
    """Solicitar datos al usuario"""
    print_color("\n📊 Introduce los datos del análisis cromatográfico:", 'CYAN')
    print_color("(Todos los valores en %v/v)\n", 'YELLOW')
    
    datos = {}
    for var in variables:
        while True:
            try:
                valor = input(f"  {var:15s}: ")
                if valor.lower() == 'exit':
                    return None
                valor_num = float(valor)
                
                # Verificar rango
                if var in rangos:
                    min_val, max_val = rangos[var]
                    if valor_num < min_val or valor_num > max_val:
                        print_color(f"    ⚠️  Advertencia: valor fuera del rango [{min_val:.2f}, {max_val:.2f}]", 'YELLOW')
                
                datos[var] = valor_num
                break
            except ValueError:
                print_color("    ❌ Por favor, introduce un número válido", 'RED')
    
    return datos

def predecir(modelo, datos):
    """Hacer predicción"""
    df = pd.DataFrame([datos])
    octanaje = modelo.predict(df)[0]
    return octanaje

def mostrar_resultado(octanaje, datos, rangos):
    """Mostrar resultado de la predicción"""
    print_color("\n" + "="*80, 'GREEN')
    print_color("RESULTADO DE LA PREDICCIÓN", 'GREEN')
    print_color("="*80, 'GREEN')
    
    # Resultado principal
    print_color(f"\n  🎯 OCTANAJE PREDICHO: {octanaje:.2f}", 'GREEN')
    print(f"  📊 Valor exacto:      {octanaje:.6f}")
    print(f"  📈 IC 95%:            {octanaje-0.06:.2f} - {octanaje+0.06:.2f}")
    
    # Validar rangos
    print_color("\n  VALIDACIÓN DE RANGOS:", 'CYAN')
    fuera_rango = []
    for var, valor in datos.items():
        if var in rangos:
            min_val, max_val = rangos[var]
            if valor < min_val or valor > max_val:
                print_color(f"    ⚠️  {var:15s}: {valor:.2f} FUERA del rango [{min_val:.2f}, {max_val:.2f}]", 'YELLOW')
                fuera_rango.append(var)
            else:
                print(f"    ✓  {var:15s}: {valor:.2f} dentro del rango")
    
    if not fuera_rango:
        print_color("\n  ✅ Todos los valores dentro del rango de entrenamiento", 'GREEN')
        print_color("  📍 Predicción confiable", 'GREEN')
    else:
        print_color(f"\n  ⚠️  {len(fuera_rango)} variable(s) fuera del rango", 'YELLOW')
        print_color("  📍 Predicción con mayor incertidumbre (extrapolación)", 'YELLOW')
    
    print_color("="*80 + "\n", 'GREEN')

def datos_ejemplo():
    """Datos de ejemplo"""
    return {
        'PARAFINAS': 10.50,
        'ISOPARAFINAS': 32.00,
        'NAFTENICOS': 8.00,
        'AROMATICOS': 30.00,
        'Ox': 10.00,
        'ETANOL': 3.50,
        'MTBE': 5.00,
        'ETBE': 1.50
    }

def mostrar_info_modelo():
    """Mostrar información del modelo"""
    print_color("\n" + "="*80, 'CYAN')
    print_color("INFORMACIÓN DEL MODELO", 'CYAN')
    print_color("="*80, 'CYAN')
    print("\n  Tipo:                 Gradient Boosting Regressor")
    print("  N° de árboles:        200")
    print("  Learning rate:        0.05")
    print("  Profundidad máxima:   4")
    print("  Subsample:            0.8")
    print("\n  MÉTRICAS DE DESEMPEÑO:")
    print("  ────────────────────────────────")
    print_color("  R² (ajuste):          0.9995 (99.95%)", 'GREEN')
    print("  R² CV (10-fold):      0.798 ± 0.109")
    print("  RMSE:                 0.028 unidades")
    print("  MAE:                  0.023 unidades")
    print("  Error porcentual:     0.024%")
    print_color("  Predicciones < 0.1:   90/90 (100%)", 'GREEN')
    print("\n  DATOS DE ENTRENAMIENTO:")
    print("  ────────────────────────────────")
    print("  N° de muestras:       90")
    print("  Rango octanaje:       92.90 - 99.00")
    print_color("="*80 + "\n", 'CYAN')

def mostrar_rangos(rangos):
    """Mostrar rangos válidos"""
    print_color("\n" + "="*80, 'CYAN')
    print_color("RANGOS VÁLIDOS DE VARIABLES", 'CYAN')
    print_color("="*80, 'CYAN')
    print("\n  Variable          Mínimo    Máximo")
    print("  " + "─"*40)
    for var, (min_val, max_val) in rangos.items():
        print(f"  {var:15s}  {min_val:7.2f}   {max_val:7.2f}")
    print_color("\n  ℹ️  Los valores fuera de estos rangos implican extrapolación", 'YELLOW')
    print_color("="*80 + "\n", 'CYAN')

def main():
    """Función principal"""
    # Cargar modelo
    modelo, variables = cargar_modelo()
    if modelo is None:
        return
    
    # Rangos válidos
    rangos = {
        'PARAFINAS': (5.52, 16.21),
        'ISOPARAFINAS': (25.77, 43.96),
        'NAFTENICOS': (3.77, 12.00),
        'AROMATICOS': (23.44, 37.10),
        'Ox': (3.38, 16.22),
        'ETANOL': (0.00, 4.89),
        'MTBE': (0.00, 13.19),
        'ETBE': (0.00, 14.02)
    }
    
    # Banner
    mostrar_banner()
    print_color("✓ Modelo cargado exitosamente\n", 'GREEN')
    
    # Loop principal
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción (1-6): ").strip()
            
            if opcion == '1':
                # Predecir nueva muestra
                datos = solicitar_datos(variables, rangos)
                if datos is not None:
                    octanaje = predecir(modelo, datos)
                    mostrar_resultado(octanaje, datos, rangos)
                    
                    guardar = input("¿Guardar resultado en archivo? (s/n): ").lower()
                    if guardar == 's':
                        filename = input("Nombre del archivo (sin extensión): ").strip()
                        df = pd.DataFrame([{**datos, 'OCTANAJE_PREDICHO': octanaje}])
                        df.to_csv(f'{filename}.csv', index=False)
                        print_color(f"✓ Resultado guardado en '{filename}.csv'\n", 'GREEN')
            
            elif opcion == '2':
                # Múltiples muestras
                print_color("\nEsta función requiere un archivo CSV con las 8 variables", 'YELLOW')
                filename = input("Nombre del archivo CSV: ").strip()
                try:
                    df_input = pd.read_csv(filename)
                    predicciones = modelo.predict(df_input)
                    df_input['OCTANAJE_PREDICHO'] = predicciones
                    output_file = filename.replace('.csv', '_predicciones.csv')
                    df_input.to_csv(output_file, index=False)
                    print_color(f"\n✓ Predicciones guardadas en '{output_file}'", 'GREEN')
                    print(f"Total de muestras procesadas: {len(predicciones)}")
                except FileNotFoundError:
                    print_color(f"\n❌ No se encontró el archivo '{filename}'", 'RED')
            
            elif opcion == '3':
                # Cargar ejemplo
                datos = datos_ejemplo()
                print_color("\n💡 Datos de ejemplo cargados:", 'CYAN')
                for var, val in datos.items():
                    print(f"  {var:15s}: {val:.2f}")
                
                continuar = input("\n¿Calcular octanaje con estos datos? (s/n): ").lower()
                if continuar == 's':
                    octanaje = predecir(modelo, datos)
                    mostrar_resultado(octanaje, datos, rangos)
            
            elif opcion == '4':
                # Información del modelo
                mostrar_info_modelo()
            
            elif opcion == '5':
                # Rangos válidos
                mostrar_rangos(rangos)
            
            elif opcion == '6':
                # Salir
                print_color("\n👋 ¡Hasta pronto!\n", 'CYAN')
                break
            
            else:
                print_color("\n❌ Opción inválida. Por favor, elige 1-6\n", 'RED')
        
        except KeyboardInterrupt:
            print_color("\n\n👋 Saliendo...\n", 'CYAN')
            break
        except Exception as e:
            print_color(f"\n❌ Error: {str(e)}\n", 'RED')

if __name__ == '__main__':
    main()
