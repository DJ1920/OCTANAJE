"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                  GENERADOR DE PDFs DE OCTANAJE                            ║
║                  Reportes individuales por muestra                        ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def generar_pdf_muestra(datos_muestra, resultado_prediccion, ruta_salida):
    """
    Genera un PDF individual para una muestra de gasolina.
    
    Args:
        datos_muestra: dict con datos de la muestra {
            'muestra': '2025 014144',
            'parafinas': 12.74,
            'isoparafinas': 36.38,
            ...
            'fecha': '2025-01-30',  # opcional
            'comentarios': 'texto'  # opcional
        }
        resultado_prediccion: dict con resultado del modelo {
            'octanaje': 98.3,
            'octanaje_redondeado': 98,
            'categoria': 'GASOLINA 98 OCTANOS',
            'codigo_nc': '2710.12.49',
            'epigrafe': '1.2.1',
            'advertencia': 'texto o None'
        }
        ruta_salida: str, ruta donde guardar el PDF
    
    Returns:
        str: ruta del archivo PDF generado
    """
    
    # Crear documento
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Contenedor de elementos
    elementos = []
    
    # Estilos
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=estilos['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    estilo_subtitulo = ParagraphStyle(
        'CustomSubtitle',
        parent=estilos['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    estilo_normal = ParagraphStyle(
        'CustomNormal',
        parent=estilos['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=6
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # ENCABEZADO
    # ═══════════════════════════════════════════════════════════════════════
    
    # Banner superior (si existe)
    if os.path.exists('banner.png'):
        try:
            img = Image('banner.png', width=17*cm, height=3*cm)
            elementos.append(img)
            elementos.append(Spacer(1, 0.5*cm))
        except:
            pass
    
    # Título principal
    titulo = Paragraph("INFORME DE ANÁLISIS DE OCTANAJE", estilo_titulo)
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.5*cm))
    
    # ═══════════════════════════════════════════════════════════════════════
    # INFORMACIÓN DE LA MUESTRA
    # ═══════════════════════════════════════════════════════════════════════
    
    subtitulo_muestra = Paragraph("📋 Información de la Muestra", estilo_subtitulo)
    elementos.append(subtitulo_muestra)
    
    # Tabla de información general
    fecha = datos_muestra.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    fecha_reporte = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    datos_info = [
        ['Número de Muestra:', datos_muestra.get('muestra', 'N/A')],
        ['Fecha de Análisis:', fecha],
        ['Fecha del Reporte:', fecha_reporte],
    ]
    
    # Añadir comentarios si existen
    if datos_muestra.get('comentarios'):
        datos_info.append(['Comentarios:', datos_muestra.get('comentarios')])
    
    tabla_info = Table(datos_info, colWidths=[5*cm, 12*cm])
    tabla_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.8*cm))
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPOSICIÓN CROMATOGRÁFICA
    # ═══════════════════════════════════════════════════════════════════════
    
    subtitulo_comp = Paragraph("🧪 Composición Cromatográfica (%v/v)", estilo_subtitulo)
    elementos.append(subtitulo_comp)
    
    # Tabla de componentes
    datos_componentes = [
        ['Componente', 'Valor (%v/v)'],
        ['PARAFINAS', f"{datos_muestra.get('parafinas', 0):.2f}"],
        ['ISOPARAFINAS', f"{datos_muestra.get('isoparafinas', 0):.2f}"],
        ['OLEFINAS', f"{datos_muestra.get('olefinas', 0):.2f}"],
        ['NAFTÉNICOS', f"{datos_muestra.get('naftenicos', 0):.2f}"],
        ['AROMÁTICOS', f"{datos_muestra.get('aromaticos', 0):.2f}"],
        ['ETANOL', f"{datos_muestra.get('etanol', 0):.2f}"],
        ['MTBE', f"{datos_muestra.get('mtbe', 0):.2f}"],
        ['ETBE', f"{datos_muestra.get('etbe', 0):.2f}"],
        ['OXIGENADOS (Ox)', f"{datos_muestra.get('ox', 0):.2f}"],
    ]
    
    # Calcular suma total
    suma_total = sum([
        datos_muestra.get('parafinas', 0),
        datos_muestra.get('isoparafinas', 0),
        datos_muestra.get('olefinas', 0),
        datos_muestra.get('naftenicos', 0),
        datos_muestra.get('aromaticos', 0),
        datos_muestra.get('ox', 0)
    ])
    
    datos_componentes.append(['SUMA TOTAL', f"{suma_total:.2f}"])
    
    tabla_componentes = Table(datos_componentes, colWidths=[10*cm, 7*cm])
    tabla_componentes.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        
        # Datos
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # Última fila (SUMA)
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        # General
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elementos.append(tabla_componentes)
    elementos.append(Spacer(1, 0.8*cm))
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESULTADO DE PREDICCIÓN
    # ═══════════════════════════════════════════════════════════════════════
    
    subtitulo_resultado = Paragraph("✨ Resultado de la Predicción", estilo_subtitulo)
    elementos.append(subtitulo_resultado)
    
    # Determinar color según categoría
    if 'GASOLINA <95' in resultado_prediccion['categoria']:
        color_categoria = colors.HexColor('#F39C12')  # Amarillo/naranja
    elif 'GASOLINA 95' in resultado_prediccion['categoria']:
        color_categoria = colors.HexColor('#3498DB')  # Azul
    else:  # GASOLINA 98
        color_categoria = colors.HexColor('#9B59B6')  # Morado
    
    # Tabla de resultados
    octanaje = resultado_prediccion['octanaje']
    octanaje_red = resultado_prediccion['octanaje_redondeado']
    
    datos_resultado = [
        ['Parámetro', 'Valor'],
        ['Octanaje Predicho (RON)', f"{octanaje:.1f}"],
        ['Octanaje Redondeado', f"{octanaje_red}"],
        ['Intervalo de Confianza', f"[{octanaje-0.5:.1f}, {octanaje+0.5:.1f}]"],
        ['Categoría Fiscal', resultado_prediccion['categoria']],
        ['Código NC', resultado_prediccion['codigo_nc']],
        ['Epígrafe Fiscal', resultado_prediccion['epigrafe']],
    ]
    
    tabla_resultado = Table(datos_resultado, colWidths=[10*cm, 7*cm])
    tabla_resultado.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        
        # Fila de categoría (destacada)
        ('BACKGROUND', (0, 4), (-1, 4), color_categoria),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.whitesmoke),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        
        # Datos normales
        ('BACKGROUND', (0, 1), (-1, 3), colors.beige),
        ('BACKGROUND', (0, 5), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # General
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elementos.append(tabla_resultado)
    elementos.append(Spacer(1, 0.5*cm))
    
    # ═══════════════════════════════════════════════════════════════════════
    # ADVERTENCIA (si existe)
    # ═══════════════════════════════════════════════════════════════════════
    
    if resultado_prediccion.get('advertencia'):
        elementos.append(Spacer(1, 0.3*cm))
        
        advertencia_texto = f"⚠️ {resultado_prediccion['advertencia']}"
        
        datos_advertencia = [[advertencia_texto]]
        tabla_advertencia = Table(datos_advertencia, colWidths=[17*cm])
        tabla_advertencia.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF3CD')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#856404')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#FFC107')),
        ]))
        
        elementos.append(tabla_advertencia)
    
    elementos.append(Spacer(1, 1*cm))
    
    # ═══════════════════════════════════════════════════════════════════════
    # PIE DE PÁGINA
    # ═══════════════════════════════════════════════════════════════════════
    
    estilo_footer = ParagraphStyle(
        'Footer',
        parent=estilos['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    footer_texto = f"""
    <para align=center>
    Sistema de Predicción de Octanaje con Machine Learning<br/>
    Modelo: Gradient Boosting Regressor | R² = 0.8365 | Precisión: 100% (±0.5)<br/>
    Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </para>
    """
    
    footer = Paragraph(footer_texto, estilo_footer)
    elementos.append(footer)
    
    # ═══════════════════════════════════════════════════════════════════════
    # GENERAR PDF
    # ═══════════════════════════════════════════════════════════════════════
    
    doc.build(elementos)
    
    return ruta_salida


def generar_pdf_batch(lista_muestras, ruta_carpeta_salida):
    """
    Genera múltiples PDFs, uno por cada muestra.
    
    Args:
        lista_muestras: list de dicts, cada uno con datos_muestra y resultado_prediccion
        ruta_carpeta_salida: str, carpeta donde guardar los PDFs
    
    Returns:
        list: lista de rutas de los PDFs generados
    """
    
    if not os.path.exists(ruta_carpeta_salida):
        os.makedirs(ruta_carpeta_salida)
    
    pdfs_generados = []
    
    for muestra in lista_muestras:
        # Nombre del archivo
        numero_muestra = muestra['datos_muestra'].get('muestra', 'SIN_NUMERO').replace(' ', '_')
        nombre_archivo = f"Informe_Octanaje_{numero_muestra}.pdf"
        ruta_completa = os.path.join(ruta_carpeta_salida, nombre_archivo)
        
        # Generar PDF
        try:
            generar_pdf_muestra(
                muestra['datos_muestra'],
                muestra['resultado_prediccion'],
                ruta_completa
            )
            pdfs_generados.append(ruta_completa)
        except Exception as e:
            print(f"Error generando PDF para muestra {numero_muestra}: {e}")
    
    return pdfs_generados
