"""
╔═══════════════════════════════════════════════════════════════════════════╗
║              🤖 PREDICTOR DE OCTANAJE - STREAMLIT APP 🤖                  ║
║                    Con Clasificación Fiscal Automática                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

Aplicación Streamlit para predicción de octanaje en gasolina
Versión: 2.0 - CORREGIDA
"""

import streamlit as st
import pickle
import pandas as pd
from datetime import datetime
import os

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="🤖 Predictor de Octanaje",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Sistema de predicción de octanaje con ML | Precisión: 100% (±0.5)"
    }
)

# Inicializar session_state
if 'resultado' not in st.session_state:
    st.session_state.resultado = None

# ═══════════════════════════════════════════════════════════════════════════
# CSS PERSONALIZADO
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Header principal */
    .main-header {
        font-size: 3.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0;
        padding: 1rem 0;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        padding: 0.5rem;
    }
    
    /* Cajas de resultado según categoría */
    .result-box {
        padding: 2.5rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .result-regular {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        color: #2d3436;
    }
    
    .result-premium {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
    }
    
    .result-super {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
    }
    
    .octanaje-value {
        font-size: 4rem;
        font-weight: bold;
        margin: 1rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .emoji-large {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Tabla de categorías en sidebar */
    .categoria-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .categoria-regular {
        background: #fff3cd;
        border-color: #ffc107;
    }
    
    .categoria-premium {
        background: #d1ecf1;
        border-color: #0dcaf0;
    }
    
    .categoria-super {
        background: #e7d6f5;
        border-color: #a855f7;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 10px;
        height: 3rem;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Inputs */
    .stNumberInput > div > div > input {
        border-radius: 8px;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CLASIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def clasificar_gasolina(octanaje_real):
    """
    Clasifica la gasolina según normativa fiscal española.
    
    Args:
        octanaje_real: Octanaje predicho con decimales (valor real sin redondear)
        
    Returns:
        dict con información de clasificación y advertencias
    """
    # IMPORTANTE: Clasificar con el valor REAL, no con el redondeado
    
    # Detectar si está en zona crítica (límite ± tolerancia 0.5)
    advertencia = None
    limite_critico = None
    
    # Límite crítico en 95.0 (rango de advertencia: 94.5 - 95.5)
    if 94.5 <= octanaje_real <= 95.5:
        limite_critico = 95.0
        if octanaje_real < 95:
            advertencia = f"⚠️ ADVERTENCIA: Octanaje {octanaje_real:.1f} está muy cerca del límite inferior (95.0). Dentro de tolerancia industrial (±0.5), podría reclasificarse."
        else:
            advertencia = f"⚠️ ADVERTENCIA: Octanaje {octanaje_real:.1f} está muy cerca del límite superior (95.0). Dentro de tolerancia industrial (±0.5), podría reclasificarse."
    
    # Límite crítico en 98.0 (rango de advertencia: 97.5 - 98.5)
    elif 97.5 <= octanaje_real <= 98.5:
        limite_critico = 98.0
        if octanaje_real <= 98:
            advertencia = f"⚠️ ADVERTENCIA: Octanaje {octanaje_real:.1f} está muy cerca del límite superior (98.0). Dentro de tolerancia industrial (±0.5), podría reclasificarse."
        else:
            advertencia = f"⚠️ ADVERTENCIA: Octanaje {octanaje_real:.1f} está muy cerca del límite inferior (98.0). Dentro de tolerancia industrial (±0.5), podría reclasificarse."
    
    # Clasificación
    if octanaje_real < 95:
        return {
            'categoria': 'GASOLINA <95 OCTANOS',
            'codigo_nc': '2710.12.41',
            'epigrafe': '1.2.2',
            'descripcion': 'Inferior a 95 octanos',
            'emoji': '⚡',
            'clase': 'result-regular',
            'imagen': '94.png',
            'advertencia': advertencia,
            'limite_critico': limite_critico
        }
    elif octanaje_real <= 98:
        return {
            'categoria': 'GASOLINA 95 OCTANOS',
            'codigo_nc': '2710.12.45',
            'epigrafe': '1.2.2',
            'descripcion': '95 a 98 octanos',
            'emoji': '🚗',
            'clase': 'result-premium',
            'imagen': '95.png',
            'advertencia': advertencia,
            'limite_critico': limite_critico
        }
    else:  # > 98
        return {
            'categoria': 'GASOLINA 98 OCTANOS',
            'codigo_nc': '2710.12.49',
            'epigrafe': '1.2.1',
            'descripcion': 'Superior a 98 octanos',
            'emoji': '🏎️',
            'clase': 'result-super',
            'imagen': '98.png',
            'advertencia': advertencia,
            'limite_critico': limite_critico
        }

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def cargar_modelo():
    """Carga el modelo de predicción (con caché)."""
    try:
        # Buscar el modelo en varias ubicaciones
        rutas_posibles = [
            'modelo_final_gb.pkl',
            './modelo_final_gb.pkl',
            'models/modelo_final_gb.pkl'
        ]
        
        modelo_path = None
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                modelo_path = ruta
                break
        
        if modelo_path is None:
            return None, None, "No se encontró el archivo 'modelo_final_gb.pkl'"
        
        with open(modelo_path, 'rb') as f:
            modelo_info = pickle.load(f)
            return modelo_info['modelo'], modelo_info['variables'], None
    
    except Exception as e:
        return None, None, f"Error al cargar: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════════
# HEADER DE LA APLICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

# Banner superior
try:
    st.image('banner.png', use_column_width=True)
except:
    # Si no encuentra la imagen, muestra el título normal
    st.markdown('<p class="main-header">🤖 Predictor de Octanaje ⛽</p>', unsafe_allow_html=True)

st.markdown('<p class="subtitle">Sistema de predicción con clasificación fiscal automática | Precisión: 100% (±0.5)</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CARGAR MODELO
# ═══════════════════════════════════════════════════════════════════════════

modelo, variables, error = cargar_modelo()

if modelo is None:
    st.error(f"❌ **Error al cargar el modelo**")
    st.error(error)
    st.info("💡 Asegúrate de que el archivo 'modelo_final_gb.pkl' está en el repositorio.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR CON INFORMACIÓN
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ℹ️ Información")
    
    st.markdown("### 📋 Categorías Fiscales")
    
    # Categoría 1
    st.markdown("""
    <div class="categoria-box categoria-regular">
        <strong>⚡ GASOLINA <95 OCTANOS</strong><br>
        <small>< 95 octanos</small><br>
        <strong>Código NC:</strong> 2710.12.41<br>
        <strong>Epígrafe:</strong> 1.2.2
    </div>
    """, unsafe_allow_html=True)
    
    # Categoría 2
    st.markdown("""
    <div class="categoria-box categoria-premium">
        <strong>🚗 GASOLINA 95 OCTANOS</strong><br>
        <small>95 - 98 octanos</small><br>
        <strong>Código NC:</strong> 2710.12.45<br>
        <strong>Epígrafe:</strong> 1.2.2
    </div>
    """, unsafe_allow_html=True)
    
    # Categoría 3
    st.markdown("""
    <div class="categoria-box categoria-super">
        <strong>🏎️ GASOLINA 98 OCTANOS</strong><br>
        <small>> 98 octanos</small><br>
        <strong>Código NC:</strong> 2710.12.49<br>
        <strong>Epígrafe:</strong> 1.2.1
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 🎯 Especificaciones del Modelo")
    st.markdown("""
    - **Algoritmo:** Gradient Boosting
    - **Árboles:** 200 secuenciales
    - **R² validación:** 0.8365
    - **MAE:** 0.3774
    - **Precisión:** 100% (±0.5)
    """)
    
    st.divider()
    
    # Botón de ejemplo
    if st.button("💡 Cargar Datos de Ejemplo", use_container_width=True):
        st.session_state.cargar_ejemplo = True
        st.session_state.resultado = None
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["🎯 Predicción", "📊 Modelo", "📖 Guía de Uso"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: PREDICCIÓN
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 📊 Análisis Cromatográfico")
    st.markdown("Introduce los valores obtenidos del análisis cromatográfico:")
    
    # Determinar valores iniciales (ejemplo o cero)
    if 'cargar_ejemplo' in st.session_state and st.session_state.cargar_ejemplo:
        valores = {
            'PARAFINAS': 10.5,
            'ISOPARAFINAS': 32.0,
            'OLEFINAS': 8.5,
            'NAFTENICOS': 6.2,
            'AROMATICOS': 38.0,
            'ETANOL': 4.8,
            'MTBE': 0.0,
            'ETBE': 0.0
        }
        st.session_state.cargar_ejemplo = False
        st.success("✅ Datos de ejemplo cargados")
    else:
        valores = {key: 0.0 for key in ['PARAFINAS', 'ISOPARAFINAS', 'OLEFINAS', 
                                         'NAFTENICOS', 'AROMATICOS', 'ETANOL', 'MTBE', 'ETBE']}
    
    # Formulario en 2 columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🧪 Componentes Principales")
        parafinas = st.number_input(
            "**PARAFINAS** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['PARAFINAS'], 
            step=0.1,
            help="Rango típico: 5.5 - 16.2",
            key="parafinas"
        )
        
        isoparafinas = st.number_input(
            "**ISOPARAFINAS** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['ISOPARAFINAS'], 
            step=0.1,
            help="Rango típico: 22.5 - 43.9",
            key="isoparafinas"
        )
        
        olefinas = st.number_input(
            "**OLEFINAS** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['OLEFINAS'], 
            step=0.1,
            help="Rango típico: 2.3 - 13.8",
            key="olefinas"
        )
        
        naftenicos = st.number_input(
            "**NAFTÉNICOS** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['NAFTENICOS'], 
            step=0.1,
            help="Rango típico: 2.0 - 14.5",
            key="naftenicos"
        )
    
    with col2:
        st.markdown("#### 🧪 Aromáticos y Oxigenados")
        aromaticos = st.number_input(
            "**AROMÁTICOS** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['AROMATICOS'], 
            step=0.1,
            help="Rango típico: 26.5 - 48.9",
            key="aromaticos"
        )
        
        etanol = st.number_input(
            "**ETANOL** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['ETANOL'], 
            step=0.1,
            help="Rango típico: 0.0 - 4.9",
            key="etanol"
        )
        
        mtbe = st.number_input(
            "**MTBE** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['MTBE'], 
            step=0.1,
            help="Rango típico: 0.0 - 14.3",
            key="mtbe"
        )
        
        etbe = st.number_input(
            "**ETBE** (%v/v)", 
            min_value=0.0, 
            max_value=100.0, 
            value=valores['ETBE'], 
            step=0.1,
            help="Rango típico: 0.0 - 7.9",
            key="etbe"
        )
    
    # Calcular Ox y suma total
    ox = etanol + mtbe + etbe
    suma_total = parafinas + isoparafinas + olefinas + naftenicos + aromaticos + ox
    
    # Mostrar resumen antes de calcular
    st.markdown("### 📈 Resumen de Componentes")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Oxigenados totales (Ox)", f"{ox:.2f}%")
    with col2:
        st.metric("Suma de componentes", f"{suma_total:.1f}%")
    with col3:
        if abs(suma_total - 100) > 5:
            st.metric("Desviación de 100%", f"{suma_total - 100:+.1f}%", delta_color="inverse")
        else:
            st.metric("✅ Suma válida", "OK", delta_color="normal")
    
    # Advertencia si la suma se desvía mucho
    if abs(suma_total - 100) > 5:
        st.warning(f"⚠️ **Advertencia:** La suma de componentes es {suma_total:.1f}% (debería estar cerca de 100%)")
    
    st.markdown("---")
    
    # Botones de calcular y limpiar
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        calcular = st.button("🎯 CALCULAR OCTANAJE", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button("🔄 LIMPIAR RESULTADOS", use_container_width=True):
            st.session_state.resultado = None
            st.rerun()
    
    # PROCESAR CÁLCULO
    if calcular:
        # Preparar datos para predicción
        datos_prediccion = {
            'PARAFINAS': parafinas,
            'ISOPARAFINAS': isoparafinas,
            'OLEFINAS': olefinas,
            'NAFTENICOS': naftenicos,
            'AROMATICOS': aromaticos,
            'ETANOL': etanol,
            'MTBE': mtbe,
            'ETBE': etbe,
            'Ox': ox
        }
        
        # Crear DataFrame
        df_input = pd.DataFrame([datos_prediccion])[variables]
        
        # PREDECIR
        with st.spinner("🔮 Calculando octanaje..."):
            octanaje_predicho = float(modelo.predict(df_input)[0])
            octanaje_redondeado = round(octanaje_predicho)
        
        # Clasificar usando el valor REAL (con decimales), no el redondeado
        clasificacion = clasificar_gasolina(octanaje_predicho)
        
        # Guardar en session_state
        st.session_state.resultado = {
            'octanaje': octanaje_predicho,
            'octanaje_redondeado': octanaje_redondeado,
            'clasificacion': clasificacion,
            'datos': datos_prediccion,
            'suma_total': suma_total
        }
    
    # MOSTRAR RESULTADO si existe
    if st.session_state.resultado is not None:
        resultado = st.session_state.resultado
        octanaje_predicho = resultado['octanaje']
        octanaje_redondeado = resultado['octanaje_redondeado']
        clasificacion = resultado['clasificacion']
        datos_prediccion = resultado['datos']
        suma_total = resultado['suma_total']
        
        st.markdown("---")
        st.markdown("## ✨ RESULTADO DE LA PREDICCIÓN")
        
        # Mostrar imagen del coche correspondiente (MÁS PEQUEÑA)
        try:
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(clasificacion['imagen'], width=400)  # ← IMAGEN MÁS PEQUEÑA
        except:
            pass  # Si no encuentra la imagen, continúa sin ella
        
        # Caja de resultado con estilo según categoría
        resultado_html = f"""
        <div class="result-box {clasificacion['clase']}">
            <div class="emoji-large">{clasificacion['emoji']}</div>
            <div class="octanaje-value">{octanaje_predicho:.1f} RON</div>
            <div style="font-size: 1.3rem; margin-bottom: 1rem; opacity: 0.9;">
                (Redondeado: {octanaje_redondeado} RON)
            </div>
            <div style="font-size: 1.1rem; opacity: 0.85;">
                Intervalo de confianza: [{octanaje_predicho - 0.5:.1f}, {octanaje_predicho + 0.5:.1f}] RON
            </div>
        </div>
        """
        st.markdown(resultado_html, unsafe_allow_html=True)
        
        # Clasificación Fiscal
        st.markdown("### 📋 Clasificación Fiscal")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Categoría", clasificacion['categoria'])
        
        with col2:
            st.metric("Código NC", clasificacion['codigo_nc'])
        
        with col3:
            st.metric("Epígrafe Fiscal", clasificacion['epigrafe'])
        
        st.info(f"📝 **Descripción:** {clasificacion['descripcion']}")
        
        # Mostrar advertencia si está en límite crítico
        if clasificacion['advertencia']:
            st.warning(clasificacion['advertencia'])
        
        # Información adicional
        st.markdown("### 💡 Información Adicional")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Componentes Principales", f"{parafinas + isoparafinas + aromaticos:.1f}%")
        
        with col2:
            st.metric("Oxigenados Totales", f"{ox:.2f}%")
        
        with col3:
            st.metric("Suma Total", f"{suma_total:.1f}%")
        
        # Timestamp
        st.caption(f"🕐 Predicción realizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Opción de descargar datos
        st.markdown("### 💾 Exportar Resultado")
        
        datos_exportar = {
            'Fecha_Hora': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'PARAFINAS': [parafinas],
            'ISOPARAFINAS': [isoparafinas],
            'OLEFINAS': [olefinas],
            'NAFTENICOS': [naftenicos],
            'AROMATICOS': [aromaticos],
            'ETANOL': [etanol],
            'MTBE': [mtbe],
            'ETBE': [etbe],
            'Ox': [ox],
            'Octanaje_Predicho': [round(octanaje_predicho, 1)],
            'Octanaje_Redondeado': [octanaje_redondeado],
            'Categoria': [clasificacion['categoria']],
            'Codigo_NC': [clasificacion['codigo_nc']],
            'Epigrafe': [clasificacion['epigrafe']]
        }
        
        df_exportar = pd.DataFrame(datos_exportar)
        
        csv = df_exportar.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Descargar resultado en CSV",
            data=csv,
            file_name=f'prediccion_octanaje_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            use_container_width=True
        )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: INFORMACIÓN DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## 📊 Información del Modelo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Especificaciones Técnicas")
        st.markdown("""
        - **Algoritmo:** Gradient Boosting Regressor
        - **Número de árboles:** 200 secuenciales
        - **Profundidad máxima:** 4 niveles
        - **Learning rate:** 0.05
        - **Subsample:** 0.8 (80% de datos)
        - **Variables de entrada:** 9 (8 medidas + Ox calculado)
        """)
        
        st.markdown("### 📈 Datos de Entrenamiento")
        st.markdown("""
        - **Muestras de entrenamiento:** 90
        - **Muestras de validación:** 77 (independientes)
        - **Rango de octanaje:** 92.9 - 99.0 RON
        """)
    
    with col2:
        st.markdown("### 📊 Métricas de Desempeño")
        
        metricas_col1, metricas_col2 = st.columns(2)
        
        with metricas_col1:
            st.metric("R² Entrenamiento", "99.96%")
            st.metric("R² Validación", "83.65%")
        
        with metricas_col2:
            st.metric("MAE", "0.3774")
            st.metric("RMSE", "0.5260")
        
        st.success("✅ **Exactitud clasificación:** 100% (criterio industrial ±0.5)")
    
    st.markdown("---")
    
    st.markdown("### 🔝 Importancia de Variables")
    
    st.markdown("""
    Las variables están ordenadas por su contribución a la predicción del octanaje.
    Las 3 primeras explican el **89.2%** del comportamiento total.
    """)
    
    # Gráfico de importancia
    importancia_data = pd.DataFrame({
        'Variable': ['PARAFINAS', 'Ox (Oxigenados)', 'NAFTÉNICOS', 'OLEFINAS', 
                     'AROMÁTICOS', 'ISOPARAFINAS', 'ETANOL', 'MTBE', 'ETBE'],
        'Importancia (%)': [40.3, 32.1, 16.8, 4.0, 3.1, 1.6, 1.2, 0.7, 0.2]
    })
    
    st.bar_chart(importancia_data.set_index('Variable')['Importancia (%)'])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: GUÍA DE USO
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("## 📖 Guía de Uso")
    
    st.markdown("### 🚀 Inicio Rápido")
    
    st.markdown("""
    1. **Obtén los datos** del análisis cromatográfico de tu muestra de gasolina
    2. **Introduce los valores** en el formulario de la pestaña "Predicción"
    3. **Haz clic** en "CALCULAR OCTANAJE"
    4. **Obtén el resultado** con clasificación fiscal automática
    
    💡 **Tip:** Puedes usar el botón "Cargar Datos de Ejemplo" en el panel lateral para ver un ejemplo.
    """)
    
    st.markdown("### 📋 Interpretación de Resultados")
    
    st.markdown("""
    El modelo proporciona:
    
    - **Octanaje predicho:** Valor con 1 decimal (ej: 96.2 RON)
    - **Octanaje redondeado:** Valor entero usado para clasificación (ej: 96 RON)
    - **Intervalo de confianza:** Rango ±0.5 unidades (tolerancia industrial)
    - **Clasificación fiscal:** Categoría, Código NC y Epígrafe automáticos
    
    Las 3 categorías fiscales son:
    
    | Octanaje | Categoría | Código NC | Epígrafe |
    |----------|-----------|-----------|----------|
    | < 95 | GASOLINA <95 OCTANOS ⚡ | 2710.12.41 | 1.2.2 |
    | 95-98 | GASOLINA 95 OCTANOS 🚗 | 2710.12.45 | 1.2.2 |
    | > 98 | GASOLINA 98 OCTANOS 🏎️ | 2710.12.49 | 1.2.1 |
    """)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>🤖 Sistema de Predicción de Octanaje con Machine Learning</strong></p>
    <p>Modelo: Gradient Boosting Regressor | R² = 0.8365 | Precisión: 100% (±0.5)</p>
    <p style='font-size: 0.9rem; margin-top: 10px;'>
        Desarrollado para clasificación fiscal de gasolina según normativa española
    </p>
</div>
""", unsafe_allow_html=True)
