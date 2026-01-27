"""
API REST para predicción de octanaje
Backend Flask que sirve el modelo de machine learning
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pickle
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el frontend

# Cargar modelo al iniciar
print("Cargando modelo...")
try:
    with open('modelo_final_gb.pkl', 'rb') as f:
        datos_modelo = pickle.load(f)
    modelo = datos_modelo['modelo']
    variables = datos_modelo['variables']
    print("✓ Modelo cargado exitosamente")
except FileNotFoundError:
    print("❌ ERROR: No se encuentra modelo_final_gb.pkl")
    modelo = None

# Rangos válidos para validación
RANGOS_VALIDOS = {
    'PARAFINAS': (5.52, 16.21),
    'ISOPARAFINAS': (25.77, 43.96),
    'NAFTENICOS': (3.77, 12.00),
    'AROMATICOS': (23.44, 37.10),
    'Ox': (3.38, 16.22),
    'ETANOL': (0.00, 4.89),
    'MTBE': (0.00, 13.19),
    'ETBE': (0.00, 14.02)
}

@app.route('/')
def home():
    """Página de inicio"""
    return """
    <h1>API de Predicción de Octanaje</h1>
    <p>Modelo Gradient Boosting - 90 datos de entrenamiento</p>
    <p>Endpoints disponibles:</p>
    <ul>
        <li>POST /predecir - Predecir octanaje</li>
        <li>GET /info - Información del modelo</li>
        <li>GET /rangos - Rangos válidos de variables</li>
    </ul>
    """

@app.route('/predecir', methods=['POST'])
def predecir():
    """Endpoint para predecir octanaje"""
    
    if modelo is None:
        return jsonify({
            'error': 'Modelo no disponible'
        }), 500
    
    try:
        # Obtener datos del request
        datos = request.json
        
        # Validar que estén todas las variables
        for var in variables:
            if var not in datos:
                return jsonify({
                    'error': f'Falta la variable: {var}'
                }), 400
        
        # Crear DataFrame
        df = pd.DataFrame([datos])
        
        # Predecir
        octanaje = modelo.predict(df)[0]
        
        # Validar rangos
        advertencias = []
        for var, valor in datos.items():
            if var in RANGOS_VALIDOS:
                min_val, max_val = RANGOS_VALIDOS[var]
                if valor < min_val or valor > max_val:
                    advertencias.append({
                        'variable': var,
                        'valor': valor,
                        'rango_min': min_val,
                        'rango_max': max_val,
                        'mensaje': f'{var} fuera del rango de entrenamiento'
                    })
        
        # Respuesta
        respuesta = {
            'octanaje': round(octanaje, 2),
            'octanaje_exacto': float(octanaje),
            'intervalo_confianza': {
                'min': round(octanaje - 0.06, 2),
                'max': round(octanaje + 0.06, 2)
            },
            'advertencias': advertencias,
            'datos_entrada': datos,
            'dentro_rango': len(advertencias) == 0
        }
        
        return jsonify(respuesta)
        
    except Exception as e:
        return jsonify({
            'error': f'Error en la predicción: {str(e)}'
        }), 500

@app.route('/info', methods=['GET'])
def info():
    """Información del modelo"""
    if modelo is None:
        return jsonify({'error': 'Modelo no disponible'}), 500
    
    return jsonify({
        'modelo': 'Gradient Boosting Regressor',
        'n_estimators': 200,
        'learning_rate': 0.05,
        'max_depth': 4,
        'variables_requeridas': variables,
        'r2_entrenamiento': 0.9995,
        'r2_cv': 0.798,
        'mae': 0.023,
        'rmse': 0.028,
        'n_datos_entrenamiento': 90
    })

@app.route('/rangos', methods=['GET'])
def rangos():
    """Rangos válidos de variables"""
    return jsonify(RANGOS_VALIDOS)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SERVIDOR API OCTANAJE")
    print("="*80)
    print("Iniciando en http://localhost:5000")
    print("Para usar desde otro equipo, cambia host='0.0.0.0'")
    print("="*80 + "\n")
    
    # Iniciar servidor
    app.run(debug=True, host='127.0.0.1', port=5000)
