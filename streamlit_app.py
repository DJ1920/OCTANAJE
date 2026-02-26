"""
╔═══════════════════════════════════════════════════════════════════════════╗
║              🤖 PREDICTOR DE OCTANAJE - STREAMLIT APP 🤖                  ║
║         Con Google Sheets Integration y Generación de PDFs                ║
╚═══════════════════════════════════════════════════════════════════════════╝

Aplicación Streamlit para predicción de octanaje en gasolina
Versión: 4.0 - Con Google Sheets y PDFs
"""

import streamlit as st
import pickle
import pandas as pd
from datetime import datetime
import os
import io
import zipfile

# Importar módulo de generación de PDFs
try:
    from generar_pdf import generar_pdf_muestra, generar_pdf_batch
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False
    st.warning("⚠️ Módulo generar_pdf.py no encontrado. Funcionalidad de PDFs deshabilitada.")

# Importar Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_DISPONIBLE = True
except ImportError:
    GSHEETS_DISPONIBLE = False

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
if 'datos_gsheets' not in st.session_state:
    st.session_state.datos_gsheets = None
if 'datos_gsheets_original' not in st.session_state:
    st.session_state.datos_gsheets_original = None
if 'pdfs_generados' not in st.session_state:
    st.session_state.pdfs_generados = []

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
    # Detectar si está en zona crítica (límite ± tolerancia 0.5)
    advertencia = None
    limite_critico = None
    
    # Límite crítico en 95.0 (rango de advertencia: 94.5 - 95.5)
    if 94.5 <= octanaje_real <= 95.5:
        limite_critico = 95.0
        if octanaje_real < 95:
            advertencia = f"⚠️ Octanaje {octanaje_real:.1f} cerca de límite 95.0. Tolerancia ±0.5 puede reclasificar."
        else:
            advertencia = f"⚠️ Octanaje {octanaje_real:.1f} cerca de límite 95.0. Tolerancia ±0.5 puede reclasificar."
    
    # Límite crítico en 98.0 (rango de advertencia: 97.5 - 98.5)
    elif 97.5 <= octanaje_real <= 98.5:
        limite_critico = 98.0
        if octanaje_real <= 98:
            advertencia = f"⚠️ Octanaje {octanaje_real:.1f} cerca de límite 98.0. Tolerancia ±0.5 puede reclasificar."
        else:
            advertencia = f"⚠️ Octanaje {octanaje_real:.1f} cerca de límite 98.0. Tolerancia ±0.5 puede reclasificar."
    
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
# FUNCIONES DE GOOGLE SHEETS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def conectar_google_sheets():
    """Conecta con Google Sheets usando credenciales."""
    try:
        # Intentar leer credenciales de Streamlit Secrets
        if 'gcp_service_account' in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
        # Alternativa: leer de archivo local (para desarrollo)
        elif os.path.exists('credentials.json'):
            credentials = Credentials.from_service_account_file(
                'credentials.json',
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
        else:
            return None, "No se encontraron credenciales de Google. Configura 'gcp_service_account' en Secrets."
        
        client = gspread.authorize(credentials)
        return client, None
    
    except Exception as e:
        return None, f"Error de conexión: {str(e)}"

def leer_datos_sheet(sheet_id, sheet_name='Hoja1'):
    """
    Lee datos del Google Sheet.
    Devuelve dos DataFrames: uno original (para mostrar) y uno procesado (para calcular).
    
    Args:
        sheet_id: ID del Google Sheet
        sheet_name: Nombre de la hoja (tab)
    
    Returns:
        tuple: (DataFrame original, DataFrame procesado, mensaje de error o None)
    """
    try:
        client, error = conectar_google_sheets()
        if error:
            return None, None, error
        
        # Abrir el sheet
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(sheet_name)
        
        # Obtener todos los datos
        datos = worksheet.get_all_records()
        
        if not datos:
            return None, None, "El sheet está vacío o no tiene encabezados."
        
        # DataFrame original (para mostrar)
        df_original = pd.DataFrame(datos)
        
        # DataFrame procesado (para calcular)
        df_procesado = df_original.copy()
        
        # Convertir comas a puntos en columnas numéricas del DataFrame procesado
        columnas_numericas = ['P', 'I', 'O', 'N', 'A', 'E', 'MT', 'ET', 'OX']
        for col in columnas_numericas:
            if col in df_procesado.columns:
                # Convertir a string, reemplazar coma por punto, convertir a float
                df_procesado[col] = df_procesado[col].astype(str).str.replace(',', '.').astype(float)
        
        return df_original, df_procesado, None
    
    except Exception as e:
        return None, None, f"Error leyendo datos: {str(e)}"

def escribir_octanaje_en_sheet(sheet_id, sheet_name, fila, octanaje):
    """
    Escribe el octanaje calculado en la columna M del Google Sheet.
    
    Args:
        sheet_id: ID del Google Sheet
        sheet_name: Nombre de la hoja
        fila: Número de fila (1-indexed, incluyendo encabezado)
        octanaje: Valor de octanaje a escribir
    
    Returns:
        tuple: (True/False, mensaje)
    """
    try:
        client, error = conectar_google_sheets()
        if error:
            return False, error
        
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(sheet_name)
        
        # Escribir en columna M (índice 13)
        # fila + 1 porque la fila 1 es el encabezado
        worksheet.update_cell(fila + 2, 13, round(octanaje, 1))
        
        return True, "Octanaje escrito correctamente"
    
    except Exception as e:
        return False, f"Error escribiendo en Sheet: {str(e)}"

def subir_pdf_a_drive(pdf_path, folder_id=None):
    """
    Sube un PDF a Google Drive.
    
    Args:
        pdf_path: Ruta del archivo PDF local
        folder_id: ID de la carpeta de Drive (opcional)
    
    Returns:
        tuple: (URL del archivo o None, mensaje)
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # Verificar que el archivo existe
        if not os.path.exists(pdf_path):
            return None, f"Archivo no encontrado: {pdf_path}"
        
        # Obtener credenciales con scope de Drive
        if 'gcp_service_account' in st.secrets:
            from google.oauth2.service_account import Credentials
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
        else:
            return None, "No se encontraron credenciales"
        
        # Construir servicio de Drive
        service = build('drive', 'v3', credentials=credentials)
        
        # Preparar metadata del archivo
        file_metadata = {
            'name': os.path.basename(pdf_path)
        }
        
        # Si se especifica carpeta, añadir a metadata
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Crear media upload
        media = MediaFileUpload(
            pdf_path,
            mimetype='application/pdf',
            resumable=True
        )
        
        # Subir archivo
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()
        
        # Hacer el archivo accesible públicamente (opcional)
        try:
            service.permissions().create(
                fileId=file.get('id'),
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except:
            pass  # Si falla el permiso público, continuar
        
        return file.get('webViewLink'), f"PDF subido correctamente"
    
    except Exception as e:
        return None, f"Error subiendo a Drive: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def cargar_modelo():
    """Carga el modelo de predicción (con caché)."""
    try:
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
    
    st.markdown("""
    <div class="categoria-box categoria-regular">
        <strong>⚡ GASOLINA <95 OCTANOS</strong><br>
        <small>< 95 octanos</small><br>
        <strong>Código NC:</strong> 2710.12.41<br>
        <strong>Epígrafe:</strong> 1.2.2
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="categoria-box categoria-premium">
        <strong>🚗 GASOLINA 95 OCTANOS</strong><br>
        <small>95 - 98 octanos</small><br>
        <strong>Código NC:</strong> 2710.12.45<br>
        <strong>Epígrafe:</strong> 1.2.2
    </div>
    """, unsafe_allow_html=True)
    
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
    
    if st.button("💡 Cargar Datos de Ejemplo", use_container_width=True):
        st.session_state.cargar_ejemplo = True
        st.session_state.resultado = None
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Predicción", "📊 Procesamiento por Lotes", "📋 Modelo", "📖 Guía"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: PREDICCIÓN INDIVIDUAL (código existente sin cambios)
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 📊 Análisis Cromatográfico")
    st.markdown("Introduce los valores obtenidos del análisis cromatográfico:")
    
    # Determinar valores iniciales
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
        parafinas = st.number_input("**PARAFINAS** (%v/v)", min_value=0.0, max_value=100.0, 
                                     value=valores['PARAFINAS'], step=0.1, help="Rango típico: 5.5 - 16.2", key="parafinas")
        isoparafinas = st.number_input("**ISOPARAFINAS** (%v/v)", min_value=0.0, max_value=100.0, 
                                        value=valores['ISOPARAFINAS'], step=0.1, help="Rango típico: 22.5 - 43.9", key="isoparafinas")
        olefinas = st.number_input("**OLEFINAS** (%v/v)", min_value=0.0, max_value=100.0, 
                                    value=valores['OLEFINAS'], step=0.1, help="Rango típico: 2.3 - 13.8", key="olefinas")
        naftenicos = st.number_input("**NAFTÉNICOS** (%v/v)", min_value=0.0, max_value=100.0, 
                                      value=valores['NAFTENICOS'], step=0.1, help="Rango típico: 2.0 - 14.5", key="naftenicos")
    
    with col2:
        st.markdown("#### 🧪 Aromáticos y Oxigenados")
        aromaticos = st.number_input("**AROMÁTICOS** (%v/v)", min_value=0.0, max_value=100.0, 
                                      value=valores['AROMATICOS'], step=0.1, help="Rango típico: 26.5 - 48.9", key="aromaticos")
        etanol = st.number_input("**ETANOL** (%v/v)", min_value=0.0, max_value=100.0, 
                                 value=valores['ETANOL'], step=0.1, help="Rango típico: 0.0 - 4.9", key="etanol")
        mtbe = st.number_input("**MTBE** (%v/v)", min_value=0.0, max_value=100.0, 
                               value=valores['MTBE'], step=0.1, help="Rango típico: 0.0 - 14.3", key="mtbe")
        etbe = st.number_input("**ETBE** (%v/v)", min_value=0.0, max_value=100.0, 
                               value=valores['ETBE'], step=0.1, help="Rango típico: 0.0 - 7.9", key="etbe")
    
    ox = etanol + mtbe + etbe
    suma_total = parafinas + isoparafinas + olefinas + naftenicos + aromaticos + ox
    
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
    
    if abs(suma_total - 100) > 5:
        st.warning(f"⚠️ **Advertencia:** La suma de componentes es {suma_total:.1f}% (debería estar cerca de 100%)")
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        calcular = st.button("🎯 CALCULAR OCTANAJE", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("🔄 LIMPIAR RESULTADOS", use_container_width=True):
            st.session_state.resultado = None
            st.rerun()
    
    if calcular:
        datos_prediccion = {
            'PARAFINAS': parafinas, 'ISOPARAFINAS': isoparafinas, 'OLEFINAS': olefinas,
            'NAFTENICOS': naftenicos, 'AROMATICOS': aromaticos, 'ETANOL': etanol,
            'MTBE': mtbe, 'ETBE': etbe, 'Ox': ox
        }
        df_input = pd.DataFrame([datos_prediccion])[variables]
        
        with st.spinner("🔮 Calculando octanaje..."):
            octanaje_predicho = float(modelo.predict(df_input)[0])
            octanaje_redondeado = round(octanaje_predicho)
        
        clasificacion = clasificar_gasolina(octanaje_predicho)
        
        st.session_state.resultado = {
            'octanaje': octanaje_predicho,
            'octanaje_redondeado': octanaje_redondeado,
            'clasificacion': clasificacion,
            'datos': datos_prediccion,
            'suma_total': suma_total
        }
    
    if st.session_state.resultado is not None:
        resultado = st.session_state.resultado
        octanaje_predicho = resultado['octanaje']
        octanaje_redondeado = resultado['octanaje_redondeado']
        clasificacion = resultado['clasificacion']
        
        st.markdown("---")
        st.markdown("## ✨ RESULTADO DE LA PREDICCIÓN")
        
        try:
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(clasificacion['imagen'], width=400)
        except:
            pass
        
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
        
        st.markdown("### 📋 Clasificación Fiscal")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Categoría", clasificacion['categoria'])
        with col2:
            st.metric("Código NC", clasificacion['codigo_nc'])
        with col3:
            st.metric("Epígrafe Fiscal", clasificacion['epigrafe'])
        
        st.info(f"📝 **Descripción:** {clasificacion['descripcion']}")
        
        if clasificacion.get('advertencia'):
            st.warning(clasificacion['advertencia'])
        
        st.markdown("### 💾 Exportar Resultado")
        datos_exportar = {
            'Fecha_Hora': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'PARAFINAS': [parafinas], 'ISOPARAFINAS': [isoparafinas], 'OLEFINAS': [olefinas],
            'NAFTENICOS': [naftenicos], 'AROMATICOS': [aromaticos], 'ETANOL': [etanol],
            'MTBE': [mtbe], 'ETBE': [etbe], 'Ox': [ox],
            'Octanaje_Predicho': [round(octanaje_predicho, 1)],
            'Octanaje_Redondeado': [octanaje_redondeado],
            'Categoria': [clasificacion['categoria']],
            'Codigo_NC': [clasificacion['codigo_nc']],
            'Epigrafe': [clasificacion['epigrafe']]
        }
        df_exportar = pd.DataFrame(datos_exportar)
        csv = df_exportar.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar resultado en CSV", data=csv,
                          file_name=f'prediccion_octanaje_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                          mime='text/csv', use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: PROCESAMIENTO POR LOTES (NUEVA FUNCIONALIDAD)
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## 📊 Procesamiento por Lotes desde Google Sheets")
    
    if not GSHEETS_DISPONIBLE:
        st.error("❌ **Error:** Librerías de Google Sheets no instaladas.")
        st.info("Añade a requirements.txt: gspread, google-auth, google-auth-oauthlib")
        st.stop()
    
    st.markdown("### ⚙️ Configuración")
    
    # Configuración del Sheet
    col1, col2 = st.columns(2)
    
    with col1:
        sheet_id = st.text_input(
            "🔑 ID del Google Sheet",
            value=st.secrets.get("google_sheets", {}).get("sheet_id", ""),
            help="Ej: 1xYz_ABCD1234567890 (se encuentra en la URL del Sheet)",
            key="sheet_id_input"
        )
    
    with col2:
        sheet_name = st.text_input(
            "📄 Nombre de la Hoja",
            value=st.secrets.get("google_sheets", {}).get("sheet_name", "Hoja1"),
            help="Nombre del tab en el Google Sheet",
            key="sheet_name_input"
        )
    
    # Botón para leer datos
    if st.button("📥 LEER DATOS DEL SHEET", type="primary", use_container_width=True):
        if not sheet_id:
            st.error("❌ Por favor, proporciona el ID del Google Sheet")
        else:
            with st.spinner("🔄 Conectando con Google Sheets..."):
                df_original, df_procesado, error = leer_datos_sheet(sheet_id, sheet_name)
                
                if error:
                    st.error(f"❌ Error: {error}")
                    st.info("💡 Verifica que:\n- Las credenciales están configuradas en Secrets\n- El Sheet está compartido con la cuenta de servicio\n- El nombre de la hoja es correcto")
                else:
                    # Guardar ambos DataFrames
                    st.session_state.datos_gsheets_original = df_original
                    st.session_state.datos_gsheets = df_procesado
                    st.success(f"✅ Datos leídos correctamente: {len(df_procesado)} filas")
    
    # Mostrar datos si existen (usar el original para la vista previa)
    if st.session_state.datos_gsheets is not None:
        # DataFrame procesado para cálculos
        df = st.session_state.datos_gsheets
        # DataFrame original para mostrar
        df_mostrar = st.session_state.get('datos_gsheets_original', df)
        
        st.markdown("### 📋 Vista Previa de Datos")
        
        # Mostrar TODAS las filas del DataFrame ORIGINAL (con comas)
        st.dataframe(df_mostrar, use_container_width=True, height=400)
        st.caption(f"Mostrando todas las {len(df)} filas")
        
        # Verificar que las columnas necesarias existen
        columnas_necesarias = ['P', 'I', 'O', 'N', 'A', 'E', 'MT', 'ET']
        columnas_faltantes = [col for col in columnas_necesarias if col not in df.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas: {', '.join(columnas_faltantes)}")
            st.info("Las columnas deben llamarse: MUESTRA, P, I, O, N, A, E, MT, ET, OX")
        else:
            st.markdown("### 🎯 Seleccionar Muestras a Procesar")
            
            # Radio button para seleccionar modo
            modo_seleccion = st.radio(
                "¿Qué muestras quieres procesar?",
                ["Todas las filas", "Una fila específica", "Rango de filas"],
                horizontal=True
            )
            
            filas_a_procesar = []
            
            if modo_seleccion == "Todas las filas":
                filas_a_procesar = list(range(len(df)))
                st.info(f"📊 Se procesarán todas las {len(df)} muestras")
            
            elif modo_seleccion == "Una fila específica":
                col1, col2 = st.columns([3, 1])
                with col1:
                    fila_especifica = st.number_input(
                        "Número de fila (1 = primera fila de datos)",
                        min_value=1,
                        max_value=len(df),
                        value=1,
                        step=1
                    )
                with col2:
                    st.metric("Muestra", df.iloc[fila_especifica-1].get('MUESTRA', f'Fila {fila_especifica}'))
                
                filas_a_procesar = [fila_especifica - 1]
                st.info(f"📊 Se procesará 1 muestra: fila {fila_especifica}")
            
            elif modo_seleccion == "Rango de filas":
                col1, col2 = st.columns(2)
                with col1:
                    fila_inicio = st.number_input(
                        "Fila inicial",
                        min_value=1,
                        max_value=len(df),
                        value=1,
                        step=1
                    )
                with col2:
                    fila_fin = st.number_input(
                        "Fila final",
                        min_value=1,
                        max_value=len(df),
                        value=min(10, len(df)),
                        step=1
                    )
                
                if fila_inicio > fila_fin:
                    st.error("❌ La fila inicial debe ser menor o igual que la fila final")
                else:
                    filas_a_procesar = list(range(fila_inicio - 1, fila_fin))
                    st.info(f"📊 Se procesarán {len(filas_a_procesar)} muestras (filas {fila_inicio} a {fila_fin})")
            
            st.markdown("---")
            
            # Opciones adicionales
            col1, col2 = st.columns(2)
            with col1:
                escribir_en_sheet = st.checkbox("✍️ Escribir octanaje en columna M del Sheet", value=True)
            with col2:
                subir_a_drive = st.checkbox("☁️ Subir PDFs a Google Drive", value=False)
            
            if subir_a_drive:
                folder_id_drive = st.text_input(
                    "ID de carpeta de Drive (opcional)",
                    help="Deja vacío para subir a la raíz. ID se ve en la URL de la carpeta.",
                    key="folder_drive"
                )
            else:
                folder_id_drive = None
            
            st.markdown("---")
            
            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 PROCESAR Y GENERAR PDFs", type="primary", use_container_width=True):
                    if not PDF_DISPONIBLE:
                        st.error("❌ Módulo generar_pdf.py no disponible")
                    else:
                        with st.spinner(f"🔮 Procesando {len(filas_a_procesar)} muestras..."):
                            resultados = []
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, idx in enumerate(filas_a_procesar):
                                fila = df.iloc[idx]
                                status_text.text(f"Procesando muestra {i+1}/{len(filas_a_procesar)}...")
                                progress_bar.progress((i + 1) / len(filas_a_procesar))
                                
                                # Preparar datos
                                datos_muestra = {
                                    'muestra': str(fila.get('MUESTRA', f'Muestra_{idx+1}')),
                                    'parafinas': float(fila['P']),
                                    'isoparafinas': float(fila['I']),
                                    'olefinas': float(fila['O']),
                                    'naftenicos': float(fila['N']),
                                    'aromaticos': float(fila['A']),
                                    'etanol': float(fila['E']),
                                    'mtbe': float(fila['MT']),
                                    'etbe': float(fila['ET']),
                                    'ox': float(fila.get('OX', fila['E'] + fila['MT'] + fila['ET'])),
                                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                                    'comentarios': fila.get('COMENTARIOS', '')
                                }
                                
                                # Predecir
                                df_pred = pd.DataFrame([{
                                    'PARAFINAS': datos_muestra['parafinas'],
                                    'ISOPARAFINAS': datos_muestra['isoparafinas'],
                                    'OLEFINAS': datos_muestra['olefinas'],
                                    'NAFTENICOS': datos_muestra['naftenicos'],
                                    'AROMATICOS': datos_muestra['aromaticos'],
                                    'ETANOL': datos_muestra['etanol'],
                                    'MTBE': datos_muestra['mtbe'],
                                    'ETBE': datos_muestra['etbe'],
                                    'Ox': datos_muestra['ox']
                                }])[variables]
                                
                                octanaje = float(modelo.predict(df_pred)[0])
                                clasificacion = clasificar_gasolina(octanaje)
                                
                                resultado_prediccion = {
                                    'octanaje': octanaje,
                                    'octanaje_redondeado': round(octanaje),
                                    'categoria': clasificacion['categoria'],
                                    'codigo_nc': clasificacion['codigo_nc'],
                                    'epigrafe': clasificacion['epigrafe'],
                                    'advertencia': clasificacion.get('advertencia', None)
                                }
                                
                                # Generar PDF
                                nombre_pdf = f"Informe_{datos_muestra['muestra'].replace(' ', '_')}.pdf"
                                ruta_pdf = generar_pdf_muestra(datos_muestra, resultado_prediccion, nombre_pdf)
                                
                                # Escribir en Sheet si está activado
                                if escribir_en_sheet:
                                    exito, msg = escribir_octanaje_en_sheet(sheet_id, sheet_name, idx, octanaje)
                                    if not exito:
                                        st.warning(f"⚠️ No se pudo escribir en Sheet fila {idx+1}: {msg}")
                                
                                # Subir a Drive si está activado
                                drive_url = None
                                if subir_a_drive:
                                    drive_url, msg = subir_pdf_a_drive(ruta_pdf, folder_id_drive)
                                    if not drive_url:
                                        st.warning(f"⚠️ No se pudo subir a Drive: {msg}")
                                
                                resultados.append({
                                    'fila': idx + 1,
                                    'muestra': datos_muestra['muestra'],
                                    'octanaje': octanaje,
                                    'categoria': clasificacion['categoria'],
                                    'pdf_path': ruta_pdf,
                                    'drive_url': drive_url
                                })
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            st.session_state.pdfs_generados = resultados
                            
                            msg_success = f"✅ {len(resultados)} PDFs generados"
                            if escribir_en_sheet:
                                msg_success += " | Octanajes escritos en Sheet"
                            if subir_a_drive:
                                msg_success += " | PDFs subidos a Drive"
                            st.success(msg_success)
            
            with col2:
                if st.button("🔄 LIMPIAR", use_container_width=True):
                    st.session_state.datos_gsheets = None
                    st.session_state.datos_gsheets_original = None
                    st.session_state.pdfs_generados = []
                    st.rerun()
            
            # Mostrar resultados
            if st.session_state.pdfs_generados:
                st.markdown("### 📥 Resultados y Descargas")
                
                # Crear DataFrame para mostrar
                df_resultados = pd.DataFrame(st.session_state.pdfs_generados)
                cols_mostrar = ['fila', 'muestra', 'octanaje', 'categoria']
                
                if subir_a_drive and 'drive_url' in df_resultados.columns:
                    cols_mostrar.append('drive_url')
                
                st.dataframe(df_resultados[cols_mostrar], use_container_width=True)
                
                # Botón para descargar ZIP
                if len(st.session_state.pdfs_generados) > 1:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for resultado in st.session_state.pdfs_generados:
                            if os.path.exists(resultado['pdf_path']):
                                zip_file.write(resultado['pdf_path'], os.path.basename(resultado['pdf_path']))
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        "📦 DESCARGAR TODOS LOS PDFs (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"Informes_Octanaje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                else:
                    # Descargar individual
                    if os.path.exists(st.session_state.pdfs_generados[0]['pdf_path']):
                        with open(st.session_state.pdfs_generados[0]['pdf_path'], 'rb') as f:
                            st.download_button(
                                "📄 DESCARGAR PDF",
                                data=f.read(),
                                file_name=os.path.basename(st.session_state.pdfs_generados[0]['pdf_path']),
                                mime="application/pdf",
                                use_container_width=True
                            )

# TAB 3 y TAB 4: Información del modelo y guía (código existente sin cambios)
with tab3:
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

with tab4:
    st.markdown("## 📖 Guía de Uso")
    st.markdown("""
    ### 🚀 Predicción Individual
    1. Introduce los valores del análisis cromatográfico
    2. Haz clic en "CALCULAR OCTANAJE"
    3. Obtén el resultado con clasificación fiscal
    
    ### 📊 Procesamiento por Lotes
    1. Configura el ID de tu Google Sheet
    2. Haz clic en "LEER DATOS DEL SHEET"
    3. Verifica los datos en la vista previa
    4. Haz clic en "PROCESAR Y GENERAR PDFs"
    5. Descarga los PDFs individuales o el ZIP completo
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>🤖 Sistema de Predicción de Octanaje con Machine Learning</strong></p>
    <p>Versión 4.0 | Modelo: Gradient Boosting | R² = 0.8365 | Precisión: 100% (±0.5)</p>
</div>
""", unsafe_allow_html=True)
